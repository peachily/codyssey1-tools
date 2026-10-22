"""명령 등록, 도움말, 공통 오류 처리와 실제 진입점을 검증한다."""

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from peach_pantry.cli import build_parser, main
from peach_pantry.errors import PantryError, handle_errors
from peach_pantry.formatter import format_title, print_error


class CliTests(unittest.TestCase):
    """실제 CLI 계약과 데이터에 영향을 주지 않는 초기 동작을 확인한다."""

    def test_help_for_every_command(self) -> None:
        commands = [[], ["add"], ["list"], ["search"], ["update"], ["delete"],
                    ["category"], ["category", "add"], ["category", "list"],
                    ["category", "remove"], ["budget"], ["budget", "set"],
                    ["summary"], ["import"], ["export"]]
        for command in commands:
            with self.subTest(command=command), TemporaryDirectory() as temp:
                result = subprocess.run(
                    [sys.executable, "-m", "peach_pantry", "--data-dir",
                     str(Path(temp) / "data"), *command, "--help"],
                    cwd=Path(__file__).resolve().parents[1], capture_output=True,
                    text=True, encoding="utf-8",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--help", result.stdout)
                self.assertIn("--data-dir", result.stdout)
                self.assertEqual(result.stderr, "")
                self.assertFalse((Path(temp) / "data").exists())

    def test_data_dir_at_every_command_level(self) -> None:
        for argv in (["--data-dir", "custom", "list"],
                     ["list", "--data-dir", "custom"],
                     ["category", "--data-dir", "custom", "list"],
                     ["category", "list", "--data-dir", "custom"]):
            with self.subTest(argv=argv):
                self.assertEqual(build_parser().parse_args(argv).data_dir, Path("custom"))
        self.assertEqual(build_parser().parse_args(["list"]).data_dir, Path("data"))

    def test_all_command_options(self) -> None:
        parser = build_parser()
        cases = [
            (["add"], {"command": "add"}),
            (["list"], {"limit": 10}),
            (["list", "--limit", "5"], {"limit": 5}),
            (["search", "--from", "2026-01-01", "--to", "2026-01-31",
              "--category", "식비", "--type", "expense", "--q", "점심", "--tag", "회사"],
             {"date_from": "2026-01-01", "date_to": "2026-01-31", "category": "식비", "type": "expense", "q": "점심", "tag": "회사"}),
            (["update", "--id", "TX-000001"], {"transaction_id": "TX-000001"}),
            (["delete", "--id", "TX-000001"], {"transaction_id": "TX-000001"}),
            (["category", "add", "식비"], {"category_command": "add", "name": "식비"}),
            (["category", "list"], {"category_command": "list"}),
            (["category", "remove", "식비"], {"category_command": "remove", "name": "식비"}),
            (["budget", "set", "--month", "2026-01", "--amount", "1000"], {"budget_command": "set", "amount": 1000}),
            (["summary", "--month", "2026-01"], {"top": 3, "month": "2026-01"}),
            (["summary", "--month", "2026-01", "--top", "5"], {"top": 5}),
            (["import", "--from", "in.csv"], {"input_csv": Path("in.csv")}),
            (["export", "--out", "out.csv", "--month", "2026-01"], {"out": Path("out.csv"), "month": "2026-01"}),
            (["export", "--out", "out.csv", "--from", "2026-01-01", "--to", "2026-01-31"], {"date_from": "2026-01-01", "date_to": "2026-01-31"}),
        ]
        for argv, expected in cases:
            with self.subTest(argv=argv):
                args = parser.parse_args(argv)
                for key, value in expected.items():
                    self.assertEqual(getattr(args, key), value)

    def test_invalid_arguments_use_error_format(self) -> None:
        cases = [[], ["unknown"], ["--unknown"], ["category"], ["budget"],
                 ["update"], ["delete"], ["category", "add"], ["category", "remove"],
                 ["budget", "set"], ["summary"], ["import"], ["export"],
                 ["list", "--limit", "abc"], ["search", "--type", "other"],
                 ["summary", "--month", "2026-01", "--top", "abc"],
                 ["budget", "set", "--month", "2026-01", "--amount", "abc"],
                 ["list", "--lim", "1"]]
        for argv in cases:
            with self.subTest(argv=argv), redirect_stderr(StringIO()) as output:
                self.assertEqual(main(argv), 2)
                self.assertIn("[오류]", output.getvalue())
                self.assertIn("[힌트]", output.getvalue())
                self.assertNotIn("Traceback", output.getvalue())

    def test_pending_command_creates_no_data(self) -> None:
        with TemporaryDirectory() as temp, redirect_stderr(StringIO()) as output:
            data_dir = Path(temp) / "data"
            self.assertEqual(main(["search", "--data-dir", str(data_dir)]), 1)
            self.assertIn("아직 구현되지 않았습니다", output.getvalue())
            self.assertFalse(data_dir.exists())

    def test_main_returns_dispatch_exit_code(self) -> None:
        with patch("peach_pantry.cli.dispatch", return_value=0) as dispatch:
            self.assertEqual(main(["list"]), 0)
            self.assertEqual(dispatch.call_args.args[0].limit, 10)

    def test_process_error_exit_code(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "peach_pantry", "update"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("[오류]", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class ErrorTests(unittest.TestCase):
    """공통 데코레이터와 포맷터의 사용자 안내를 검증한다."""

    def test_expected_errors(self) -> None:
        for error, code, message in [
            (PantryError("원인", "해결", 3), 3, "원인"),
            (OSError("detail"), 1, "파일"),
            (EOFError(), 1, "입력이 종료"),
            (KeyboardInterrupt(), 130, "중단"),
        ]:
            with self.subTest(error=error), redirect_stderr(StringIO()) as output:
                @handle_errors
                def fail() -> int:
                    raise error
                self.assertEqual(fail(), code)
                self.assertIn(message, output.getvalue())
                self.assertIn("[힌트]", output.getvalue())
                self.assertNotIn("Traceback", output.getvalue())

    def test_formatter(self) -> None:
        self.assertIn("복숭아창고 (Peach Pantry)", format_title("도움말"))
        output = StringIO()
        print_error("원인", "해결", stream=output)
        self.assertEqual(output.getvalue(), "[오류] 원인\n[힌트] 해결\n")


if __name__ == "__main__":
    unittest.main()
