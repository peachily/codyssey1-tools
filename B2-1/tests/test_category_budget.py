"""카테고리와 예산 관리의 검증·영속성·파일 안전성을 확인한다."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from peach_pantry.cli import main
from peach_pantry.errors import PantryError
from peach_pantry.models import Budget, Transaction
from peach_pantry.repository import DEFAULT_CATEGORIES, PantryRepository
from peach_pantry.service import PantryService


class CategoryBudgetTests(unittest.TestCase):
    """실제 사용자 파일에 접근하지 않고 저장과 재실행을 검증한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name) / "data"
        self.repository = PantryRepository(self.data_dir)
        self.repository.initialize()
        self.service = PantryService(self.repository)

    def run_cli(self, arguments):
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["--data-dir", str(self.data_dir), *arguments])
        return code, output.getvalue(), errors.getvalue()

    def snapshot(self) -> dict:
        return {path.name: path.read_bytes() for path in self.data_dir.iterdir()}

    def test_category_list_includes_defaults_and_does_not_modify_files(self) -> None:
        before = self.snapshot()
        code, output, errors = self.run_cli(["category", "list"])
        self.assertEqual((code, errors), (0, ""))
        for name in DEFAULT_CATEGORIES:
            self.assertIn(name, output)
        self.assertIn("🍚 식비", output)
        self.assertIn("총 12개", output)
        self.assertEqual(self.snapshot(), before)

    def test_add_category_persists_trimmed_name_without_emoji(self) -> None:
        code, output, errors = self.run_cli(["category", "add", "  가족 여행  "])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("📦 가족 여행", output)
        reopened = PantryRepository(self.data_dir)
        reopened.initialize()
        self.assertIn("가족 여행", PantryService(reopened).category_names())
        text = reopened.categories_path.read_text(encoding="utf-8")
        self.assertNotIn("📦", text)
        self.assertIn("가족 여행", text)
        transaction = PantryService(reopened).add_transaction(
            date="2026-10-22", type="expense", category="가족 여행", amount=100)
        self.assertEqual(transaction.category, "가족 여행")

    def test_duplicate_categories_including_whitespace_are_rejected(self) -> None:
        self.service.add_category("여행")
        before = self.snapshot()
        for name in ("식비", " 여행 "):
            with self.subTest(name=name):
                code, output, errors = self.run_cli(["category", "add", name])
                self.assertEqual(code, 1)
                self.assertIn("이미 등록", errors)
                self.assertNotIn("등록되었습니다", output)
                self.assertEqual(self.snapshot(), before)

    def test_invalid_category_names_are_rejected_without_writes(self) -> None:
        before = self.snapshot()
        for name in ("", "   ", "🍚 식비", "여행\n가족", "travel"):
            with self.subTest(name=name):
                code, _, errors = self.run_cli(["category", "add", name])
                self.assertEqual(code, 1)
                self.assertIn("[힌트]", errors)
                self.assertEqual(self.snapshot(), before)

    def test_remove_unused_category_and_missing_name(self) -> None:
        code, output, errors = self.run_cli(["category", "remove", " 교육 "])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("삭제되었습니다", output)
        self.assertNotIn("교육", self.service.category_names())
        before = self.snapshot()
        code, _, errors = self.run_cli(["category", "remove", "교육"])
        self.assertEqual(code, 1)
        self.assertIn("찾을 수 없습니다", errors)
        self.assertEqual(self.snapshot(), before)

    def test_used_income_and_expense_categories_cannot_be_removed(self) -> None:
        for type, category in (("income", "급여"), ("expense", "식비")):
            self.service.add_transaction(date="2026-10-22", type=type, category=category, amount=1)
        before = self.snapshot()
        for category in ("급여", "식비"):
            with self.subTest(category=category):
                code, output, errors = self.run_cli(["category", "remove", category])
                self.assertEqual(code, 1)
                self.assertIn("사용 중", errors)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("삭제되었습니다", output)
                self.assertEqual(self.snapshot(), before)

    def test_category_can_be_removed_after_reassignment_or_transaction_deletion(self) -> None:
        first = self.service.add_transaction(date="2026-10-22", type="expense", category="식비", amount=1)
        second = self.service.add_transaction(date="2026-10-22", type="income", category="급여", amount=1)
        self.service.update_transaction(first.id, category="기타")
        self.service.remove_category("식비")
        self.service.delete_transaction(second.id)
        self.service.remove_category("급여")
        self.assertNotIn("식비", self.service.category_names())
        self.assertNotIn("급여", self.service.category_names())
        self.assertEqual(self.service.get_transaction(first.id).category, "기타")

    def test_deleting_all_categories_stays_empty_after_reinitialization(self) -> None:
        for name in DEFAULT_CATEGORIES:
            self.service.remove_category(name)
        reopened = PantryRepository(self.data_dir)
        reopened.initialize()
        self.assertEqual(list(reopened.iter_categories()), [])
        code, output, errors = self.run_cli(["category", "list"])
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("등록된 카테고리가 없습니다", output)

    def test_category_usage_check_streams_and_closes_file(self) -> None:
        closed = []

        def transactions():
            try:
                yield Transaction("TX-000001", "2026-10-22", "expense", "식비", 1)
                self.fail("사용 중임을 확인하면 추가 거래를 읽을 필요가 없습니다.")
            finally:
                closed.append(True)

        with patch.object(self.repository, "iter_transactions", side_effect=transactions):
            with self.assertRaisesRegex(PantryError, "사용 중"):
                self.service.remove_category("식비")
        self.assertEqual(closed, [True])

    def test_corrupted_transactions_block_category_removal(self) -> None:
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("broken JSON\n")
        before = self.snapshot()
        code, _, errors = self.run_cli(["category", "remove", "식비"])
        self.assertEqual(code, 1)
        self.assertIn("transactions.jsonl", errors)
        self.assertEqual(self.snapshot(), before)

    def test_budget_set_and_reset_preserve_other_month_and_one_entry_per_month(self) -> None:
        for month, amount in (("2026-10", 100000), ("2026-11", 200000), ("2026-10", 300000)):
            code, output, errors = self.run_cli(["budget", "set", "--month", month, "--amount", str(amount)])
            self.assertEqual((code, errors), (0, ""))
            self.assertIn(month, output)
            self.assertIn(f"{amount:,}원", output)
        reopened = PantryRepository(self.data_dir)
        reopened.initialize()
        budgets = list(reopened.iter_budgets())
        self.assertEqual(len(budgets), 2)
        self.assertEqual({budget.month: budget.amount for budget in budgets},
                         {"2026-10": 300000, "2026-11": 200000})

    def test_budget_rejects_invalid_months_and_amounts_without_writes(self) -> None:
        self.service.set_budget("2026-10", 100000)
        before = self.snapshot()
        cases = [(month, "1000") for month in ("", "2026-1", "2026-00", "2026-13", "0000-01", "2026-10-01")]
        cases += [("2026-10", amount) for amount in ("0", "-1", "1.5", "abc")]
        for month, amount in cases:
            with self.subTest(month=month, amount=amount):
                code, output, errors = self.run_cli(["budget", "set", "--month", month, "--amount", amount])
                self.assertNotEqual(code, 0)
                self.assertIn("[힌트]", errors)
                self.assertNotIn("저장되었습니다", output)
                self.assertEqual(self.snapshot(), before)
        for amount in (True, 1.5):
            with self.subTest(amount=amount), self.assertRaises(PantryError):
                self.service.set_budget("2026-10", amount)
        self.assertEqual(self.snapshot(), before)

    def test_budget_valid_month_boundaries_and_trimmed_input(self) -> None:
        self.assertEqual(self.service.set_budget(" 2024-02 ", 1), Budget("2024-02", 1))
        self.assertEqual(self.service.set_budget("0001-01", 1), Budget("0001-01", 1))
        self.assertEqual(self.service.set_budget("9999-12", 1), Budget("9999-12", 1))

    def test_save_failures_preserve_category_and_budget_files(self) -> None:
        self.service.set_budget("2026-10", 1000)
        before = self.snapshot()
        commands = [
            ["category", "add", "여행"],
            ["category", "remove", "식비"],
            ["budget", "set", "--month", "2026-10", "--amount", "2000"],
        ]
        for command in commands:
            for stage in ("fsync", "replace"):
                with self.subTest(command=command, stage=stage):
                    with patch(f"peach_pantry.repository.os.{stage}", side_effect=OSError("failed")):
                        code, output, errors = self.run_cli(command)
                    self.assertEqual(code, 1)
                    self.assertIn("[오류]", errors)
                    self.assertNotIn("되었습니다", output)
                    self.assertEqual(self.snapshot(), before)

    def test_corrupted_management_files_are_not_overwritten(self) -> None:
        for path, command in (
            (self.repository.categories_path, ["category", "add", "여행"]),
            (self.repository.budgets_path, ["budget", "set", "--month", "2026-10", "--amount", "1"]),
        ):
            with self.subTest(path=path):
                path.write_text("broken JSON\n", encoding="utf-8")
                before = self.snapshot()
                code, _, errors = self.run_cli(command)
                self.assertEqual(code, 1)
                self.assertIn(path.name, errors)
                self.assertEqual(self.snapshot(), before)

    def test_real_process_category_and_budget_persistence(self) -> None:
        directory = Path(__file__).resolve().parents[1]
        cases = [
            (["category", "add", "여행"], "📦 여행"),
            (["category", "list"], "📦 여행"),
            (["category", "remove", "여행"], "삭제되었습니다"),
            (["budget", "set", "--month", "2026-10", "--amount", "1000"], "1,000원"),
            (["budget", "set", "--month", "2026-10", "--amount", "2000"], "2,000원"),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    [sys.executable, "-m", "peach_pantry", *arguments, "--data-dir", str(self.data_dir)],
                    cwd=directory, capture_output=True, text=True, encoding="utf-8",
                )
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertIn(expected, result.stdout)
        reopened = PantryRepository(self.data_dir)
        self.assertNotIn("여행", PantryService(reopened).category_names())
        self.assertEqual(list(reopened.iter_budgets()), [Budget("2026-10", 2000)])


if __name__ == "__main__":
    unittest.main()
