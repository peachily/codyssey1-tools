import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from git_utils import GitError
from main import build_parser, main
from test_ai_client import make_response, success_response
from test_validators import VALID_PR


class MainTests(unittest.TestCase):
    def run_command(self, argv, changes=(["app.py"], "+print('hello')", 0), response=None, key="test-key"):
        output = io.StringIO()
        with patch("main.check_repository", return_value=Path("/temporary-repo")):
            with patch("main.collect_changes", return_value=changes):
                with patch.dict(os.environ, {"AI_API_KEY": key}):
                    with patch("ai_client.requests.post", return_value=response if response is not None else success_response()) as post:
                        with redirect_stdout(output), redirect_stderr(output):
                            code = main(argv)
        return code, output.getvalue(), post

    def test_commit_one_call(self):
        code, output, post = self.run_command(["commit"])
        self.assertEqual(code, 0)
        self.assertIn("[DONE]", output)
        self.assertIn("API 호출 횟수: 1", output)
        post.assert_called_once()

    def test_pr_one_call(self):
        code, output, post = self.run_command(["pr"], response=success_response(VALID_PR))
        self.assertEqual(code, 0)
        self.assertIn("## How to Test", output)
        post.assert_called_once()

    def test_no_changes_and_only_excluded_files_skip_api(self):
        for excluded in [0, 2]:
            code, output, post = self.run_command(["commit"], ([], "", excluded), key="")
            self.assertEqual(code, 0)
            self.assertIn("API 호출 횟수: 0", output)
            post.assert_not_called()

    def test_missing_key_skips_api(self):
        code, output, post = self.run_command(["commit"], key="")
        self.assertEqual(code, 1)
        self.assertIn("AI_API_KEY", output)
        self.assertIn("API 호출 횟수: 0", output)
        post.assert_not_called()

    def test_validation_failure_does_not_retry(self):
        code, output, post = self.run_command(["commit"], response=success_response("제목만 있어요."))
        self.assertEqual(code, 1)
        self.assertIn("형식 검증", output)
        self.assertIn("API 호출 횟수: 1", output)
        post.assert_called_once()

    def test_http_failure_does_not_retry(self):
        code, output, post = self.run_command(["commit"], response=make_response({}, 429))
        self.assertEqual(code, 1)
        self.assertIn("API 호출 횟수: 1", output)
        post.assert_called_once()

    def test_default_safe_mode_masks_whole_request(self):
        changes = (["user@example.com.txt"], "+password=private\n+test-key", 0)
        code, _, post = self.run_command(["commit"], changes)
        self.assertEqual(code, 0)
        messages = json.dumps(post.call_args.kwargs["json"]["messages"])
        for secret in ["user@example.com", "private", "test-key"]:
            self.assertNotIn(secret, messages)

    def test_no_safe_mode_warns_and_preserves_request(self):
        code, output, post = self.run_command(["commit", "--no-safe-mode"], (["app.py"], "password=private", 0))
        self.assertEqual(code, 0)
        self.assertIn("안전 모드가 꺼져", output)
        self.assertIn("password=private", post.call_args.kwargs["json"]["messages"][1]["content"])

    def test_response_secrets_never_printed(self):
        code, output, _ = self.run_command(["commit", "--no-safe-mode"], response=success_response("fix: 설정 수정\n\n- password=private test-key"))
        self.assertEqual(code, 0)
        self.assertNotIn("private", output)
        self.assertNotIn("test-key", output)

    def test_git_failure_skips_api(self):
        output = io.StringIO()
        with patch("main.check_repository", side_effect=GitError("Git 저장소 오류")):
            with patch("ai_client.requests.post") as post:
                with redirect_stdout(output), redirect_stderr(output):
                    self.assertEqual(main(["commit"]), 1)
                post.assert_not_called()
        self.assertIn("API 호출 횟수: 0", output.getvalue())

    def test_bad_options_rejected_in_korean_without_echoing_values(self):
        cases = [[], ["wrong-command"], ["commit", "--temperature", "nan"],
                 ["commit", "--temperature", "inf"], ["commit", "--temperature", "2.1"],
                 ["commit", "--max-tokens", "0"], ["commit", "--max-tokens", "128001"],
                 ["commit", "--max-tokens", "1.5"], ["commit", "--model", "private key"],
                 ["commit", "--safe-mode", "--no-safe-mode"], ["commit", "--unknown"]]
        for argv in cases:
            with self.subTest(argv=argv):
                output = io.StringIO()
                with redirect_stderr(output), self.assertRaises(SystemExit) as caught:
                    build_parser().parse_args(argv)
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("올바르지", output.getvalue())
                self.assertNotIn("private key", output.getvalue())


if __name__ == "__main__":
    unittest.main()
