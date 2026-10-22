"""CSV 스키마, 날짜 필터와 실패 시 전체 취소 및 원본 보존을 검증한다."""

from contextlib import redirect_stderr, redirect_stdout
import csv
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import weakref

from peach_pantry.cli import main
from peach_pantry.csv_io import CSV_COLUMNS
from peach_pantry.errors import PantryError
from peach_pantry.models import Transaction
from peach_pantry.repository import PantryRepository
from peach_pantry.service import PantryService


class CsvTests(unittest.TestCase):
    """모든 CSV와 JSONL을 임시 디렉터리에만 저장한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.repository = PantryRepository(self.directory / "data")
        self.repository.initialize()
        self.service = PantryService(self.repository)
        self.original = self.service.add_transaction(
            date="2026-10-22", type="expense", category="식비", amount=1000,
            memo='복숭아, "점심"\n두 번째 줄', tags=("회사", "점심"),
        )
        self.input = self.directory / "input.csv"
        self.output = self.directory / "output.csv"

    def write_input(self, rows, header=CSV_COLUMNS, encoding="utf-8") -> None:
        with self.input.open("w", encoding=encoding, newline="") as target:
            writer = csv.writer(target)
            writer.writerow(header)
            writer.writerows(rows)

    def read_output(self) -> list[list[str]]:
        with self.output.open("r", encoding="utf-8", newline="") as source:
            return list(csv.reader(source))

    def snapshot(self) -> dict:
        return {path.name: path.read_bytes() for path in self.repository.data_dir.iterdir()}

    def run_cli(self, arguments):
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["--data-dir", str(self.repository.data_dir), *arguments])
        return code, output.getvalue(), errors.getvalue()

    def test_import_preserves_existing_and_assigns_new_ids_to_all_fields(self) -> None:
        self.write_input([
            ["2024-02-29", "income", "급여", "2000", '월급, "상여"\n줄바꿈', "회사, 급여"],
            ["2026-10-01", "expense", "카페", "500", "", ""],
        ], encoding="utf-8-sig")
        real_replace = os.replace
        with patch("peach_pantry.file_io.os.replace", wraps=real_replace) as replace:
            code, output, errors = self.run_cli(["import", "--from", str(self.input)])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("2건", output)
        replace.assert_called_once()
        self.assertEqual(list(PantryRepository(self.repository.data_dir).iter_transactions()), [
            self.original,
            Transaction("TX-000002", "2024-02-29", "income", "급여", 2000,
                        '월급, "상여"\n줄바꿈', ("회사", "급여")),
            Transaction("TX-000003", "2026-10-01", "expense", "카페", 500),
        ])

    def test_import_id_counter_is_preserved_after_deleting_highest_id(self) -> None:
        second = self.service.add_transaction(date="2026-10-22", type="income", category="급여", amount=1)
        self.service.delete_transaction(second.id)
        self.write_input([["2026-10-01", "expense", "카페", "1", "", ""]])
        self.assertEqual(self.service.import_csv(self.input), 1)
        self.assertEqual(list(self.repository.iter_transactions())[-1].id, "TX-000003")

    def test_bad_headers_cancel_without_changes(self) -> None:
        before = self.snapshot()
        for header in ((), CSV_COLUMNS[:-1], (*CSV_COLUMNS, "id"),
                       ("type", "date", *CSV_COLUMNS[2:]),
                       ("date", "type", "category", "amount", "memo", "memo")):
            with self.subTest(header=header):
                self.write_input([], header)
                code, output, errors = self.run_cli(["import", "--from", str(self.input)])
                self.assertEqual(code, 1)
                self.assertIn("헤더", errors)
                self.assertNotIn("완료되었습니다", output)
                self.assertEqual(self.snapshot(), before)

    def test_invalid_later_row_cancels_entire_import_and_does_not_issue_ids(self) -> None:
        valid = ["2026-10-01", "expense", "식비", "1", "정상 행", "회사,점심"]
        invalid_rows = [
            ["2026-02-29", *valid[1:]], ["2026-1-01", *valid[1:]],
            [valid[0], "other", *valid[2:]], [*valid[:2], "미등록", *valid[3:]],
            [*valid[:2], "🍚 식비", *valid[3:]],
            *[[*valid[:3], value, *valid[4:]] for value in ("0", "-1", "1.5", "abc", "1,000")],
            valid[:-1], [*valid, "추가 컬럼"], [],
            ["", *valid[1:]], [valid[0], "", *valid[2:]],
            [*valid[:2], "", *valid[3:]], [*valid[:3], "", *valid[4:]],
        ]
        before = self.snapshot()
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid):
                self.write_input([valid, invalid])
                code, output, errors = self.run_cli(["import", "--from", str(self.input)])
                self.assertEqual(code, 1)
                self.assertIn("전체 가져오기를 취소", errors)
                self.assertIn("3번째 줄", errors)
                self.assertNotIn("완료되었습니다", output)
                self.assertEqual(self.snapshot(), before)
        self.write_input([valid])
        self.assertEqual(self.service.import_csv(self.input), 1)
        self.assertEqual(list(self.repository.iter_transactions())[-1].id, "TX-000002")

    def test_malformed_csv_encoding_empty_file_and_missing_file(self) -> None:
        before = self.snapshot()
        for content in (b"", b"\xff\xfe\n",
                        b'date,type,category,amount,memo,tags\n"unterminated'):
            with self.subTest(content=content):
                self.input.write_bytes(content)
                code, output, errors = self.run_cli(["import", "--from", str(self.input)])
                self.assertEqual(code, 1)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("Traceback", errors)
                self.assertNotIn("완료되었습니다", output)
                self.assertEqual(self.snapshot(), before)
        self.input.unlink()
        code, _, errors = self.run_cli(["import", "--from", str(self.input)])
        self.assertEqual(code, 1)
        self.assertIn("[힌트]", errors)
        self.assertEqual(self.snapshot(), before)

    def test_header_only_import_is_zero_and_does_not_rewrite_data(self) -> None:
        self.write_input([])
        before = self.snapshot()
        with patch("peach_pantry.file_io.os.replace") as replace:
            self.assertEqual(self.service.import_csv(self.input), 0)
        replace.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_import_save_failures_cancel_all_and_preserve_counter(self) -> None:
        self.write_input([["2026-10-01", "income", "급여", "2", "", ""],
                          ["2026-10-02", "expense", "식비", "1", "", ""]])
        before = self.snapshot()
        for stage in ("fsync", "replace"):
            with self.subTest(stage=stage), patch(f"peach_pantry.file_io.os.{stage}", side_effect=OSError("failed")):
                code, output, errors = self.run_cli(["import", "--from", str(self.input)])
                self.assertEqual(code, 1)
                self.assertIn("[오류]", errors)
                self.assertNotIn("완료되었습니다", output)
            self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.service.import_csv(self.input), 2)
        self.assertEqual([tx.id for tx in self.repository.iter_transactions()],
                         ["TX-000001", "TX-000002", "TX-000003"])

    def test_import_does_not_overwrite_corrupt_existing_data(self) -> None:
        self.write_input([["2026-10-01", "expense", "식비", "1", "", ""]])
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("bad JSON\n")
        before = self.snapshot()
        with self.assertRaises(PantryError):
            self.service.import_csv(self.input)
        self.assertEqual(self.snapshot(), before)

    def test_export_fixed_schema_utf8_and_csv_round_trip(self) -> None:
        before = self.snapshot()
        code, output, errors = self.run_cli(["export", "--out", str(self.output), "--month", "2026-10"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("1건", output)
        self.assertEqual(self.read_output(), [list(CSV_COLUMNS),
                         ["2026-10-22", "expense", "식비", "1000", self.original.memo, "회사,점심"]])
        self.assertEqual(self.snapshot(), before)
        new_repository = PantryRepository(self.directory / "other")
        new_repository.initialize()
        self.assertEqual(PantryService(new_repository).import_csv(self.output), 1)
        self.assertEqual(list(new_repository.iter_transactions()), [self.original])

    def test_export_month_and_inclusive_ranges_with_unordered_dates(self) -> None:
        dates = ("2026-09-30", "2026-11-01", "2026-10-01", "2025-10-22", "2026-10-31")
        for date in dates:
            self.service.add_transaction(date=date, type="income", category="급여", amount=1)
        cases = [
            ({"month": "2026-10"}, ["2026-10-22", "2026-10-01", "2026-10-31"]),
            ({"date_from": "2026-10-01", "date_to": "2026-10-31"}, ["2026-10-22", "2026-10-01", "2026-10-31"]),
            ({"date_from": "2026-10-22", "date_to": "2026-10-22"}, ["2026-10-22"]),
            ({"date_from": "2026-10-31"}, ["2026-11-01", "2026-10-31"]),
            ({"date_to": "2026-09-30"}, ["2026-09-30", "2025-10-22"]),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                self.assertEqual(self.service.export_csv(self.output, **filters), len(expected))
                self.assertEqual([row[0] for row in self.read_output()[1:]], expected)

    def test_export_leap_day_and_maximum_year_month(self) -> None:
        self.service.add_transaction(date="2024-02-29", type="expense", category="식비", amount=1)
        self.service.add_transaction(date="2024-03-01", type="expense", category="식비", amount=1)
        self.assertEqual(self.service.export_csv(self.output, month="2024-02"), 1)
        self.assertEqual(self.read_output()[1][0], "2024-02-29")
        self.assertEqual(self.service.export_csv(self.output, month="9999-12"), 0)
        self.assertEqual(self.read_output(), [list(CSV_COLUMNS)])

    def test_export_rejects_missing_mixed_or_invalid_dates_without_touching_output(self) -> None:
        self.output.write_bytes(b"existing output")
        before = self.snapshot()
        for filters in ({}, {"month": "2026-10", "date_from": "2026-10-01"},
                        {"month": "2026-10", "date_to": "2026-10-31"},
                        {"month": "2026-13"}, {"date_from": "2026-02-29"},
                        {"date_from": "2026-11-01", "date_to": "2026-10-01"}):
            with self.subTest(filters=filters), self.assertRaises(PantryError):
                self.service.export_csv(self.output, **filters)
            self.assertEqual(self.output.read_bytes(), b"existing output")
            self.assertEqual(self.snapshot(), before)
        code, _, errors = self.run_cli(["export", "--out", str(self.output)])
        self.assertEqual(code, 1)
        self.assertIn("날짜 조건", errors)
        self.assertEqual(self.output.read_bytes(), b"existing output")

    def test_export_blocks_all_storage_files_and_aliases(self) -> None:
        before = self.snapshot()
        for path in (self.repository.transactions_path, self.repository.categories_path,
                     self.repository.budgets_path):
            with self.subTest(path=path), self.assertRaises(PantryError):
                self.service.export_csv(path, month="2026-10")
            self.assertEqual(self.snapshot(), before)
        for alias_type in ("symlink", "hardlink"):
            with self.subTest(alias_type=alias_type):
                alias = self.directory / f"{alias_type}.csv"
                if alias_type == "symlink":
                    alias.symlink_to(self.repository.transactions_path)
                else:
                    os.link(self.repository.transactions_path, alias)
                with self.assertRaises(PantryError):
                    self.service.export_csv(alias, month="2026-10")
                self.assertEqual(self.snapshot(), before)

    def test_export_failures_preserve_existing_output_and_remove_temporary_files(self) -> None:
        self.output.write_bytes(b"existing output")
        before = self.snapshot()
        for stage in ("fsync", "replace"):
            with self.subTest(stage=stage), patch(f"peach_pantry.file_io.os.{stage}", side_effect=OSError("failed")):
                code, output, errors = self.run_cli(["export", "--out", str(self.output), "--month", "2026-10"])
                self.assertEqual(code, 1)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("완료되었습니다", output)
            self.assertEqual(self.output.read_bytes(), b"existing output")
            self.assertEqual(list(self.directory.glob("*.tmp")), [])
            self.assertEqual(self.snapshot(), before)

    def test_export_corrupt_source_preserves_output_even_after_valid_rows(self) -> None:
        self.output.write_bytes(b"existing output")
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("bad JSON\n")
        before = self.snapshot()
        with self.assertRaises(PantryError):
            self.service.export_csv(self.output, month="2026-10")
        self.assertEqual(self.output.read_bytes(), b"existing output")
        self.assertEqual(list(self.directory.glob("*.tmp")), [])
        self.assertEqual(self.snapshot(), before)

    def test_export_missing_parent_has_clear_error_and_does_not_modify_data(self) -> None:
        before = self.snapshot()
        code, _, errors = self.run_cli(["export", "--out", str(self.directory / "missing" / "out.csv"), "--month", "2026-10"])
        self.assertEqual(code, 1)
        self.assertIn("[오류]", errors)
        self.assertNotIn("Traceback", errors)
        self.assertEqual(self.snapshot(), before)

    def test_export_streams_without_retaining_all_transactions(self) -> None:
        references = []
        peak = 0

        def transactions():
            nonlocal peak
            for number in range(1, 2001):
                transaction = Transaction(f"TX-{number:06d}", "2026-10-22", "expense", "식비", 1)
                references[:] = [reference for reference in references if reference() is not None]
                references.append(weakref.ref(transaction))
                peak = max(peak, len(references))
                yield transaction

        with patch.object(self.repository, "iter_transactions", side_effect=transactions):
            self.assertEqual(self.service.export_csv(self.output, month="2026-10"), 2000)
        self.assertEqual(len(self.read_output()), 2001)
        self.assertLessEqual(peak, 4)

    def test_real_process_import_export_and_reported_counts(self) -> None:
        self.write_input([["2026-10-01", "income", "급여", "2", "월급", "회사,급여"]])
        command = [sys.executable, "-m", "peach_pantry", "--data-dir", str(self.repository.data_dir)]
        for arguments, expected in (
            (["import", "--from", str(self.input)], "1건"),
            (["export", "--out", str(self.output), "--from", "2026-10-01", "--to", "2026-10-31"], "2건"),
        ):
            with self.subTest(arguments=arguments):
                result = subprocess.run(command + arguments, cwd=Path(__file__).resolve().parents[1],
                                        capture_output=True, text=True, encoding="utf-8")
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertIn(expected, result.stdout)
        self.assertEqual(len(self.read_output()), 3)


if __name__ == "__main__":
    unittest.main()
