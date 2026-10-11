import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skills


class SkillsBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "collection"
        self.remote = Path(self.temp.name) / "remote"
        self.root.mkdir()
        self.remote.mkdir()
        skills.run("git", "init", "--quiet", "-b", "main", str(self.remote))
        skills.run("git", "config", "user.name", "Test", cwd=self.remote)
        skills.run("git", "config", "user.email", "test@example.invalid", cwd=self.remote)
        self.put("pstack/LICENSE", "Test fixture license\n")
        self.put("pstack/skills/example/SKILL.md",
                 "---\nname: Example\ndescription: Test skill\nmode: true\n---\n\n# Example\n\nFirst\nSecond\nThird\n")
        self.put("unrelated/SKILL.md", "Must not be imported\n")
        self.commit()
        skills.write_json(self.root / "sources.json", {
            "pstack": {"url": str(self.remote), "branch": "main", "path": "pstack"}})
        self.quiet(skills.snapshot, self.root, "pstack")
        self.pack = self.root / "skills/pstack"
        skills.replace_files(self.pack, skills.transform(skills.files(self.root / "upstream/pstack/skills")))
        skills.write_json(self.root / "adaptations.lock.json", skills.read_json(self.root / "sources.lock.json"))

    def quiet(self, function, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return function(*args, **kwargs)

    def put(self, name, text):
        path = self.remote / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self):
        skills.run("git", "add", "-A", cwd=self.remote)
        skills.run("git", "commit", "--quiet", "-m", "Update fixture", cwd=self.remote)

    def update(self, name, text):
        self.put(name, text)
        self.commit()
        self.quiet(skills.snapshot, self.root, "pstack")

    def test_only_selected_subtree_is_imported(self):
        self.assertEqual(set(skills.files(self.root / "upstream/pstack")),
                         {"LICENSE", "skills/example/SKILL.md"})
        self.assertFalse((self.root / "upstream/unrelated").exists())

    def test_unrelated_commits_leave_snapshot_and_lock_unchanged(self):
        before = (self.root / "sources.lock.json").read_bytes()
        self.put("unrelated/new.md", "Other plugin update\n")
        self.commit()
        self.assertFalse(self.quiet(skills.snapshot, self.root, "pstack"))
        self.assertEqual((self.root / "sources.lock.json").read_bytes(), before)

    def test_sync_preserves_user_changes(self):
        local = self.pack / "example/SKILL.md"
        local.write_text(local.read_text() + "My preference\n")
        self.update("pstack/README.md", "New upstream documentation\n")
        self.assertTrue(local.read_text().endswith("My preference\n"))

    def test_three_way_merge_keeps_local_addition_and_upstream_edit(self):
        local = self.pack / "example/SKILL.md"
        local.write_text(local.read_text().replace("First\n", "My first\n"))
        upstream = self.remote / "pstack/skills/example/SKILL.md"
        self.update("pstack/skills/example/SKILL.md", upstream.read_text().replace("Third\n", "New third\n"))
        personal = self.pack / "my-skill/SKILL.md"
        personal.parent.mkdir()
        personal.write_text("---\nname: my-skill\ndescription: Mine\n---\nMine\n")
        self.quiet(skills.merge, self.root, "pstack")
        self.assertIn("My first\nSecond\nNew third\n", local.read_text())
        self.assertEqual(personal.read_text(), "---\nname: my-skill\ndescription: Mine\n---\nMine\n")
        before = skills.files(self.pack)
        self.quiet(skills.merge, self.root, "pstack")
        self.assertEqual(skills.files(self.pack), before)

    def test_overlap_blocks_validation_until_resolved(self):
        local = self.pack / "example/SKILL.md"
        local.write_text(local.read_text().replace("Second\n", "My second\n"))
        upstream = self.remote / "pstack/skills/example/SKILL.md"
        self.update("pstack/skills/example/SKILL.md", upstream.read_text().replace("Second\n", "Their second\n"))
        self.quiet(skills.merge, self.root, "pstack")
        self.assertIn("<<<<<<< ours", local.read_text())
        self.assertIn("Their second", local.read_text())
        with self.assertRaises(ValueError):
            self.quiet(skills.validate, self.root)
        local.write_text("---\nname: example\ndescription: Resolved\n---\nMy second and their second\n")
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.quiet(skills.validate, self.root)
        self.assertFalse((self.root / ".sync-conflicts/pstack").exists())

    def test_upstream_deletion_removes_unmodified_file(self):
        (self.remote / "pstack/skills/example/SKILL.md").unlink()
        self.commit()
        self.quiet(skills.snapshot, self.root, "pstack")
        self.quiet(skills.merge, self.root, "pstack")
        self.assertFalse((self.pack / "example/SKILL.md").exists())

    def test_edit_delete_conflict_preserves_local_choice(self):
        local = self.pack / "example/SKILL.md"
        local.write_text(local.read_text() + "My work\n")
        (self.remote / "pstack/skills/example/SKILL.md").unlink()
        self.commit()
        self.quiet(skills.snapshot, self.root, "pstack")
        self.quiet(skills.merge, self.root, "pstack")
        self.assertTrue(local.read_text().endswith("My work\n"))
        self.assertEqual(skills.read_json(self.root / "adaptations.lock.json")["pstack"]["conflicts"],
                         ["example/SKILL.md"])

    def test_binary_conflict_retains_local_file(self):
        result, conflict = skills.merge_file(b"\0base", b"\0mine", b"\0theirs")
        self.assertEqual(result, b"\0mine")
        self.assertTrue(conflict)

    def test_install_is_repeatable_and_preserves_existing_skills(self):
        project = Path(self.temp.name) / "project"
        project.mkdir()
        self.quiet(skills.install, self.root, project, "codex")
        link = project / ".agents/skills/example"
        self.assertTrue(link.is_symlink())
        self.assertEqual((link / "SKILL.md").read_bytes(), (self.pack / "example/SKILL.md").read_bytes())
        self.quiet(skills.install, self.root, project, "codex")
        link.unlink()
        link.mkdir()
        (link / "SKILL.md").write_text("Existing skill")
        with self.assertRaises(ValueError):
            self.quiet(skills.install, self.root, project, "codex")
        self.assertEqual((link / "SKILL.md").read_text(), "Existing skill")

    def test_frontmatter_port_keeps_skill_description_and_normalizes_name(self):
        text = (self.pack / "example/SKILL.md").read_text()
        self.assertIn("name: example\ndescription: Test skill\n", text)
        self.assertNotIn("mode: true", text)

    def test_initialize_records_base_and_refuses_to_reset_existing_pack(self):
        shutil.rmtree(self.pack)
        self.quiet(skills.initialize, self.root, "pstack")
        self.assertEqual((self.pack / "LICENSE").read_text(), "Test fixture license\n")
        self.assertEqual(skills.read_json(self.root / "adaptations.lock.json")["pstack"],
                         skills.read_json(self.root / "sources.lock.json")["pstack"])
        with self.assertRaises(ValueError):
            self.quiet(skills.initialize, self.root, "pstack")


if __name__ == "__main__":
    unittest.main()
