#!/usr/bin/env python3
"""Build/query a revision-scoped SQLite evidence catalog; Python standard library only."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3


# One database holds one revision: snapshot records provenance, files holds the full
# baseline, and entities/declared_bases/name_occurrences hold collector observations.
# Entity IDs come from the collector (C#: path + syntax offset), not qualified names;
# duplicate names and partial declarations therefore remain distinct within a snapshot.
# Interpretations are separate, evidenced judgments; purpose_search is their FTS index.
# The profiles view matches occurrences by name/arity only. Its ambiguity count exposes
# collisions; these counts and textual bases are not resolved dependency edges.
SCHEMA = """
CREATE TABLE snapshot(repository TEXT NOT NULL, commit_sha TEXT NOT NULL,
    baseline_sha256 TEXT NOT NULL, analysis_sha256 TEXT NOT NULL, metadata_json TEXT NOT NULL);
CREATE TABLE files(path TEXT PRIMARY KEY, extension TEXT NOT NULL, sha256 TEXT NOT NULL,
    bytes INTEGER NOT NULL, lines INTEGER, nonblank_lines INTEGER);
CREATE TABLE entities(id TEXT PRIMARY KEY, file_path TEXT NOT NULL REFERENCES files(path),
    name TEXT NOT NULL, qualified_name TEXT NOT NULL, arity INTEGER NOT NULL, kind TEXT NOT NULL,
    parent_id TEXT REFERENCES entities(id) DEFERRABLE INITIALLY DEFERRED,
    line INTEGER NOT NULL, end_line INTEGER NOT NULL, modifiers_json TEXT NOT NULL,
    branch_nodes INTEGER NOT NULL, method_declarations INTEGER NOT NULL,
    max_constructor_parameters INTEGER NOT NULL);
CREATE INDEX entities_name ON entities(name, arity);
CREATE INDEX entities_parent ON entities(parent_id);
CREATE TABLE declared_bases(entity_id TEXT NOT NULL REFERENCES entities(id), target_text TEXT NOT NULL);
CREATE TABLE name_occurrences(file_path TEXT NOT NULL REFERENCES files(path), offset INTEGER NOT NULL,
    line INTEGER NOT NULL, name TEXT NOT NULL, arity INTEGER NOT NULL,
    owner_id TEXT REFERENCES entities(id), context TEXT, PRIMARY KEY(file_path, offset));
CREATE INDEX occurrence_name ON name_occurrences(name, arity);
CREATE INDEX occurrence_owner ON name_occurrences(owner_id);
CREATE TABLE interpretations(entity_id TEXT PRIMARY KEY REFERENCES entities(id),
    purpose TEXT NOT NULL, confidence TEXT NOT NULL CHECK(confidence IN ('low','medium','high')),
    author TEXT NOT NULL, evidence_json TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE VIRTUAL TABLE purpose_search USING fts5(entity_id UNINDEXED, name, purpose);
CREATE VIEW profiles AS SELECT e.*,
    (SELECT count(*) FROM name_occurrences n WHERE n.name=e.name AND n.arity=e.arity)
        AS lexical_name_occurrences,
    (SELECT count(DISTINCT owner_id) FROM name_occurrences n
        WHERE n.name=e.name AND n.arity=e.arity) AS lexical_owner_count,
    (SELECT count(*) FROM entities other WHERE other.name=e.name AND other.arity=e.arity)
        AS same_name_declarations,
    i.purpose, i.confidence
    FROM entities e LEFT JOIN interpretations i ON i.entity_id=e.id;
"""


def connect(path, readonly=False):
    uri = Path(path).resolve().as_uri() + ("?mode=ro" if readonly else "?mode=rw")
    db = sqlite3.connect(uri, uri=True)
    db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = sqlite3.Row
    return db


def build(database, baseline_path, analysis_path, repository):
    """Create a new snapshot, refusing mismatched evidence or overwrites."""
    baseline_bytes = Path(baseline_path).read_bytes()
    analysis_bytes = Path(analysis_path).read_bytes()
    baseline, analysis = json.loads(baseline_bytes), json.loads(analysis_bytes)
    # The file baseline is language-neutral, but this importer currently requires the
    # C# schema and complete .cs coverage. Other collectors need an explicit adapter here.
    # Match revision, content hashes, and declaration totals before creating the database.
    if analysis.get("schema") != 2:
        raise ValueError("Expected C# collector schema 2")
    if baseline["commit"] != analysis["commit"]:
        raise ValueError("Baseline and analysis revisions differ")
    files = {f["path"]: f for f in baseline["files"]}
    expected_paths = {path for path in files if path.endswith(".cs")}
    analyzed_paths = [row["path"] for row in analysis["files"]]
    if set(analyzed_paths) != expected_paths or len(set(analyzed_paths)) != len(analyzed_paths):
        raise ValueError("Analysis must cover each committed regular .cs file exactly once")
    declaration_counts = Counter(e["path"] for e in analysis["declarations"])
    for row in analysis["files"]:
        if row["path"] not in files or files[row["path"]]["sha256"] != row["sha256"]:
            raise ValueError("Analysis content does not match committed baseline: " + row["path"])
        if declaration_counts[row["path"]] != row["type_declarations"]:
            raise ValueError("Declaration inventory is incomplete: " + row["path"])
    if set(declaration_counts) - expected_paths:
        raise ValueError("Declarations must belong to analyzed C# files")
    # Exclusive reservation prevents overwriting another assessment. Errors remove only our new file.
    path = Path(database)
    with path.open("xb"):
        pass
    db = None
    try:
        with connect(path) as db:
            db.executescript(SCHEMA)
            # Preserve collector definitions/diagnostics alongside hashes of both input
            # artifacts so consumers can audit the scope and provenance of the measurements.
            metadata = {k: v for k, v in analysis.items()
                        if k not in ("files", "declarations", "name_occurrences")}
            metadata["file_diagnostics"] = [{"path": f["path"], "directives": f["directives"],
                                           "parse_errors": f["parse_errors"]}
                                          for f in analysis["files"]
                                          if f["directives"] or f["parse_errors"]]
            metadata["schema_version"] = 1
            metadata["baseline_excluded"] = baseline["excluded"]
            db.execute("INSERT INTO snapshot VALUES (?,?,?,?,?)", (
                repository, baseline["commit"], hashlib.sha256(baseline_bytes).hexdigest(),
                hashlib.sha256(analysis_bytes).hexdigest(), json.dumps(metadata)))
            # Keep every baseline file, including non-C# files; absent line measurements
            # stay NULL. Import declarations and occurrences without binding their names.
            # Deferred parent foreign keys allow any declaration order; the transaction
            # rejects dangling relationships before committing the imported evidence.
            db.executemany("INSERT INTO files VALUES (?,?,?,?,?,?)", [(
                f["path"], f["extension"], f["sha256"], f["bytes"],
                f.get("lines"), f.get("nonblank_lines")) for f in files.values()])
            db.executemany("INSERT INTO entities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [(
                e["id"], e["path"], e["name"], e["qualified_name"], e["arity"], e["kind"],
                e["parent_id"], e["line"], e["end_line"], json.dumps(e["modifiers"]),
                e["branch_nodes"], e["method_declarations"], e["max_constructor_parameters"])
                for e in analysis["declarations"]])
            db.executemany("INSERT INTO declared_bases VALUES (?,?)", [
                (e["id"], base) for e in analysis["declarations"] for base in e["bases"]])
            db.executemany("INSERT INTO name_occurrences VALUES (?,?,?,?,?,?,?)", [(
                n["path"], n["offset"], n["line"], n["name"], n["arity"], n["owner_id"], n["context"])
                for n in analysis["name_occurrences"]])
    except Exception:
        if db is not None:
            db.close()
            db = None
        path.unlink()
        raise
    finally:
        if db is not None:
            db.close()


def annotate(database, annotation_path):
    """Store interpretations separately, only with evidence belonging to this snapshot."""
    payload = json.loads(Path(annotation_path).read_text(encoding="utf-8"))
    db = connect(database)
    try:
        # Apply the whole annotation batch and its search-index updates in one transaction:
        # invalid evidence rolls everything back, and measured entities remain untouched.
        with db:
            snapshot = db.execute("SELECT repository,commit_sha FROM snapshot").fetchone()
            if (payload["repository"], payload["commit"]) != tuple(snapshot):
                raise ValueError("Interpretations belong to a different repository or revision")
            for item in payload["interpretations"]:
                if not item["purpose"].strip() or not item["author"].strip() or not item["evidence"]:
                    raise ValueError("An interpretation requires purpose, author, and evidence")
                for evidence in item["evidence"]:
                    file = db.execute("SELECT lines FROM files WHERE path=?", (evidence["path"],)).fetchone()
                    if (file is None or file["lines"] is None or type(evidence["line"]) is not int
                            or not 1 <= evidence["line"] <= file["lines"]):
                        raise ValueError("Evidence must point into a measured file in this snapshot")
                name = db.execute("SELECT qualified_name FROM entities WHERE id=?", (item["entity_id"],)).fetchone()
                if name is None:
                    raise ValueError("Unknown entity: " + item["entity_id"])
                db.execute("INSERT INTO interpretations VALUES (?,?,?,?,?,?) "
                           "ON CONFLICT(entity_id) DO UPDATE SET purpose=excluded.purpose, "
                           "confidence=excluded.confidence, author=excluded.author, "
                           "evidence_json=excluded.evidence_json, recorded_at=excluded.recorded_at", (
                               item["entity_id"], item["purpose"], item["confidence"], item["author"],
                               json.dumps(item["evidence"]), datetime.now(timezone.utc).isoformat()))
                # FTS5 is maintained explicitly, so replacing a purpose also replaces its
                # searchable text rather than leaving stale matches for the previous wording.
                db.execute("DELETE FROM purpose_search WHERE entity_id=?", (item["entity_id"],))
                db.execute("INSERT INTO purpose_search VALUES (?,?,?)",
                           (item["entity_id"], name[0], item["purpose"]))
    finally:
        db.close()


def query(database, sql, limit=100):
    db = connect(database, readonly=True)
    try:
        # Also blocks ATTACH/writes to other databases; query mode is read-only, not an SQL sandbox.
        db.set_authorizer(lambda action, *args: sqlite3.SQLITE_DENY if action in (
            sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH) else sqlite3.SQLITE_OK)
        db.execute("PRAGMA query_only=ON")
        rows = db.execute(sql).fetchmany(limit + 1)
        return {"rows": [dict(row) for row in rows[:limit]], "truncated": len(rows) > limit}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("build", help="Create a new database; never overwrite")
    create.add_argument("database", type=Path)
    create.add_argument("--baseline", type=Path, required=True)
    create.add_argument("--analysis", type=Path, required=True)
    create.add_argument("--repository", required=True, help="Non-sensitive repository label")
    annotation = commands.add_parser("annotate")
    annotation.add_argument("database", type=Path)
    annotation.add_argument("annotations", type=Path)
    read = commands.add_parser("query")
    read.add_argument("database", type=Path)
    read.add_argument("sql")
    read.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build(args.database, args.baseline, args.analysis, args.repository)
        elif args.command == "annotate":
            annotate(args.database, args.annotations)
        else:
            if args.limit < 1:
                raise ValueError("Limit must be positive")
            print(json.dumps(query(args.database, args.sql, args.limit), indent=2))
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
