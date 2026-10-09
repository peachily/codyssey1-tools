import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from git_utils import GitError, check_repository, collect_changes, read_status, run_git


class GitUtilsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)

    def stage(self, filename):
        subprocess.run(["git", "add", "--", filename], cwd=self.root, check=True)

    def test_repository_root(self):
        self.assertEqual(check_repository(self.root), self.root)

    def test_non_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(GitError, "Git 저장소"):
                check_repository(Path(directory))

    def test_subdirectory_rejected(self):
        child = self.root / "child"
        child.mkdir()
        with self.assertRaisesRegex(GitError, "최상위"):
            check_repository(child)

    def test_no_changes(self):
        self.assertEqual(collect_changes(self.root), ([], "", 0))

    def test_untracked_file_with_spaces_and_korean(self):
        name = "새 파일.txt"
        (self.root / name).write_text("hello\n", encoding="utf-8")
        files, diff, excluded = collect_changes(self.root)
        self.assertEqual(files, [name])
        self.assertIn("+hello", diff)
        self.assertEqual(excluded, 0)

    def test_initial_staged_and_unstaged_changes_are_combined(self):
        file = self.root / "app.py"
        file.write_text("middle\n", encoding="utf-8")
        self.stage("app.py")
        file.write_text("final\n", encoding="utf-8")
        before = run_git(["status", "--porcelain=v2", "-z"], self.root)
        files, diff, _ = collect_changes(self.root)
        after = run_git(["status", "--porcelain=v2", "-z"], self.root)
        self.assertEqual(before, after)
        self.assertEqual(files, ["app.py"])
        self.assertEqual(diff.count("+final"), 1)
        self.assertNotIn("middle", diff)
        self.assertEqual(run_git(["diff", "--cached"], self.root).count("+middle"), 1)

    def test_staged_new_file(self):
        (self.root / "added.txt").write_text("staged\n", encoding="utf-8")
        self.stage("added.txt")
        self.assertIn("+staged", collect_changes(self.root)[1])

    def test_initial_added_then_deleted_is_no_net_change(self):
        file = self.root / "removed.txt"
        file.write_text("temporary", encoding="utf-8")
        self.stage(file.name)
        file.unlink()
        self.assertEqual(collect_changes(self.root), ([], "", 0))

    def test_sensitive_file_excluded_before_read(self):
        (self.root / ".env").write_text("PASSWORD=private", encoding="utf-8")
        with patch("git_utils.new_file_diff") as reader:
            self.assertEqual(collect_changes(self.root), ([], "", 1))
            reader.assert_not_called()
        self.assertIn("private", collect_changes(self.root, False)[1])

    def test_binary_content_omitted(self):
        (self.root / "image.bin").write_bytes(b"\x00private\xff")
        self.assertNotIn("private", collect_changes(self.root)[1])

    def test_symlink_target_not_read(self):
        with tempfile.TemporaryDirectory() as directory:
            secret = Path(directory) / "outside"
            secret.write_text("outside-secret", encoding="utf-8")
            (self.root / "link.txt").symlink_to(secret)
            self.assertNotIn("outside-secret", collect_changes(self.root)[1])

    def test_tracked_changes_use_one_head_diff(self):
        with patch("git_utils.read_status", return_value=(False, [("app.py", None, False)])):
            with patch("git_utils.run_git", return_value="-old\n+final\n") as git:
                self.assertEqual(collect_changes(self.root), (["app.py"], "-old\n+final\n", 0))
                git.assert_called_once()
                arguments = git.call_args.args[0]
                self.assertIn("HEAD", arguments)
                self.assertIn("--no-ext-diff", arguments)
                self.assertIn("--no-textconv", arguments)

    def test_tracked_reverted_change_is_skipped(self):
        with patch("git_utils.read_status", return_value=(False, [("app.py", None, False)])):
            with patch("git_utils.run_git", return_value=""):
                self.assertEqual(collect_changes(self.root), ([], "", 0))

    def test_sensitive_rename_source_is_excluded(self):
        with patch("git_utils.read_status", return_value=(False, [("ordinary.txt", ".env", False)])):
            with patch("git_utils.run_git") as git:
                self.assertEqual(collect_changes(self.root), ([], "", 1))
                git.assert_not_called()

    def test_status_rename_and_newline_filename(self):
        status = "# branch.oid abc\0" + "2 R. N... 100644 100644 100644 abc abc R100 new\nname\0old name\0"
        with patch("git_utils.run_git", return_value=status):
            self.assertEqual(read_status(self.root), (False, [("new\nname", "old name", False)]))

    def test_conflict_rejected(self):
        with patch("git_utils.run_git", return_value="u UU conflict\0"):
            with self.assertRaisesRegex(GitError, "충돌"):
                read_status(self.root)

    def test_git_missing_timeout_and_failure(self):
        for error in [FileNotFoundError(), subprocess.TimeoutExpired("git", 30)]:
            with self.subTest(error=type(error).__name__):
                with patch("git_utils.subprocess.run", side_effect=error):
                    with self.assertRaises(GitError):
                        run_git(["status"], self.root)
        result = subprocess.CompletedProcess([], 128, b"", b"unexpected secret-token")
        with patch("git_utils.subprocess.run", return_value=result):
            with self.assertRaises(GitError) as caught:
                run_git(["status"], self.root)
            self.assertNotIn("secret-token", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
