"""거래 추가와 최신 목록의 입력·출력·스트리밍 계약을 검증한다."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import weakref

from peach_pantry.cli import main
from peach_pantry.errors import PantryError
from peach_pantry.formatter import format_category, format_transaction
from peach_pantry.models import Transaction
from peach_pantry.repository import PantryRepository
from peach_pantry.service import PantryService
from peach_pantry.validators import parse_amount, parse_date, parse_tags, parse_type


class TransactionTests(unittest.TestCase):
    """사용자 데이터 대신 임시 디렉터리의 실제 JSONL 파일을 사용한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name) / "data"
        self.repository = PantryRepository(self.data_dir)
        self.repository.initialize()
        self.service = PantryService(self.repository)

    def run_cli(self, argv, inputs=()):
        stdout, stderr = StringIO(), StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--data-dir", str(self.data_dir), *argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_add_persists_all_fields_and_reports_id(self) -> None:
        code, output, errors = self.run_cli(
            ["add"], ["2024-02-29", "expense", "식비", "12000", "복숭아, 점심", "회사, 점심,, "])
        self.assertEqual(code, 0)
        self.assertEqual(errors, "")
        self.assertIn("TX-000001", output)
        expected = Transaction("TX-000001", "2024-02-29", "expense", "식비", 12000,
                               "복숭아, 점심", ("회사", "점심"))
        self.assertEqual(list(PantryRepository(self.data_dir).iter_transactions()), [expected])
        self.assertNotIn("🍚", self.repository.transactions_path.read_text(encoding="utf-8"))

    def test_invalid_fields_are_reprompted_without_extra_transactions(self) -> None:
        code, output, errors = self.run_cli(["add"], [
            "2026-02-29", "2026-1-01", "2026-10-22", "other", "income",
            "미등록", "🍚 식비", "급여", "0", "-1", "1.5", "1,000", "abc", "1000", "", "",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(errors.count("[오류]"), 10)
        self.assertIn("[힌트]", errors)
        self.assertIn("TX-000001", output)
        transactions = list(self.repository.iter_transactions())
        self.assertEqual(len(transactions), 1)
        self.assertEqual((transactions[0].type, transactions[0].amount, transactions[0].memo,
                          transactions[0].tags), ("income", 1000, "", ()))

    def test_input_end_and_interrupt_do_not_save_partial_transaction(self) -> None:
        before = self.repository.transactions_path.read_bytes()
        for error, expected_code in ((EOFError(), 1), (KeyboardInterrupt(), 130)):
            with self.subTest(error=error):
                code, output, errors = self.run_cli(["add"], ["2026-10-22", error])
                self.assertEqual(code, expected_code)
                self.assertIn("[오류]", errors)
                self.assertNotIn("저장되었습니다", output)
                self.assertEqual(self.repository.transactions_path.read_bytes(), before)

    def test_empty_categories_do_not_get_restored_or_prompt_forever(self) -> None:
        self.repository.save_categories(())
        code, _, errors = self.run_cli(["add"])
        self.assertEqual(code, 1)
        self.assertIn("카테고리가 없어", errors)
        self.assertEqual(list(self.repository.iter_categories()), [])
        self.assertEqual(list(self.repository.iter_transactions()), [])

    def test_service_rejects_invalid_fields_before_writing(self) -> None:
        valid = dict(date="2026-10-22", type="expense", category="식비", amount=1)
        before = self.repository.transactions_path.read_bytes()
        for invalid in (dict(date="2026-02-29"), dict(type="other"),
                        dict(category="미등록"), dict(amount=0), dict(amount=True)):
            with self.subTest(invalid=invalid), self.assertRaises(PantryError):
                self.service.add_transaction(**(valid | invalid))
            self.assertEqual(self.repository.transactions_path.read_bytes(), before)

    def test_default_ten_and_custom_limit_with_unordered_dates_and_ties(self) -> None:
        transactions = []
        for day in (12, 1, 10, 3, 11, 5, 9, 4, 8, 2, 7, 6, 12, 12):
            transactions.append(self.service.add_transaction(
                date=f"2026-10-{day:02d}", type="expense", category="식비", amount=day))
        expected = sorted(transactions, key=lambda tx: (tx.date, int(tx.id[3:])), reverse=True)
        self.assertEqual(self.service.list_transactions(), expected[:10])
        self.assertEqual(self.service.list_transactions(1), expected[:1])
        self.assertEqual(self.service.list_transactions(30), expected)
        code, output, errors = self.run_cli(["list"])
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(output.count("TX-"), 10)
        self.assertIn("총 10건", output)
        self.assertEqual([line.split(" | ")[1] for line in output.splitlines() if "TX-" in line],
                         [tx.id for tx in expected[:10]])
        code, output, _ = self.run_cli(["list", "--limit", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(output.count("TX-"), 2)

    def test_invalid_limits_are_errors_without_initialization(self) -> None:
        missing = Path(self.temporary.name) / "unused"
        for value in ("0", "-1", "abc", "1.5"):
            with self.subTest(value=value), redirect_stderr(StringIO()) as errors:
                self.assertEqual(main(["list", "--data-dir", str(missing), "--limit", value]), 2)
                self.assertIn("[힌트]", errors.getvalue())
                self.assertFalse(missing.exists())
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(PantryError):
                self.service.list_transactions(value)

    def test_empty_list_initializes_new_data_directory(self) -> None:
        self.data_dir = Path(self.temporary.name) / "new"
        code, output, errors = self.run_cli(["list"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("등록된 거래가 없습니다", output)
        self.assertEqual(len(list(self.data_dir.iterdir())), 3)

    def test_list_consumes_generator_with_bounded_live_transactions(self) -> None:
        references = []
        consumed = 0
        maximum_live = 0

        def transactions():
            nonlocal consumed, maximum_live
            for number in range(1, 3001):
                transaction = Transaction(f"TX-{number:06d}", "2026-10-22", "income", "급여", number)
                references[:] = [ref for ref in references if ref() is not None]
                references.append(weakref.ref(transaction))
                maximum_live = max(maximum_live, len(references))
                consumed += 1
                yield transaction

        with patch.object(self.repository, "iter_transactions", side_effect=transactions):
            result = self.service.list_transactions(7)
        self.assertEqual(consumed, 3000)
        self.assertEqual([tx.id for tx in result], [f"TX-{number:06d}" for number in range(3000, 2993, -1)])
        self.assertLessEqual(maximum_live, 10)

    def test_same_date_ids_sort_numerically_after_six_digits(self) -> None:
        transactions = [Transaction(id, "2026-10-22", "income", "급여", 1)
                        for id in ("TX-999999", "TX-1000000")]
        with patch.object(self.repository, "iter_transactions", return_value=iter(transactions)):
            self.assertEqual(self.service.list_transactions(2), transactions[::-1])

    def test_late_corruption_is_reported_instead_of_partial_success(self) -> None:
        self.service.add_transaction(date="2026-10-22", type="expense", category="식비", amount=1)
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("bad JSON\n")
        code, output, errors = self.run_cli(["list", "--limit", "1"])
        self.assertEqual(code, 1)
        self.assertIn("transactions.jsonl", errors)
        self.assertNotIn("TX-000001", output)

    def test_failed_save_reports_error_without_success_message(self) -> None:
        before = self.repository.transactions_path.read_bytes()
        with patch("peach_pantry.repository.os.replace", side_effect=OSError("failed")):
            code, output, errors = self.run_cli(
                ["add"], ["2026-10-22", "expense", "식비", "1", "", ""])
        self.assertEqual(code, 1)
        self.assertIn("[오류]", errors)
        self.assertNotIn("저장되었습니다", output)
        self.assertEqual(self.repository.transactions_path.read_bytes(), before)

    def test_real_process_add_then_list(self) -> None:
        command = [sys.executable, "-m", "peach_pantry", "--data-dir", str(self.data_dir)]
        directory = Path(__file__).resolve().parents[1]
        added = subprocess.run(command + ["add"], cwd=directory,
                               input="2026-10-22\nincome\n급여\n1000\n월급\n회사\n",
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((added.returncode, added.stderr), (0, ""))
        listed = subprocess.run(command + ["list", "--limit", "1"], cwd=directory,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((listed.returncode, listed.stderr), (0, ""))
        for text in ("TX-000001", "+1,000원", "💰 급여", "월급", "회사"):
            self.assertIn(text, listed.stdout)


class InputAndFormattingTests(unittest.TestCase):
    """입력 경계값과 이모지 출력의 저장 분리를 확인한다."""

    def test_input_validation_boundaries(self) -> None:
        self.assertEqual(parse_date(" 2024-02-29 "), "2024-02-29")
        self.assertEqual(parse_type(" expense "), "expense")
        self.assertEqual(parse_amount(" 00100 "), 100)
        self.assertEqual(parse_tags(" 회사, 점심, , "), ("회사", "점심"))
        for value in ("", "2026-1-01", "2026-04-31", "2026-10-22T00:00:00"):
            with self.subTest(value=value), self.assertRaises(PantryError):
                parse_date(value)
        for value in ("", "0", "-1", "+1", "1.1", "1,000", "１"):
            with self.subTest(value=value), self.assertRaises(PantryError):
                parse_amount(value)

    def test_formatter_signs_unknown_category_and_multiline_memo(self) -> None:
        self.assertEqual(format_category("여행"), "📦 여행")
        expense = Transaction("TX-000001", "2026-10-22", "expense", "식비", 1200, "줄1\n줄2\t끝")
        output = format_transaction(expense)
        self.assertIn("-1,200원", output)
        self.assertIn("🍚 식비", output)
        self.assertIn("줄1\\n줄2\\t끝", output)
        self.assertEqual(len(output.splitlines()), 3)
        income = Transaction("TX-000002", "2026-10-22", "income", "급여", 1000)
        self.assertIn("+1,000원", format_transaction(income))


if __name__ == "__main__":
    unittest.main()
