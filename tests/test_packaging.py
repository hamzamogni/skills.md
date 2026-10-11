from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import package_skills
import skills


class PortablePackaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pack = self.root / 'skills/author'
        self.pack.mkdir(parents=True)
        (self.pack / 'runtime.md').write_text('Native runtime instructions\n')
        (self.pack / 'LICENSE').write_text('Copyright fixture author\nPermission notice\n')
        for name in ('one', 'two'):
            entry = self.pack / name / 'SKILL.md'
            entry.parent.mkdir()
            entry.write_text(f'---\nname: {name}\ndescription: Fixture\n---\nRead [runtime](references/t3-runtime.md).\n')
        skills.write_json(self.root / 'bundles.json', {'skills/author': {
            'skills/author/runtime.md': 'references/t3-runtime.md', 'skills/author/LICENSE': 'LICENSE'}})

    def test_bundles_preserve_edits_and_refresh_shared_guidance_and_notices(self):
        self.assertEqual(package_skills.build(self.root), 4)
        entry = self.pack / 'one/SKILL.md'
        entry.write_text(entry.read_text() + 'Personal workflow\n')
        self.assertEqual(package_skills.build(self.root), 0)
        (self.pack / 'runtime.md').write_text('Changed native contract\n')
        (self.pack / 'LICENSE').write_text('Updated copyright and notice\n')
        with self.assertRaisesRegex(ValueError, 'Stale bundle'):
            package_skills.check(self.root)
        self.assertEqual(package_skills.build(self.root), 4)
        package_skills.check(self.root)
        self.assertIn('Personal workflow', entry.read_text())
        self.assertEqual((self.pack / 'two/references/t3-runtime.md').read_text(), 'Changed native contract\n')
        self.assertEqual((self.pack / 'two/LICENSE').read_text(), 'Updated copyright and notice\n')

    def test_flat_copies_resolve_bundled_and_other_installed_skill_references(self):
        entry = self.pack / 'one/SKILL.md'
        entry.write_text(entry.read_text() + 'Read [two](../two/SKILL.md).\n')
        package_skills.build(self.root)
        destination = self.root / 'installed'
        for name in ('one', 'two'):
            shutil.copytree(self.pack / name, destination / name)
        self.assertEqual(package_skills.flat_link_problems(destination), [])
        (destination / 'one/references/t3-runtime.md').unlink()
        self.assertEqual(package_skills.flat_link_problems(destination),
                         ['one/SKILL.md: missing installed reference references/t3-runtime.md'])

    def test_validation_rejects_repository_only_paths_and_changed_bundle_copies(self):
        package_skills.build(self.root)
        runtime = self.pack / 'one/references/t3-runtime.md'
        runtime.write_text('Accidental edit to generated file\n')
        with self.assertRaisesRegex(ValueError, 'Stale bundle'):
            skills.validate(self.root)
        package_skills.build(self.root)
        entry = self.pack / 'one/SKILL.md'
        entry.write_text(entry.read_text() + 'Read [shared](../../runtime.md).\n')
        with self.assertRaisesRegex(ValueError, 'missing installed reference ../../runtime.md'):
            skills.validate(self.root)

    def test_bundle_manifest_cannot_write_outside_the_skill(self):
        outside = self.root / 'outside.md'
        outside.write_text('Untouched\n')
        skills.write_json(self.root / 'bundles.json', {'skills/author': {'skills/author/runtime.md': '../../outside.md'}})
        with self.assertRaisesRegex(ValueError, 'escapes its skill'):
            package_skills.build(self.root)
        self.assertEqual(outside.read_text(), 'Untouched\n')
