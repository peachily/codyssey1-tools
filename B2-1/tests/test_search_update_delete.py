"""검색 조건, 거래 수정·삭제와 실패 시 파일 안전성을 검증한다."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import weakref

from peach_pantry.cli import main
from peach_pantry.errors import PantryError
from peach_pantry.models import Transaction
from peach_pantry.repository import PantryRepository
from peach_pantry.service import PantryService
from peach_pantry.sorting import latest_first


class SearchUpdateDeleteTests(unittest.TestCase):
    """실제 JSONL 파일을 임시 디렉터리 안에서만 생성한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name) / "data"
        self.repository = PantryRepository(self.data_dir)
        self.repository.initialize()
        self.service = PantryService(self.repository)
        values = [
            ("2026-10-22", "expense", "식비", "회사 점심", ("회사", "점심")),
            ("2026-10-01", "income", "급여", "회사 월급", ("회사",)),
            ("2026-11-01", "expense", "식비", "회사 저녁", ("회사",)),
            ("2026-10-22", "expense", "카페", "회사 점심 커피", ("회사", "점심")),
            ("2026-10-22", "expense", "식비", "회사 점심", ("회사생활",)),
            ("2026-09-30", "expense", "식비", "저녁", ()),
        ]
        self.transactions = [self.service.add_transaction(
            date=date, type=type, category=category, amount=1000, memo=memo, tags=tags,
        ) for date, type, category, memo, tags in values]

    def run_cli(self, argv, inputs=()):
        stdout, stderr = StringIO(), StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--data-dir", str(self.data_dir), *argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def assert_files_unchanged(self, before: dict) -> None:
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.data_dir.iterdir()})

    def snapshot(self) -> dict:
        return {path.name: path.read_bytes() for path in self.data_dir.iterdir()}

    def test_each_search_filter(self) -> None:
        cases = [
            ({"date_from": "2026-11-01"}, [3]),
            ({"date_to": "2026-10-01"}, [2, 6]),
            ({"date_from": "2026-10-22", "date_to": "2026-10-22"}, [5, 4, 1]),
            ({"category": "카페"}, [4]),
            ({"type": "income"}, [2]),
            ({"q": "점심"}, [5, 4, 1]),
            ({"tag": "회사"}, [3, 4, 1, 2]),
            ({"tag": "회"}, []),
            ({"q": "없는 메모"}, []),
        ]
        before = self.snapshot()
        for filters, ids in cases:
            with self.subTest(filters=filters):
                result = list(self.service.search_transactions(**filters))
                self.assertEqual([tx.id for tx in result], [f"TX-{id:06d}" for id in ids])
        self.assert_files_unchanged(before)

    def test_all_filters_are_combined_with_and(self) -> None:
        filters = dict(date_from="2026-10-01", date_to="2026-10-31", category="식비",
                       type="expense", q="점심", tag="회사")
        self.assertEqual(list(self.service.search_transactions(**filters)), [self.transactions[0]])
        code, output, errors = self.run_cli([
            "search", "--from", "2026-10-01", "--to", "2026-10-31", "--category", "식비",
            "--type", "expense", "--q", "점심", "--tag", "회사",
        ])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("검색 결과", output)
        self.assertEqual(output.count("TX-"), 1)
        self.assertIn("TX-000001", output)

    def test_search_without_filters_sorts_all_and_empty_result_has_message(self) -> None:
        self.assertEqual([tx.id for tx in self.service.search_transactions()],
                         ["TX-000003", "TX-000005", "TX-000004", "TX-000001", "TX-000002", "TX-000006"])
        code, output, errors = self.run_cli(["search", "--q", "결과없음"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("검색 조건에 맞는 거래가 없습니다", output)

    def test_invalid_search_conditions_have_hints_and_preserve_files(self) -> None:
        before = self.snapshot()
        for arguments in (["--from", "2026-02-29"], ["--to", "2026-1-01"],
                          ["--from", "2026-11-01", "--to", "2026-10-01"],
                          ["--category", "미등록"], ["--type", "other"]):
            with self.subTest(arguments=arguments):
                code, _, errors = self.run_cli(["search", *arguments])
                self.assertNotEqual(code, 0)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("Traceback", errors)
                self.assert_files_unchanged(before)

    def test_update_all_fields_persists_same_id_and_preserves_other_records(self) -> None:
        updated = self.service.update_transaction(
            "TX-000001", date="2024-02-29", type="income", category="급여", amount=5000,
            memo="수정한 메모", tags=("수정",),
        )
        expected = Transaction("TX-000001", "2024-02-29", "income", "급여", 5000, "수정한 메모", ("수정",))
        self.assertEqual(updated, expected)
        self.assertEqual(list(PantryRepository(self.data_dir).iter_transactions()),
                         [expected, *self.transactions[1:]])
        next_transaction = self.service.add_transaction(date="2026-10-22", type="income", category="급여", amount=1)
        self.assertEqual(next_transaction.id, "TX-000007")

    def test_update_enter_preserves_every_field(self) -> None:
        before = self.snapshot()
        code, output, errors = self.run_cli(["update", "--id", "TX-000001"], [""] * 6)
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("수정되었습니다", output)
        self.assert_files_unchanged(before)

    def test_update_reprompts_invalid_fields_and_keeps_blank_fields(self) -> None:
        code, output, errors = self.run_cli(["update", "--id", "TX-000001"], [
            "bad date", "2024-02-29", "other", "income", "미등록", "급여",
            "-1", "5000", "", "새 태그, 다른 태그",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(errors.count("[오류]"), 4)
        self.assertIn("수정되었습니다", output)
        self.assertEqual(self.service.get_transaction("TX-000001"),
                         Transaction("TX-000001", "2024-02-29", "income", "급여", 5000,
                                     "회사 점심", ("새 태그", "다른 태그")))

    def test_update_can_clear_optional_fields_through_service(self) -> None:
        result = self.service.update_transaction("TX-000001", memo="", tags=())
        self.assertEqual((result.memo, result.tags), ("", ()))

    def test_update_validation_failure_and_input_cancellation_preserve_files(self) -> None:
        before = self.snapshot()
        for invalid in (dict(date="2026-02-29"), dict(type="other"), dict(category="미등록"),
                        dict(amount=0), dict(tags=(1,)), dict(memo=3)):
            with self.subTest(invalid=invalid), self.assertRaises(PantryError):
                self.service.update_transaction("TX-000001", **invalid)
            self.assert_files_unchanged(before)
        for error, expected in ((EOFError(), 1), (KeyboardInterrupt(), 130)):
            with self.subTest(error=error):
                code, output, errors = self.run_cli(["update", "--id", "TX-000001"], ["", error])
                self.assertEqual(code, expected)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("수정되었습니다", output)
                self.assert_files_unchanged(before)

    def test_missing_and_malformed_ids_do_not_prompt_or_change_files(self) -> None:
        before = self.snapshot()
        for command in ("update", "delete"):
            for id in ("TX-999999", "bad-id"):
                with self.subTest(command=command, id=id):
                    code, output, errors = self.run_cli([command, "--id", id])
                    self.assertEqual(code, 1)
                    self.assertIn("[힌트]", errors)
                    self.assertNotIn("되었습니다", output)
                    self.assert_files_unchanged(before)

    def test_delete_only_target_and_preserve_id_high_water_mark(self) -> None:
        code, output, errors = self.run_cli(["delete", "--id", "TX-000006"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("삭제되었습니다", output)
        self.assertEqual(list(self.repository.iter_transactions()), self.transactions[:-1])
        for transaction in self.transactions[:-1]:
            self.service.delete_transaction(transaction.id)
        self.assertEqual(list(self.repository.iter_transactions()), [])
        reopened = PantryService(PantryRepository(self.data_dir))
        self.assertEqual(reopened.add_transaction(date="2026-10-22", type="income",
                                                 category="급여", amount=1).id, "TX-000007")

    def test_update_delete_replace_and_fsync_failures_preserve_original(self) -> None:
        before = self.snapshot()
        for command in ("update", "delete"):
            for stage in ("replace", "fsync"):
                with self.subTest(command=command, stage=stage):
                    with patch(f"peach_pantry.file_io.os.{stage}", side_effect=OSError("failed")):
                        inputs = ["", "", "", "2000", "", ""] if command == "update" else []
                        code, output, errors = self.run_cli([command, "--id", "TX-000001"], inputs)
                    self.assertEqual(code, 1)
                    self.assertIn("[오류]", errors)
                    self.assertNotIn("되었습니다", output)
                    self.assert_files_unchanged(before)

    def test_late_corruption_blocks_update_delete_and_search_without_overwrite(self) -> None:
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("bad JSON\n")
        before = self.snapshot()
        for command in ("update", "delete", "search"):
            with self.subTest(command=command):
                args = [command] if command == "search" else [command, "--id", "TX-000001"]
                code, output, errors = self.run_cli(args, ["", "", "", "2000", "", ""])
                self.assertEqual(code, 1)
                self.assertIn("transactions.jsonl", errors)
                self.assertNotIn("되었습니다", output)
                self.assert_files_unchanged(before)

    def test_real_process_update_search_and_delete(self) -> None:
        prefix = [sys.executable, "-m", "peach_pantry", "--data-dir", str(self.data_dir)]
        directory = Path(__file__).resolve().parents[1]
        cases = [
            (["update", "--id", "TX-000001"], "\n\n\n1500\n새 메모\n새태그\n", "수정되었습니다"),
            (["search", "--q", "새 메모", "--tag", "새태그"], None, "-1,500원"),
            (["delete", "--id", "TX-000001"], None, "삭제되었습니다"),
        ]
        for arguments, input, expected in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run(prefix + arguments, cwd=directory, input=input,
                                        capture_output=True, text=True, encoding="utf-8")
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertIn(expected, result.stdout)


class DiskSortingTests(unittest.TestCase):
    """검색의 스트리밍과 임시 디스크 정리 수명주기를 확인한다."""

    def test_search_generator_does_not_hold_all_transactions(self) -> None:
        references = []
        peak = 0
        consumed = 0

        def records():
            nonlocal peak, consumed
            for number in range(1, 2001):
                transaction = Transaction(f"TX-{number:06d}", "2026-10-22", "income", "급여", 1)
                references[:] = [reference for reference in references if reference() is not None]
                references.append(weakref.ref(transaction))
                peak = max(peak, len(references))
                consumed += 1
                yield transaction

        with TemporaryDirectory() as temporary:
            repository = PantryRepository(temporary)
            with patch.object(repository, "iter_transactions", side_effect=records):
                results = PantryService(repository).search_transactions(q="")
                self.assertEqual(consumed, 0)
                for expected, transaction in zip(range(2000, 0, -1), results):
                    self.assertEqual(transaction.id, f"TX-{expected:06d}")
                results.close()
        self.assertEqual(consumed, 2000)
        self.assertLessEqual(peak, 4)

    def test_numeric_ids_with_more_than_six_digits(self) -> None:
        transactions = [Transaction(id, "2026-10-22", "income", "급여", 1)
                        for id in ("TX-999999", "TX-1000000")]
        self.assertEqual(list(latest_first(iter(transactions))), transactions[::-1])

    def test_temporary_directory_cleaned_on_success_early_close_and_failure(self) -> None:
        for mode in ("success", "early_close", "source_failure", "sqlite_failure"):
            with self.subTest(mode=mode), TemporaryDirectory() as parent:
                def directory_factory(**kwargs):
                    return TemporaryDirectory(dir=parent, **kwargs)

                def records():
                    yield Transaction("TX-000001", "2026-10-22", "income", "급여", 1)
                    if mode == "source_failure":
                        raise PantryError("원본 손상", "백업 확인")
                    yield Transaction("TX-000002", "2026-10-22", "income", "급여", 1)

                with patch("peach_pantry.sorting.TemporaryDirectory", side_effect=directory_factory):
                    results = latest_first(records())
                    if mode == "sqlite_failure":
                        with patch("peach_pantry.sorting.sqlite3.connect", side_effect=sqlite3.OperationalError("full")):
                            with self.assertRaises(PantryError):
                                list(results)
                    elif mode == "source_failure":
                        with self.assertRaises(PantryError):
                            list(results)
                    elif mode == "early_close":
                        next(results)
                        self.assertTrue(list(Path(parent).iterdir()))
                        results.close()
                    else:
                        self.assertEqual(len(list(results)), 2)
                self.assertEqual(list(Path(parent).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
