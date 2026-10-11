import contextlib
import io
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skills
import porting
import seed_t3_port
import check_upstream


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

    def native(self):
        raw = self.root / "upstream/pstack/skills/example/SKILL.md"
        skills.write_json(self.root / "ports/pstack.json", {
            "schema_version": 1, "excluded_prefixes": {"example/scripts/": "Native T3 replacement"},
            "files": {"example/SKILL.md": {"strategy": "native-rewrite",
                       "upstream_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}}})
        skills.write_json(self.root / "ports/t3-tools.json", {"tools": {"delegate_task": "fixture"}})
        local = self.pack / "example/SKILL.md"
        local.write_text(local.read_text().replace(skills.BRIDGE, ""))
        return local

    def test_clean_native_merge_requires_acceptance_and_preserves_full_diff_base(self):
        local = self.native()
        original = skills.read_json(self.root / "adaptations.lock.json")["pstack"]["commit"]
        upstream = self.remote / "pstack/skills/example/SKILL.md"
        self.update("pstack/skills/example/SKILL.md", upstream.read_text().replace("Third", "Updated third"))
        self.quiet(skills.merge, self.root, "pstack")
        self.assertIn("Updated third", local.read_text())
        state = skills.read_json(self.root / "adaptations.lock.json")["pstack"]
        self.assertTrue(state["pending_port"])
        self.assertEqual(state["merge_base"]["commit"], original)
        with self.assertRaisesRegex(ValueError, "unresolved upstream merge"):
            self.quiet(skills.validate, self.root)
        self.quiet(porting.report, self.root, "pstack", save_diff=True)
        diff = (self.root / ".work/pstack-upstream.diff").read_text()
        self.assertIn("-Third", diff)
        self.assertIn("+Updated third", diff)
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.quiet(skills.validate, self.root)
        self.assertNotIn("pending_port", skills.read_json(self.root / "adaptations.lock.json")["pstack"])
        self.assertEqual(self.quiet(porting.report, self.root, "pstack"), [])

    def test_excluded_new_scripts_are_reported_but_never_installed(self):
        self.native()
        self.update("pstack/skills/example/scripts/new.ts", "Cursor-only script\n")
        self.assertIn("Excluded runtime file", "\n".join(self.quiet(porting.report, self.root, "pstack")))
        self.quiet(skills.merge, self.root, "pstack")
        self.assertFalse((self.pack / "example/scripts/new.ts").exists())
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.assertEqual(self.quiet(porting.report, self.root, "pstack"), [])

    def test_advanced_snapshot_cannot_be_mistakenly_accepted_as_pending_port(self):
        local = self.native()
        raw = self.remote / "pstack/skills/example/SKILL.md"
        self.update("pstack/skills/example/SKILL.md", raw.read_text().replace("Third", "Revision B"))
        self.quiet(skills.merge, self.root, "pstack")
        before = (self.root / "ports/pstack.json").read_bytes()
        self.update("pstack/skills/example/SKILL.md", raw.read_text().replace("Revision B", "Revision C"))
        with self.assertRaisesRegex(ValueError, "raw snapshot advanced"):
            self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.assertEqual((self.root / "ports/pstack.json").read_bytes(), before)
        self.assertIn("Revision B", local.read_text())
        self.assertTrue(self.quiet(porting.report, self.root, "pstack"))

    def test_deferred_raw_only_update_validates_until_port_is_started(self):
        self.native()
        self.update("pstack/skills/new-skill/SKILL.md", "---\nname: new-skill\ndescription: New\n---\nNew\n")
        self.quiet(skills.validate, self.root)
        self.assertIn("NEW: port", "\n".join(self.quiet(porting.report, self.root, "pstack")))
        self.quiet(skills.merge, self.root, "pstack")
        with self.assertRaisesRegex(ValueError, "Unmapped upstream file"):
            self.quiet(skills.merge, self.root, "pstack", continuing=True)

    def test_new_skill_needs_mapping_and_native_instruction_before_acceptance(self):
        self.native()
        self.update("pstack/skills/new-skill/SKILL.md", "---\nname: new-skill\ndescription: New\n---\nNew\n")
        self.quiet(skills.merge, self.root, "pstack")
        with self.assertRaisesRegex(ValueError, "Unmapped upstream file"):
            self.quiet(skills.merge, self.root, "pstack", continuing=True)
        path = self.pack / "new-skill/SKILL.md"
        path.write_text(path.read_text().replace(skills.BRIDGE, ""))
        self.quiet(porting.classify, self.root, "pstack", "new-skill/SKILL.md", "native-rewrite", "Reviewed T3 port")
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.quiet(skills.validate, self.root)

    def test_audit_rejects_cursor_remnants_unknown_tools_and_broken_references(self):
        local = self.native()
        local.write_text(local.read_text() + "Use the Task tool, `t3_missing_tool`, and [brief](missing.md).\n")
        problems = "\n".join(porting.audit(self.root, "pstack"))
        self.assertIn("legacy runtime instruction", problems)
        self.assertIn("t3_missing_tool", problems)
        self.assertIn("broken local link missing.md", problems)

    def test_audit_rejects_deleted_mapped_files_and_restored_exclusions(self):
        local = self.native()
        local.unlink()
        script = self.pack / "example/scripts/old.py"
        script.parent.mkdir(parents=True)
        script.write_text("Cursor code")
        problems = "\n".join(porting.audit(self.root, "pstack"))
        self.assertIn("Mapped upstream file missing", problems)
        self.assertIn("Excluded upstream file reintroduced", problems)

    def test_deleted_upstream_file_can_be_explicitly_retained_in_native_pack(self):
        local = self.native()
        local.write_text(local.read_text() + "Native retained behavior\n")
        (self.remote / "pstack/skills/example/SKILL.md").unlink()
        self.commit()
        self.quiet(skills.snapshot, self.root, "pstack")
        self.quiet(skills.merge, self.root, "pstack")
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.assertIn("Native retained behavior", local.read_text())
        self.assertEqual(self.quiet(porting.report, self.root, "pstack"), [])

    def test_seed_aliases_bundle_paths_and_original_invocation_settings(self):
        original = b"---\nname: poteto-mode\ndescription: Native\n---\nBody\n"
        reference = b"---\nname: p3-mode\ndescription: Native\ndisable-model-invocation: true\n---\nRead p3-models.md and agents/p3-agent.md.\n"
        result = seed_t3_port.rewrite(reference, "poteto-mode/SKILL.md", original=original).decode()
        self.assertIn(".pstack-models.md", result)
        self.assertIn("references/agents/poteto-agent.md", result)
        self.assertNotIn("disable-model-invocation", result)
        self.assertNotIn("p3-mode", result)
        with self.assertRaisesRegex(ValueError, "new candidate directory"):
            seed_t3_port.build(self.remote, self.pack, root=self.root)

    def test_selected_root_import_tracks_skills_and_license_only(self):
        self.put("LICENSE", "Root license\n")
        self.put("skills/engineering/other/SKILL.md", "---\nname: other\ndescription: Nested\n---\nNested\n")
        self.commit()
        config = skills.read_json(self.root / "sources.json")
        config["matt-pocock"] = {"url": str(self.remote), "branch": "main", "path": ".", "include": ["LICENSE", "skills"]}
        skills.write_json(self.root / "sources.json", config)
        self.quiet(skills.initialize, self.root, "matt-pocock")
        self.assertEqual(set(skills.files(self.root / "upstream/matt-pocock")),
                         {"LICENSE", "skills/engineering/other/SKILL.md"})
        self.put("README.md", "Unrelated repository documentation\n")
        self.commit()
        self.assertFalse(self.quiet(skills.snapshot, self.root, "matt-pocock"))
        self.put("LICENSE", "Root license updated\n")
        self.commit()
        self.assertTrue(self.quiet(skills.snapshot, self.root, "matt-pocock"))
        project = Path(self.temp.name) / "nested-project"
        project.mkdir()
        self.quiet(skills.install, self.root, project, "codex")
        self.assertEqual((project / ".agents/skills/other").resolve(),
                         (self.root / "skills/matt-pocock/engineering/other").resolve())

    def test_alias_migration_merges_upstream_into_originally_named_skill(self):
        self.native()
        policy = porting.manifest(self.root, "pstack")
        policy["path_aliases"] = {"example/": "local-example/"}
        policy["skill_aliases"] = {"example": "local-example"}
        skills.write_json(self.root / "ports/pstack.json", policy)
        skills.replace_files(self.pack, porting.map_contents(skills.files(self.pack), policy))
        local = self.pack / "local-example/SKILL.md"
        local.write_text(local.read_text().replace("First", "Local first"))
        raw = self.remote / "pstack/skills/example/SKILL.md"
        self.update("pstack/skills/example/SKILL.md", raw.read_text().replace("Third", "New third"))
        self.quiet(skills.merge, self.root, "pstack")
        self.quiet(skills.merge, self.root, "pstack", continuing=True)
        self.assertIn("Local first\nSecond\nNew third", local.read_text())
        self.assertIn("name: local-example", local.read_text())
        self.assertFalse((self.pack / "example").exists())
        self.assertEqual(self.quiet(porting.report, self.root, "pstack"), [])

    def test_aliases_rewrite_commands_and_local_links_without_changing_source_urls(self):
        policy = {"path_aliases": {"code-review/": "matt-code-review/"},
                  "skill_aliases": {"code-review": "matt-code-review"}}
        data = b'---\nname: code-review\ndescription: Review\n---\nUse /code-review and "code-review". [review](./code-review/SKILL.md) [source](https://example.invalid/code-review/SKILL.md)\n'
        output = porting.map_contents({"code-review/SKILL.md": data}, policy)
        text = output["matt-code-review/SKILL.md"].decode()
        self.assertIn("name: matt-code-review", text)
        self.assertIn("/matt-code-review", text)
        self.assertIn("./matt-code-review/SKILL.md", text)
        self.assertIn("https://example.invalid/code-review/SKILL.md", text)
        self.assertEqual(porting.map_contents(output, policy), output)

    def test_alias_collision_stops_before_install_changes_existing_skills(self):
        personal = self.root / "skills/elsewhere/engineering/example"
        personal.mkdir(parents=True)
        (personal / "SKILL.md").write_text("---\nname: example\ndescription: Duplicate\n---\nBody\n")
        project = Path(self.temp.name) / "collision-project"
        project.mkdir()
        with self.assertRaisesRegex(ValueError, "Duplicate skill names"):
            self.quiet(skills.install, self.root, project, "codex")
        self.assertFalse((project / ".agents").exists())

    def test_install_migrates_only_declared_owned_alias_links(self):
        self.native()
        project = Path(self.temp.name) / "migration-project"
        project.mkdir()
        self.quiet(skills.install, self.root, project, "codex")
        policy = porting.manifest(self.root, "pstack")
        policy["path_aliases"] = {"example/": "local-example/"}
        policy["skill_aliases"] = {"example": "local-example"}
        skills.replace_files(self.pack, porting.map_contents(skills.files(self.pack), policy))
        skills.write_json(self.root / "ports/pstack.json", policy)
        self.quiet(skills.install, self.root, project, "codex")
        self.assertFalse((project / ".agents/skills/example").is_symlink())
        self.assertEqual((project / ".agents/skills/local-example").resolve(), (self.pack / "local-example").resolve())
        self.quiet(skills.install, self.root, project, "codex")
        link = project / ".agents/skills/local-example"
        link.unlink()
        foreign = Path(self.temp.name) / "foreign-skill"
        foreign.mkdir()
        link.symlink_to(foreign, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Refusing to replace"):
            self.quiet(skills.install, self.root, project, "codex")
        self.assertEqual(link.resolve(), foreign.resolve())

    def test_two_source_updater_creates_independent_review_branches(self):
        self.native()
        configs = skills.read_json(self.root / "sources.json")
        configs["pstack"].update(web_url="https://example.invalid/source", reviewer="maintainer")
        configs["other"] = dict(configs["pstack"])
        skills.write_json(self.root / "sources.json", configs)
        self.quiet(skills.initialize, self.root, "other")
        skills.run("git", "init", "--quiet", "-b", "main", str(self.root))
        skills.run("git", "config", "user.name", "Test", cwd=self.root)
        skills.run("git", "config", "user.email", "test@example.invalid", cwd=self.root)
        skills.run("git", "add", "-A", cwd=self.root)
        skills.run("git", "commit", "--quiet", "-m", "Initial collection", cwd=self.root)
        target = Path(self.temp.name) / "collection-origin"
        skills.run("git", "init", "--quiet", "--bare", str(target))
        skills.run("git", "remote", "add", "origin", str(target), cwd=self.root)
        skills.run("git", "push", "--quiet", "origin", "main", cwd=self.root)
        initial = skills.read_json(self.root / "sources.lock.json")
        raw = self.remote / "pstack/skills/example/SKILL.md"
        self.put("pstack/skills/example/SKILL.md", raw.read_text().replace("Third", "Updated third"))
        self.commit()
        created = []
        def command(*args):
            if args[:3] == ("gh", "pr", "list"):
                return "[]"
            if args[:3] == ("gh", "pr", "create"):
                body = Path(args[args.index("--body-file") + 1]).read_text()
                self.assertIn("--reviewer", args)
                created.append((args[args.index("--head") + 1], body,
                                skills.read_json(self.root / "sources.lock.json")))
                return "https://example.invalid/pull/1"
            return skills.run(*args, cwd=self.root).stdout.decode().strip()
        with patch.object(check_upstream, "ROOT", self.root), patch.object(check_upstream, "command", command), \
                patch.dict(check_upstream.os.environ, {"GITHUB_REPOSITORY": "owner/collection"}):
            self.quiet(check_upstream.main)
        self.assertEqual([row[0] for row in created], ["sync/pstack", "sync/other"])
        self.assertIn("report pstack --diff", created[0][1])
        self.assertEqual(created[0][2]["other"], initial["other"])
        self.assertEqual(created[1][2]["pstack"], initial["pstack"])
        self.assertEqual(skills.run("git", "branch", "--show-current", cwd=self.root).stdout.strip(), b"main")
        self.assertEqual(skills.read_json(self.root / "sources.lock.json"), initial)

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
