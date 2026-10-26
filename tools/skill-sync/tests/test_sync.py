import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("skill_sync", Path(__file__).parents[1] / "sync.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools/skill-sync").mkdir(parents=True)
        self.source = self.root / ".claude/skills/cyk-example"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text("---\nname: cyk-example\n---\nOriginal\n")
        self.config = {"version": 1, "skills": {"cyk-example": {"mode": "link", "reason": "test"}}}
        self.save()

    def save(self):
        (self.root / "tools/skill-sync/config.json").write_text(json.dumps(self.config))

    def run_sync(self, command="apply", adopt=False):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return sync.synchronize(self.root, command, adopt)

    @property
    def output(self):
        return self.root / ".agents/skills/cyk-example"

    def test_check_is_read_only_and_apply_is_idempotent(self):
        self.assertEqual(self.run_sync("check"), 1)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".skill-sync").exists())
        self.assertEqual(self.run_sync(), 0)
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(self.run_sync("check"), 0)
        self.assertEqual(self.run_sync(), 0)
        self.assertFalse((self.root / ".skill-sync/backups").exists())
        (self.source / "SKILL.md").write_text("Changed")
        self.assertEqual((self.output / "SKILL.md").read_text(), "Changed")

    def test_new_unclassified_skill_blocks_all_writes(self):
        other = self.source.parent / "cyk-new"
        other.mkdir()
        (other / "SKILL.md").write_text("new")
        self.assertEqual(self.run_sync(), 2)
        self.assertFalse(self.output.exists())

    def test_adoption_preserves_existing_output(self):
        self.output.mkdir(parents=True)
        (self.output / "SKILL.md").write_text("previous copy")
        self.assertEqual(self.run_sync(), 2)
        self.assertEqual((self.output / "SKILL.md").read_text(), "previous copy")
        self.assertEqual(self.run_sync(adopt=True), 0)
        backups = list((self.root / ".skill-sync/backups").glob("*/cyk-example/SKILL.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "previous copy")

    def test_exclusion_removes_only_managed_output_and_keeps_backup(self):
        self.run_sync()
        self.config["skills"]["cyk-example"]["mode"] = "exclude"
        self.save()
        self.assertEqual(self.run_sync(), 0)
        self.assertFalse(self.output.is_symlink())
        self.assertEqual(self.run_sync("check"), 0)
        self.assertEqual(len(list((self.root / ".skill-sync/backups").glob("*/cyk-example"))), 1)

    def test_deleted_source_requires_config_update(self):
        self.run_sync()
        (self.source / "SKILL.md").unlink()
        self.source.rmdir()
        self.assertEqual(self.run_sync(), 2)
        self.config["skills"].clear()
        self.save()
        self.assertEqual(self.run_sync(), 0)
        self.assertFalse(self.output.is_symlink())

    def overlay(self):
        overlay = self.root / "tools/skill-sync/overrides/cyk-example"
        overlay.mkdir(parents=True)
        (overlay / "SKILL.md").write_text("Codex-specific text")
        (self.source / "resource.txt").write_text("shared resource")
        self.config["skills"]["cyk-example"].update(mode="overlay", source_digest=sync.digest(self.source))
        self.save()

    def test_overlay_preserves_resources_and_rejects_stale_source(self):
        self.overlay()
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual((self.output / "SKILL.md").read_text(), "Codex-specific text")
        self.assertEqual((self.output / "resource.txt").read_text(), "shared resource")
        (self.source / "resource.txt").write_text("changed resource")
        self.assertEqual(self.run_sync(), 2)
        self.assertEqual((self.output / "resource.txt").read_text(), "shared resource")

    def test_output_edits_are_never_overwritten(self):
        self.overlay()
        self.run_sync()
        (self.output / "SKILL.md").write_text("user edit")
        self.assertEqual(self.run_sync(), 2)
        self.assertEqual(self.run_sync(adopt=True), 2)
        self.assertEqual((self.output / "SKILL.md").read_text(), "user edit")

    def test_unrelated_skills_are_untouched(self):
        other = self.root / ".agents/skills/another-vendor"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("not ours")
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual((other / "SKILL.md").read_text(), "not ours")

    def test_overlay_does_not_write_through_source_resource_link(self):
        self.overlay()
        resource = self.root / "outside.txt"
        resource.write_text("original external")
        (self.source / "linked.txt").symlink_to(resource)
        (self.root / "tools/skill-sync/overrides/cyk-example/linked.txt").write_text("replacement")
        self.config["skills"]["cyk-example"]["source_digest"] = sync.digest(self.source)
        self.save()
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(resource.read_text(), "original external")
        self.assertEqual((self.output / "linked.txt").read_text(), "replacement")

    def test_redirected_output_parent_is_rejected(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.root / ".agents").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(sync.SyncError):
            self.run_sync()
        self.assertEqual(list(elsewhere.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
