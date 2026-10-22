"""임시 디렉터리에서 JSONL 영속성과 실패 시 원본 보호를 확인한다."""

import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from peach_pantry.errors import PantryError
from peach_pantry.models import Budget, Category, Transaction
from peach_pantry.repository import (
    DEFAULT_CATEGORIES, PantryRepository, read_jsonl, replace_jsonl,
)


class RepositoryTests(unittest.TestCase):
    """실제 파일을 사용하여 저장소의 동작과 안전성을 검증한다."""

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "nested" / "data"
        self.repository = PantryRepository(self.directory)
        self.repository.initialize()

    def add_transaction(self, **changes) -> Transaction:
        values = {"date": "2026-10-22", "type": "expense", "category": "식비",
                  "amount": 12000, "memo": "점심, 복숭아", "tags": ("회사", "점심")}
        values.update(changes)
        return self.repository.add_transaction(**values)

    def test_initialize_exact_files_and_default_categories(self) -> None:
        self.assertEqual({path.name for path in self.directory.iterdir()},
                         {"transactions.jsonl", "categories.jsonl", "budgets.jsonl"})
        self.assertEqual([category.name for category in self.repository.iter_categories()],
                         list(DEFAULT_CATEGORIES))
        self.assertEqual(list(self.repository.iter_transactions()), [])
        self.assertEqual(list(self.repository.iter_budgets()), [])
        self.assertIn("식비", self.repository.categories_path.read_text(encoding="utf-8"))
        self.assertNotIn("🍚", self.repository.categories_path.read_text(encoding="utf-8"))

    def test_initialize_preserves_existing_files_including_empty_categories(self) -> None:
        self.add_transaction()
        self.repository.save_categories(())
        self.repository.save_budgets([Budget("2026-10", 100000)])
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        PantryRepository(self.directory).initialize()
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.directory.iterdir()})
        self.assertEqual(list(self.repository.iter_categories()), [])

    def test_round_trip_and_sequential_ids_after_reopening(self) -> None:
        first = self.add_transaction()
        self.repository = PantryRepository(self.directory)
        second = self.add_transaction(date="2025-01-01", memo="줄1\n줄2")
        self.assertEqual((first.id, second.id), ("TX-000001", "TX-000002"))
        self.assertEqual(list(self.repository.iter_transactions()), [first, second])
        self.assertEqual(len(self.repository.transactions_path.read_text(encoding="utf-8").splitlines()), 3)

    def test_id_is_not_reused_after_highest_or_all_transactions_removed(self) -> None:
        first = self.add_transaction()
        self.add_transaction()
        self.repository.save_transactions([first])
        self.repository = PantryRepository(self.directory)
        self.assertEqual(self.add_transaction().id, "TX-000003")
        self.repository.save_transactions(())
        self.repository = PantryRepository(self.directory)
        self.assertEqual(self.add_transaction().id, "TX-000004")

    def test_id_can_grow_beyond_six_digits(self) -> None:
        replace_jsonl(self.repository.transactions_path,
                      [{"record_type": "metadata", "last_id": 999999}])
        self.assertEqual(self.add_transaction().id, "TX-1000000")

    def test_category_and_budget_round_trip(self) -> None:
        categories = [Category("식비"), Category("여행")]
        budgets = [Budget("2026-10", 500000), Budget("2026-11", 600000)]
        self.repository.save_categories(iter(categories))
        self.repository.save_budgets(iter(budgets))
        reopened = PantryRepository(self.directory)
        self.assertEqual(list(reopened.iter_categories()), categories)
        self.assertEqual(list(reopened.iter_budgets()), budgets)

    def test_transactions_are_lazy_and_do_not_read_all_records(self) -> None:
        transaction = self.add_transaction()
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("broken JSON\n")
        transactions = self.repository.iter_transactions()
        self.assertTrue(inspect.isgenerator(transactions))
        self.assertEqual(next(transactions), transaction)
        with self.assertRaisesRegex(PantryError, "3번째"):
            next(transactions)
        transactions.close()

    def test_replace_can_consume_current_file_generator(self) -> None:
        expected = [self.add_transaction(), self.add_transaction()]
        self.repository.save_transactions(self.repository.iter_transactions())
        self.assertEqual(list(self.repository.iter_transactions()), expected)

    def test_metadata_corruption_is_not_silently_reset(self) -> None:
        for record in (None, {}, {"record_type": "metadata", "last_id": True},
                       {"record_type": "metadata", "last_id": -1}):
            with self.subTest(record=record):
                replace_jsonl(self.repository.transactions_path, [] if record is None else [record])
                before = self.repository.transactions_path.read_bytes()
                self.repository.initialize()
                with self.assertRaises(PantryError):
                    self.add_transaction()
                self.assertEqual(before, self.repository.transactions_path.read_bytes())

    def test_invalid_models_in_jsonl_are_reported(self) -> None:
        cases = [
            (self.repository.categories_path, {"name": ""}, self.repository.iter_categories),
            (self.repository.budgets_path, {"month": "2026-13", "amount": 1}, self.repository.iter_budgets),
        ]
        for path, record, reader in cases:
            with self.subTest(path=path):
                replace_jsonl(path, [record])
                with self.assertRaises(PantryError):
                    list(reader())

    def test_failed_transaction_save_preserves_data_and_id_counter(self) -> None:
        self.add_transaction()
        before = self.repository.transactions_path.read_bytes()
        with patch("peach_pantry.file_io.os.replace", side_effect=OSError("failed")):
            with self.assertRaises(OSError):
                self.add_transaction()
        self.assertEqual(before, self.repository.transactions_path.read_bytes())
        self.assertEqual(self.add_transaction().id, "TX-000002")
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_corrupt_existing_transaction_blocks_add_without_overwrite(self) -> None:
        self.add_transaction()
        with self.repository.transactions_path.open("a", encoding="utf-8") as target:
            target.write("{}\n")
        before = self.repository.transactions_path.read_bytes()
        with self.assertRaises(PantryError):
            self.add_transaction()
        self.assertEqual(before, self.repository.transactions_path.read_bytes())
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_atomic_replace_failure_stages_preserve_original_and_clean_temporary(self) -> None:
        path = self.repository.categories_path
        before = path.read_bytes()

        def broken_records():
            yield {"name": "여행"}
            raise RuntimeError("generator failed")

        for failure in ("generator", "serialization", "fsync", "replace"):
            with self.subTest(failure=failure):
                if failure == "generator":
                    with self.assertRaises(RuntimeError):
                        replace_jsonl(path, broken_records())
                elif failure == "serialization":
                    with self.assertRaises(TypeError):
                        replace_jsonl(path, [{"unsupported": object()}])
                else:
                    with patch(f"peach_pantry.file_io.os.{failure}", side_effect=OSError("failed")):
                        with self.assertRaises(OSError):
                            replace_jsonl(path, [{"name": "여행"}])
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_temporary_file_is_created_beside_destination(self) -> None:
        import os
        real_replace = os.replace

        def checked_replace(source, destination):
            self.assertEqual(Path(source).parent, Path(destination).parent)
            real_replace(source, destination)

        with patch("peach_pantry.file_io.os.replace", side_effect=checked_replace):
            self.repository.save_categories([Category("여행")])
        self.assertEqual(list(self.repository.iter_categories()), [Category("여행")])

    def test_invalid_json_and_utf8_have_actionable_errors(self) -> None:
        for content in (b"{broken}\n", b"[]\n", b"\xff\n", b"\n"):
            with self.subTest(content=content):
                self.repository.categories_path.write_bytes(content)
                with self.assertRaises(PantryError) as error:
                    list(read_jsonl(self.repository.categories_path))
                self.assertIn("categories.jsonl", str(error.exception))
                self.assertTrue(error.exception.hint)


class ModelTests(unittest.TestCase):
    """잘못된 값이 영구 저장 모델에 들어가지 않도록 검증한다."""

    def test_transaction_json_round_trip(self) -> None:
        transaction = Transaction("TX-000001", "2024-02-29", "income", "급여", 100, "메모", ("태그",))
        self.assertEqual(Transaction.from_record(json.loads(json.dumps(transaction.to_record()))), transaction)

    def test_transaction_rejects_invalid_fields(self) -> None:
        values = dict(id="TX-000001", date="2026-10-22", type="expense", category="식비", amount=1)
        invalid = [dict(id="TX-000000"), dict(id="TX-1"), dict(id="TX-0000001"),
                   dict(date="2026-02-29"), dict(date="2026-1-01"), dict(type="other"),
                   dict(category=""), dict(amount=0), dict(amount=-1), dict(amount=True),
                   dict(amount=1.5), dict(memo=None), dict(tags=["태그"]), dict(tags=(1,))]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Transaction(**(values | changes))

    def test_budget_rejects_invalid_month_and_amount(self) -> None:
        for month, amount in (("2026-13", 1), ("2026-1", 1), ("0000-01", 1),
                              ("2026-01", 0), ("2026-01", True)):
            with self.subTest(month=month, amount=amount), self.assertRaises(ValueError):
                Budget(month, amount)


if __name__ == "__main__":
    unittest.main()
