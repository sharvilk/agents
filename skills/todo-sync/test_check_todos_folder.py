"""Tests for check-todos-folder.py. Each test builds its folders in a temporary directory and runs the script
there, with HOME and CLAUDE_CONFIG_DIR pointed at it, so the real config folder is never read.
Run: python3 -I test_check_todos_folder.py"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'check-todos-folder.py'
ID = '0b9e7c1a-2f3d-4e5f-8a9b-0c1d2e3f4a5b'
OTHER_ID = 'f1e2d3c4-b5a6-4978-8695-a4b3c2d1e0f9'


class CheckFolder(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.config = self.home / 'config'
        self.lists = self.config / 'todo-sync'

    def run_check(self, *args, env_config=True):
        env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_CONFIG_DIR'}
        env['HOME'] = str(self.home)
        if env_config:
            env['CLAUDE_CONFIG_DIR'] = str(self.config)
        done = subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True,
                              env=env, timeout=30)
        return done.returncode, done.stdout, done.stderr

    def write(self, path, text='- [ ] item\n'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_a_folder_of_lists_passes(self):
        self.write(self.lists / 'billing' / f'{ID}.md')
        self.write(self.lists / 'billing' / f'{OTHER_ID}.md')
        self.write(self.lists / 'billing' / '.DS_Store')
        code, out, _ = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn('holds only todo lists', out)

    def test_a_list_with_another_md_name_passes(self):
        # Only names that start with a session id are held to <session-id>.md.
        self.write(self.lists / 'billing' / 'plan.md')
        code, _, _ = self.run_check()
        self.assertEqual(code, 0)

    def test_no_folders_yet_passes(self):
        code, out, _ = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn('no list folder at', out)

    def test_a_file_in_the_folder_itself(self):
        self.write(self.lists / 'notes.md')
        code, out, err = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('notes.md -> file in the list folder itself', out)
        self.assertIn(f'1 entry in {self.lists} is not a todo list', err)

    def test_a_symlink_in_the_folder_itself_is_not_entered(self):
        target = self.write(self.home / 'elsewhere' / 'x.txt').parent
        self.lists.mkdir(parents=True)
        (self.lists / 'linked').symlink_to(target)
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('linked -> symlink in the list folder itself', out)
        self.assertNotIn('x.txt', out)

    def test_a_subfolder_is_one_line_with_its_count(self):
        for n in range(3):
            self.write(self.lists / 'billing' / 'copied-source' / 'src' / f'f{n}.py')
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('billing/copied-source/ -> subfolder (3 files)', out)
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_backup_copies(self):
        for name in (f'{ID}.md.presync-1003.bak', f'{ID}.pre-sync-2026-10-01.md', f'{ID}.bak.md', 'list.backup.md'):
            self.write(self.lists / 'billing' / name)
        code, out, err = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(out.count('backup copy of a list'), 4)
        self.assertIn('4 entries in', err)

    def test_side_files_named_after_a_session(self):
        for name in (f'{ID}-notes.md', f'{ID}.old.md', f'copy of {ID}.md'):
            self.write(self.lists / 'billing' / name)
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(out.count('named after a session but not <session-id>.md'), 3)

    def test_a_file_that_is_not_markdown(self):
        self.write(self.lists / 'billing' / 'results.json', '{}')
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('billing/results.json -> not a .md file', out)

    def test_a_hidden_file_other_than_ds_store(self):
        self.write(self.lists / 'billing' / f'{ID}.md')
        self.write(self.lists / 'billing' / '.scratch.json', '{}')
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('billing/.scratch.json -> not a .md file', out)

    def test_two_entries_are_summarised_in_the_plural(self):
        self.write(self.lists / 'billing' / 'a.json', '{}')
        self.write(self.lists / 'billing' / 'b.json', '{}')
        _, _, err = self.run_check()
        self.assertIn(f'2 entries in {self.lists} are not todo lists', err)

    def test_a_symlink_in_an_initiative(self):
        target = self.write(self.home / 'elsewhere' / 'x.md')
        self.write(self.lists / 'billing' / f'{ID}.md')
        (self.lists / 'billing' / 'link.md').symlink_to(target)
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn('billing/link.md -> symlink', out)

    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0, 'root reads any folder')
    def test_an_unreadable_initiative_makes_the_check_incomplete(self):
        locked = self.lists / 'locked'
        self.write(locked / f'{ID}.md')
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn('locked/ -> unreadable', out)
        self.assertIn('the check is incomplete', err)

    def test_a_list_folder_that_is_a_file(self):
        self.write(self.lists, 'not a folder')
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn(f'{self.lists} -> not a real folder', out)

    def test_a_list_folder_that_is_a_symlink(self):
        target = self.write(self.home / 'elsewhere' / 'billing' / f'{ID}.md').parent.parent
        self.config.mkdir()
        self.lists.symlink_to(target)
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn(f'{self.lists} -> not a real folder', out)

    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0, 'root reads any folder')
    def test_an_unreadable_list_folder(self):
        self.write(self.lists / 'billing' / f'{ID}.md')
        self.lists.chmod(0)
        self.addCleanup(self.lists.chmod, 0o755)
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn(f'{self.lists} -> unreadable', out)
        self.assertIn('1 folder could not be read', err)

    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0, 'root reads any folder')
    def test_a_partly_unreadable_subfolder(self):
        self.write(self.lists / 'billing' / 'copied' / 'a.py')
        locked = self.lists / 'billing' / 'copied' / 'locked'
        self.write(locked / 'b.py')
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        # The locked part was not counted, so the count is a floor.
        self.assertIn('billing/copied/ -> subfolder (at least 1 file)', out)
        self.assertIn('billing/copied/ -> partly unreadable', out)
        # The finding is still summarised when the check is incomplete.
        self.assertIn('1 entry in', err)
        self.assertIn('the check is incomplete', err)

    def test_an_explicit_folder_overrides_the_config_folder(self):
        lists = self.home / 'a'
        self.write(self.lists / 'notes.md')
        self.write(lists / 'billing' / f'{ID}.md')
        code, out, _ = self.run_check(str(lists))
        self.assertEqual(code, 0)
        self.assertIn(f'OK - {lists} holds only todo lists', out)

    def test_without_a_config_dir_it_uses_the_home_folder(self):
        self.write(self.home / '.claude' / 'todo-sync' / 'notes.md')
        code, out, _ = self.run_check(env_config=False)
        self.assertEqual(code, 1)
        self.assertIn(str(self.home / '.claude' / 'todo-sync' / 'notes.md'), out)


if __name__ == '__main__':
    unittest.main()
