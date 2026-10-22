"""월별 집계, 지출 순위, 예산 경계값과 CLI 출력을 검증한다."""

from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
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
from peach_pantry.models import Transaction
from peach_pantry.repository import PantryRepository
from peach_pantry.service import PantryService


class SummaryTests(unittest.TestCase):
    """임시 JSONL 파일에 서로 다른 달의 거래를 섞어서 저장한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name) / "data"
        self.repository = PantryRepository(self.data_dir)
        self.repository.initialize()
        self.service = PantryService(self.repository)

    def populate(self) -> None:
        for date, type, category, amount in (
            ("2026-10-31", "expense", "식비", 1000),
            ("2026-09-30", "expense", "식비", 90000),
            ("2026-10-01", "income", "급여", 5000),
            ("2026-11-01", "income", "급여", 80000),
            ("2026-10-22", "expense", "카페", 500),
            ("2026-10-01", "expense", "식비", 500),
            ("2025-10-22", "expense", "쇼핑", 70000),
            ("2026-10-15", "expense", "교통", 1000),
            ("2026-10-02", "income", "용돈", 1000),
            ("2026-10-20", "expense", "쇼핑", 500),
        ):
            self.service.add_transaction(date=date, type=type, category=category, amount=amount)

    def run_cli(self, month="2026-10", extra=()):
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["summary", "--data-dir", str(self.data_dir), "--month", month, *extra])
        return code, output.getvalue(), errors.getvalue()

    def snapshot(self) -> dict:
        return {path.name: path.read_bytes() for path in self.data_dir.iterdir()}

    def test_totals_include_month_boundaries_and_exclude_other_months_and_years(self) -> None:
        self.populate()
        before = self.snapshot()
        summary = self.service.summary("2026-10")
        self.assertEqual((summary.income, summary.expense, summary.balance, summary.transaction_count),
                         (6000, 3500, 2500, 7))
        self.assertIsNone(summary.budget)
        self.assertIsNone(summary.budget_usage)
        self.assertFalse(summary.budget_exceeded)
        self.assertEqual(self.snapshot(), before)

    def test_top_default_custom_large_and_tie_order(self) -> None:
        self.populate()
        expected = (("식비", 1500), ("교통", 1000), ("쇼핑", 500), ("카페", 500))
        self.assertEqual(self.service.summary("2026-10").top_expenses, expected[:3])
        self.assertEqual(self.service.summary("2026-10", 1).top_expenses, expected[:1])
        self.assertEqual(self.service.summary("2026-10", 100).top_expenses, expected)
        code, output, errors = self.run_cli(extra=["--top", "2"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("카테고리별 지출 TOP 2", output)
        self.assertIn("1. 🍚 식비 | 1,500원", output)
        self.assertIn("2. 🚌 교통 | 1,000원", output)
        self.assertNotIn("🛍️ 쇼핑", output)
        self.assertNotIn("☕ 카페", output)

    def test_cli_totals_default_top_and_no_budget_fields_when_unset(self) -> None:
        self.populate()
        code, output, errors = self.run_cli()
        self.assertEqual((code, errors), (0, ""))
        for expected in ("2026-10 월별 요약", "총수입: +6,000원", "총지출: -3,500원",
                         "잔액: +2,500원", "TOP 3"):
            self.assertIn(expected, output)
        self.assertNotIn("월 예산:", output)
        self.assertNotIn("예산 사용률:", output)
        self.assertNotIn("[경고]", output)

    def test_income_only_has_no_expense_ranking(self) -> None:
        self.service.add_transaction(date="2026-10-01", type="income", category="급여", amount=100)
        self.service.set_budget("2026-10", 1000)
        summary = self.service.summary("2026-10")
        self.assertEqual((summary.income, summary.expense, summary.balance, summary.top_expenses),
                         (100, 0, 100, ()))
        code, output, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("해당 월의 지출이 없습니다", output)
        self.assertNotIn("등록된 거래가 없습니다", output)
        self.assertIn("예산 사용률: 0.0%", output)

    def test_expense_only_has_negative_balance(self) -> None:
        self.service.add_transaction(date="2026-10-01", type="expense", category="식비", amount=100)
        self.assertEqual(self.service.summary("2026-10").balance, -100)
        code, output, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("잔액: -100원", output)

    def test_empty_month_with_and_without_budget(self) -> None:
        self.populate()
        for with_budget in (False, True):
            with self.subTest(with_budget=with_budget):
                if with_budget:
                    self.service.set_budget("2026-12", 1000)
                summary = self.service.summary("2026-12")
                self.assertEqual((summary.income, summary.expense, summary.balance,
                                  summary.transaction_count, summary.top_expenses), (0, 0, 0, 0, ()))
                code, output, errors = self.run_cli("2026-12")
                self.assertEqual((code, errors), (0, ""))
                self.assertIn("해당 월에 등록된 거래가 없습니다", output)
                self.assertNotIn("[경고]", output)
                if with_budget:
                    self.assertIn("월 예산: 1,000원", output)
                    self.assertIn("예산 사용률: 0.0%", output)
                else:
                    self.assertNotIn("예산 사용률:", output)

    def test_budget_usage_and_warning_below_equal_above(self) -> None:
        self.populate()
        self.service.set_budget("2026-11", 1)
        for amount, usage, exceeded in ((10000, Decimal("35"), False),
                                         (3500, Decimal("100"), False),
                                         (1750, Decimal("200"), True)):
            with self.subTest(amount=amount):
                self.service.set_budget("2026-10", amount)
                summary = self.service.summary("2026-10")
                self.assertEqual(summary.budget, amount)
                self.assertEqual(summary.budget_usage, usage)
                self.assertEqual(summary.budget_exceeded, exceeded)
                code, output, errors = self.run_cli()
                self.assertEqual((code, errors), (0, ""))
                self.assertIn(f"예산 사용률: {usage:.1f}%", output)
                self.assertEqual("[경고]" in output, exceeded)
                if exceeded:
                    self.assertIn("1,750원 초과", output)

    def test_warning_uses_exact_amount_despite_rounded_percentage(self) -> None:
        self.service.set_budget("2026-10", 100000)
        transaction = self.service.add_transaction(date="2026-10-22", type="expense", category="식비", amount=99999)
        code, output, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("100.0%", output)
        self.assertNotIn("[경고]", output)
        self.service.update_transaction(transaction.id, amount=100001)
        code, output, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("100.0%", output)
        self.assertIn("[경고] 월 예산을 1원 초과", output)

    def test_invalid_month_and_top_do_not_change_files(self) -> None:
        before = self.snapshot()
        for month, extra in (("2026-13", []), ("2026-1", []), ("0000-01", []),
                             ("2026-10", ["--top", "0"]), ("2026-10", ["--top", "-1"]),
                             ("2026-10", ["--top", "abc"])):
            with self.subTest(month=month, extra=extra):
                code, _, errors = self.run_cli(month, extra)
                self.assertNotEqual(code, 0)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("Traceback", errors)
                self.assertEqual(self.snapshot(), before)
        for top in (True, 1.5):
            with self.subTest(top=top), self.assertRaises(PantryError):
                self.service.summary("2026-10", top)

    def test_corrupted_transaction_or_budget_is_reported_without_partial_summary(self) -> None:
        for name in ("transactions.jsonl", "budgets.jsonl"):
            with self.subTest(name=name), TemporaryDirectory() as temporary:
                self.data_dir = Path(temporary)
                repository = PantryRepository(self.data_dir)
                repository.initialize()
                with (self.data_dir / name).open("a", encoding="utf-8") as target:
                    target.write("bad JSON\n")
                before = self.snapshot()
                code, output, errors = self.run_cli()
                self.assertEqual(code, 1)
                self.assertIn(name, errors)
                self.assertNotIn("총수입:", output)
                self.assertEqual(self.snapshot(), before)

    def test_summary_streams_once_without_retaining_transactions(self) -> None:
        references = []
        peak = 0
        consumed = 0

        def transactions():
            nonlocal peak, consumed
            for number in range(1, 3001):
                transaction = Transaction(f"TX-{number:06d}", "2026-10-22", "expense", "식비", 1)
                references[:] = [reference for reference in references if reference() is not None]
                references.append(weakref.ref(transaction))
                peak = max(peak, len(references))
                consumed += 1
                yield transaction

        with patch.object(self.repository, "iter_transactions", side_effect=transactions) as read:
            summary = self.service.summary("2026-10")
        read.assert_called_once()
        self.assertEqual(consumed, 3000)
        self.assertEqual((summary.expense, summary.transaction_count, summary.top_expenses),
                         (3000, 3000, (("식비", 3000),)))
        self.assertLessEqual(peak, 3)

    def test_real_process_reads_persisted_budget_and_transactions(self) -> None:
        self.populate()
        self.service.set_budget("2026-10", 1000)
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, "-m", "peach_pantry", "summary", "--month", "2026-10",
             "--top", "1", "--data-dir", str(self.data_dir)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertIn("총수입: +6,000원", result.stdout)
        self.assertIn("잔액: +2,500원", result.stdout)
        self.assertIn("예산 사용률: 350.0%", result.stdout)
        self.assertIn("[경고]", result.stdout)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
