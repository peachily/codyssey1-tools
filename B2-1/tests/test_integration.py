"""모킹 없이 별도 Python 프로세스로 전체 CLI 흐름을 검증한다."""

import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

PROJECT_DIR = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    """기본 ./data도 사용자 폴더가 아닌 임시 작업 폴더에서 생성한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.environment = dict(os.environ, PYTHONPATH=str(PROJECT_DIR), PYTHONIOENCODING="utf-8")

    def run_cli(self, arguments: list[str], input_text: str | None = None,
                expected_code: int = 0) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, "-m", "peach_pantry", *arguments],
            cwd=self.directory, env=self.environment, input=input_text,
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(result.returncode, expected_code, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if expected_code == 0:
            self.assertEqual(result.stderr, "")
        else:
            self.assertIn("[오류]", result.stderr)
            self.assertIn("[힌트]", result.stderr)
        return result

    def snapshot(self) -> dict:
        return {path.name: path.read_bytes() for path in (self.directory / "data").iterdir()}

    def test_complete_workflow_and_reimport_in_separate_data_directory(self) -> None:
        self.assertIn("총 12개", self.run_cli(["category", "list"]).stdout)
        self.run_cli(["category", "add", "여행"])
        self.run_cli(["add"], "2026-10-01\nincome\n급여\n50000\n급여\n회사\n")
        self.run_cli(["add"], "2026-10-22\nexpense\n식비\n12000\n점심\n회사,점심\n")
        self.run_cli(["add"], "2026-09-30\nexpense\n여행\n5000\n지난달 여행\n\n")
        listing = self.run_cli(["list", "--limit", "2"]).stdout
        self.assertLess(listing.index("TX-000002"), listing.index("TX-000001"))
        self.assertNotIn("TX-000003", listing)
        before = self.snapshot()
        self.run_cli(["category", "remove", "식비"], expected_code=1)
        self.assertEqual(self.snapshot(), before)

        self.run_cli(["update", "--id", "TX-000002"], "\n\n\n15000\n수정 점심\n회사,점심\n")
        search = self.run_cli(["search", "--from", "2026-10-01", "--to", "2026-10-31",
                               "--category", "식비", "--type", "expense", "--q", "수정", "--tag", "회사"])
        self.assertEqual(search.stdout.count("TX-"), 1)
        self.assertIn("TX-000002", search.stdout)
        self.run_cli(["budget", "set", "--month", "2026-10", "--amount", "10000"])
        summary = self.run_cli(["summary", "--month", "2026-10", "--top", "1"]).stdout
        for text in ("총수입: +50,000원", "총지출: -15,000원", "잔액: +35,000원", "150.0%", "[경고]"):
            self.assertIn(text, summary)

        self.assertIn("2건", self.run_cli(["export", "--out", "october.csv", "--month", "2026-10"]).stdout)
        with (self.directory / "october.csv").open(encoding="utf-8", newline="") as source:
            self.assertEqual(len(list(csv.reader(source))), 3)
        self.assertIn("2건", self.run_cli(["--data-dir", "copied", "import", "--from", "october.csv"]).stdout)
        copied = self.run_cli(["summary", "--month", "2026-10", "--data-dir", "copied"]).stdout
        self.assertIn("잔액: +35,000원", copied)
        self.assertNotIn("월 예산:", copied)

        self.run_cli(["delete", "--id", "TX-000003"])
        self.run_cli(["category", "remove", "여행"])
        added = self.run_cli(["add"], "2026-10-22\nexpense\n교통\n1000\n\n\n")
        self.assertIn("TX-000004", added.stdout)
        records = [json.loads(line) for line in (self.directory / "data" / "transactions.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records[0], {"record_type": "metadata", "last_id": 4})
        self.assertEqual([record["id"] for record in records[1:]], ["TX-000001", "TX-000002", "TX-000004"])
        self.assertEqual(set(self.snapshot()), {"transactions.jsonl", "categories.jsonl", "budgets.jsonl"})

    def test_failures_preserve_data_across_restarted_processes(self) -> None:
        self.run_cli(["add"], "2026-10-22\nexpense\n식비\n1000\n점심\n회사\n")
        before = self.snapshot()
        (self.directory / "bad.csv").write_text(
            "date,type,category,amount,memo,tags\n"
            "2026-10-22,expense,식비,1000,정상,회사\n"
            "2026-02-29,expense,식비,1000,잘못된 날짜,회사\n", encoding="utf-8",
        )
        self.run_cli(["import", "--from", "bad.csv"], expected_code=1)
        self.run_cli(["update", "--id", "TX-999999"], expected_code=1)
        self.run_cli(["delete", "--id", "TX-999999"], expected_code=1)
        self.run_cli(["category", "add", "식비"], expected_code=1)
        self.run_cli(["budget", "set", "--month", "2026-13", "--amount", "1000"], expected_code=1)
        self.run_cli(["summary", "--month", "2026-10", "--top", "0"], expected_code=2)
        self.run_cli(["export", "--out", "all.csv"], expected_code=1)
        self.run_cli(["export", "--out", "data/transactions.jsonl", "--month", "2026-10"], expected_code=1)
        self.assertFalse((self.directory / "all.csv").exists())
        self.assertEqual(self.snapshot(), before)
        self.assertIn("TX-000002", self.run_cli(["add"], "2026-10-22\nincome\n급여\n2000\n\n\n").stdout)

    def test_korean_help_and_parser_diagnostics_do_not_create_data(self) -> None:
        self.assertIn("사용법:", self.run_cli(["--help"]).stdout)
        for arguments in (["unknown"], ["update"], ["list", "--unknown"],
                          ["list", "--limit"], ["list", "--limit", "abc"],
                          ["search", "--type", "other"]):
            with self.subTest(arguments=arguments):
                result = self.run_cli(arguments, expected_code=2)
                for text in ("unrecognized arguments", "invalid choice", "invalid int value",
                             "the following arguments", "expected one argument"):
                    self.assertNotIn(text, result.stderr)
        self.assertFalse((self.directory / "data").exists())


if __name__ == "__main__":
    unittest.main()
