#!/usr/bin/env python3
"""Measure committed Git blobs; emit JSON without checking out or executing target code."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def collect(repo, revision):
    commit = git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    entries = git(repo, "ls-tree", "-rz", "--full-tree", commit).split(b"\0")
    files, excluded = [], []
    groups = defaultdict(Counter)
    with subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as batch:
        for entry in entries:
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, oid = metadata.split()
            path = raw_path.decode("utf-8", errors="surrogateescape")
            if kind != b"blob" or mode == b"120000":
                excluded.append({"path": path, "reason": "symlink or submodule"})
                continue
            batch.stdin.write(oid + b"\n")
            batch.stdin.flush()
            header = batch.stdout.readline().split()
            if len(header) != 3 or header[1] != b"blob":
                raise RuntimeError("Git did not return the requested blob")
            content = batch.stdout.read(int(header[2]))
            if len(content) != int(header[2]) or batch.stdout.read(1) != b"\n":
                raise RuntimeError("Incomplete Git blob response")
            suffix = Path(path).suffix.lower() or "[none]"
            row = {"path": path, "extension": suffix, "bytes": len(content), "blob": oid.decode()}
            # Exact byte equality is only a candidate signal; filenames and intent still matter.
            row["sha256"] = hashlib.sha256(content).hexdigest()
            try:
                if b"\0" in content:
                    raise UnicodeError("binary content")
                decoded = content.decode("utf-8-sig")
                lines = decoded.splitlines()
                row.update(lines=len(lines), nonblank_lines=sum(bool(line.strip()) for line in lines))
            except UnicodeError:
                row["text_status"] = "binary or non-UTF-8; line count unavailable"
            files.append(row)
            groups[suffix].update(files=1, bytes=len(content), lines=row.get("lines", 0),
                                  nonblank_lines=row.get("nonblank_lines", 0),
                                  unmeasured_files=int("lines" not in row))
        batch.stdin.close()
        if batch.wait() != 0:
            raise RuntimeError("Git blob reader failed")
    return {
        "schema": 1, "commit": commit,
        "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "all regular files in the commit; no worktree content, symlinks, or submodule contents",
        "line_definition": "UTF-8 splitlines, including comments; nonblank is not logical source LOC",
        "classification": "extensions only; classify production, tests, generated, and vendor code separately",
        "by_extension": dict(sorted(groups.items())), "excluded": excluded, "files": files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    try:
        json.dump(collect(args.repository, args.revision), sys.stdout, indent=2, sort_keys=True)
        print()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        parser.exit(1, f"Baseline failed: {error}\n")


if __name__ == "__main__":
    main()
