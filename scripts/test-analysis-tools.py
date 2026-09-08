#!/usr/bin/env python3
"""Exercise measurement boundaries using disposable Git repositories."""

import argparse
import importlib.util
import json
import sqlite3
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "skills/architecture-assessment/scripts/repository_baseline.py"
spec = importlib.util.spec_from_file_location("baseline", COLLECTOR)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
catalog_spec = importlib.util.spec_from_file_location("catalog", COLLECTOR.with_name("architecture_catalog.py"))
catalog = importlib.util.module_from_spec(catalog_spec)
catalog_spec.loader.exec_module(catalog)
CSHARP_DLL = None


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args]).decode().strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def test_committed_scope_binary_symlink_and_unusual_names(self):
        (self.repo / "a.cs").write_bytes(b"one\r\n\r\ntwo")
        (self.repo / "notes\twith\nspaces.md").write_text("hello\n", encoding="utf-8")
        (self.repo / "binary.cs").write_bytes(b"\0\xff")
        (self.repo / "link.cs").symlink_to("a.cs")
        first = self.commit()
        (self.repo / "a.cs").write_text("changed\n", encoding="utf-8")
        (self.repo / "untracked.cs").write_text("not in baseline", encoding="utf-8")
        result = baseline.collect(self.repo, first)
        self.assertEqual(first, result["commit"])
        source = next(row for row in result["files"] if row["path"] == "a.cs")
        self.assertEqual((3, 2), (source["lines"], source["nonblank_lines"]))
        self.assertEqual(2, result["by_extension"][".cs"]["files"])
        self.assertEqual(1, result["by_extension"][".cs"]["unmeasured_files"])
        self.assertEqual(1, len(result["excluded"]))
        self.assertEqual(1, result["by_extension"][".md"]["files"])
        self.assertEqual(result, baseline.collect(self.repo, first))

    def test_baselines_follow_revision_not_worktree(self):
        (self.repo / "a.cs").write_text("a\nb\n", encoding="utf-8")
        first = self.commit()
        (self.repo / "a.cs").write_text("a\n", encoding="utf-8")
        second = self.commit()
        self.assertEqual(2, baseline.collect(self.repo, first)["by_extension"][".cs"]["lines"])
        self.assertEqual(1, baseline.collect(self.repo, second)["by_extension"][".cs"]["lines"])

    def test_invalid_revision_fails(self):
        (self.repo / "a.cs").write_text("a", encoding="utf-8")
        self.commit()
        run = subprocess.run(["python3", str(COLLECTOR), str(self.repo), "--revision", "missing-revision"],
                             capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertEqual("", run.stdout)

    def test_roslyn_syntax_and_dirty_checkout_boundaries(self):
        if CSHARP_DLL is None:
            self.skipTest("Pass --csharp-dll to exercise the optional .NET flavor")
        (self.repo / "Sample.cs").write_text('''
// if (x) for while catch; these must not count as branches
class Sample(int first, string text = "if (for)")
{
    public Sample() : this(1) { }
    public int Run(bool choice)
    {
        var words = "while if catch";
        if (choice) return 1;
        return choice ? 2 : 3;
    }
}
record Pair(int Left, int Right = 0);
''', encoding="utf-8")
        self.commit()
        command = ["dotnet", str(CSHARP_DLL), str(self.repo)]
        result = json.loads(subprocess.check_output(command))
        row = result["files"][0]
        self.assertEqual([], row["parse_errors"])
        self.assertEqual(2, row["branch_nodes"])
        self.assertEqual([0, 2, 2], sorted(c["parameters"] for c in row["constructors"]))
        self.assertEqual(2, row["defaulted_parameters"])
        self.assertEqual(2, len(result["declarations"]))
        (self.repo / "Sample.cs").write_text("class Changed {}", encoding="utf-8")
        dirty = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(0, dirty.returncode)
        self.assertEqual("", dirty.stdout)

    def catalog_fixture(self):
        if CSHARP_DLL is None:
            self.skipTest("Pass --csharp-dll to exercise catalog integration")
        (self.repo / "Types.cs").write_text('''
namespace One {
    public partial class Item { public int Method(bool b) => b ? 1 : 0; }
    public partial class Item { }
    public class Outer<T> {
        public class Inner { public void Go() { if (true) {} } }
    }
    public class Consumer {
        Item field = new Item();
        public string Words = "Item Item"; // Item must not be a name occurrence here
    }
}
namespace Two { public class Item {} public class Item<T> {} }
''', encoding="utf-8")
        (self.repo / "binary.bin").write_bytes(b"\0\xff")
        (self.repo / "view.cshtml").write_text("@model One.Item\n", encoding="utf-8")
        revision = self.commit()
        analysis = json.loads(subprocess.check_output(["dotnet", str(CSHARP_DLL), str(self.repo)]))
        artifact = self.repo / "analysis.json"
        artifact.write_text(json.dumps(analysis), encoding="utf-8")
        source = self.repo / "baseline.json"
        source.write_text(json.dumps(baseline.collect(self.repo, revision)), encoding="utf-8")
        return source, artifact, analysis

    def test_catalog_preserves_declarations_ambiguity_and_non_csharp_files(self):
        source, artifact, analysis = self.catalog_fixture()
        database = self.repo / "catalog.sqlite"
        catalog.build(database, source, artifact, "fixture")
        with sqlite3.connect(database) as db:
            self.assertEqual("ok", db.execute("PRAGMA integrity_check").fetchone()[0])
            self.assertEqual([], db.execute("PRAGMA foreign_key_check").fetchall())
            self.assertEqual(7, db.execute("SELECT count(*) FROM entities").fetchone()[0])
            self.assertEqual(2, db.execute("SELECT count(*) FROM entities WHERE qualified_name='One.Item'").fetchone()[0])
            self.assertEqual(0, db.execute("SELECT branch_nodes FROM entities WHERE name='Outer'").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT branch_nodes FROM entities WHERE name='Inner'").fetchone()[0])
            self.assertEqual(2, db.execute("SELECT count(*) FROM name_occurrences WHERE name='Item'").fetchone()[0])
            self.assertEqual(3, db.execute("SELECT same_name_declarations FROM profiles WHERE qualified_name='Two.Item'").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT count(*) FROM files WHERE extension='.cshtml'").fetchone()[0])
            self.assertIsNone(db.execute("SELECT lines FROM files WHERE extension='.bin'").fetchone()[0])
        self.assertTrue(catalog.query(database, "SELECT * FROM entities", limit=1)["truncated"])
        with self.assertRaises(sqlite3.Error):
            catalog.query(database, "DELETE FROM entities")
        with self.assertRaises(sqlite3.Error):
            catalog.query(database, "ATTACH DATABASE ':memory:' AS other")
        original = database.read_bytes()
        with self.assertRaises(FileExistsError):
            catalog.build(database, source, artifact, "fixture")
        self.assertEqual(original, database.read_bytes())

    def test_catalog_rejects_mismatched_content_revision_and_dangling_relationships(self):
        source, artifact, analysis = self.catalog_fixture()
        database = self.repo / "catalog.sqlite"
        original = json.loads(json.dumps(analysis))
        for alter in (lambda a: a.update(commit="other"),
                      lambda a: a["files"][0].update(sha256="wrong"),
                      lambda a: a.update(files=[]),
                      lambda a: a["files"].append(a["files"][0]),
                      lambda a: a["declarations"].pop(),
                      lambda a: a["declarations"][0].update(parent_id="missing")):
            analysis = json.loads(json.dumps(original))
            alter(analysis)
            artifact.write_text(json.dumps(analysis), encoding="utf-8")
            with self.assertRaises((ValueError, sqlite3.IntegrityError)):
                catalog.build(database, source, artifact, "fixture")
            self.assertFalse(database.exists())

    def test_roslyn_reads_git_blobs_despite_clean_checkout_eol_conversion(self):
        if CSHARP_DLL is None:
            self.skipTest("Pass --csharp-dll to exercise the optional .NET flavor")
        (self.repo / ".gitattributes").write_text("*.cs text eol=crlf\n", encoding="utf-8")
        source = b"class Example {\n    int Run(bool b) => b ? 1 : 0;\n}\n"
        (self.repo / "Example.cs").write_bytes(source.replace(b"\n", b"\r\n"))
        (self.repo / "UPPER.CS").write_text("class Excluded {}", encoding="utf-8")
        self.commit()
        self.assertEqual("", self.git("status", "--porcelain"))
        result = json.loads(subprocess.check_output(["dotnet", str(CSHARP_DLL), str(self.repo)]))
        measured = baseline.collect(self.repo, "HEAD")
        expected = next(f for f in measured["files"] if f["path"] == "Example.cs")
        self.assertEqual(["Example.cs"], [f["path"] for f in result["files"]])
        self.assertEqual(expected["sha256"], result["files"][0]["sha256"])
        self.assertEqual(1, result["declarations"][0]["branch_nodes"])

    def test_interpretations_are_evidenced_atomic_and_revision_scoped(self):
        source, artifact, analysis = self.catalog_fixture()
        database = self.repo / "catalog.sqlite"
        catalog.build(database, source, artifact, "fixture")
        annotations = self.repo / "annotations.json"
        payload = {"repository": "fixture", "commit": analysis["commit"], "interpretations": [{
            "entity_id": analysis["declarations"][0]["id"], "purpose": "Example responsibility",
            "author": "fixture-reviewer", "confidence": "medium",
            "evidence": [{"path": "Types.cs", "line": 3}]}]}
        annotations.write_text(json.dumps(payload), encoding="utf-8")
        catalog.annotate(database, annotations)
        self.assertEqual(1, len(catalog.query(database,
            "SELECT * FROM purpose_search WHERE purpose_search MATCH 'responsibility'")["rows"]))
        payload["interpretations"][0]["purpose"] = "Updated purpose"
        payload["interpretations"].append(dict(payload["interpretations"][0], entity_id="unknown"))
        annotations.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ValueError):
            catalog.annotate(database, annotations)
        self.assertEqual("Example responsibility", catalog.query(database,
            "SELECT purpose FROM interpretations")["rows"][0]["purpose"])
        payload["commit"] = "stale"
        annotations.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ValueError):
            catalog.annotate(database, annotations)
        payload["commit"] = analysis["commit"]
        payload["interpretations"].pop()
        for line in (True, 1.5, 0, 10000):
            payload["interpretations"][0]["evidence"][0]["line"] = line
            annotations.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                catalog.annotate(database, annotations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csharp-dll", type=Path)
    args, remainder = parser.parse_known_args()
    CSHARP_DLL = args.csharp_dll.resolve() if args.csharp_dll else None
    unittest.main(argv=[__file__, *remainder])
