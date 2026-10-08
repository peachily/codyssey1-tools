import io
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from commit import Commit
from graph import ancestors, shortest_path, topological_order
from index import InvertedIndex
from main import execute, main
from mini_git import MiniGit
from sorting import merge_sort


TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_graph(parent_lists):
    return {
        commit_hash: Commit(commit_hash, "message", "peachily", TIME, parents)
        for commit_hash, parents in parent_lists.items()
    }


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repo = MiniGit()
        self.repo.init("peachily")

    def test_init_has_empty_main(self):
        self.assertEqual(self.repo.branches, {"main": None})
        self.assertEqual(self.repo.current_branch, "main")
        self.assertEqual(self.repo.user, "peachily")
        self.assertEqual(self.repo.log(), [])

    def test_commands_before_init(self):
        for line in ["BRANCH dev", "SWITCH main", "COMMIT hi", "LOG",
                     "LOG --sort-by=date", "PATH a b", "ANCESTORS a",
                     "SEARCH hi", "SEARCH --author=peachily"]:
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, "Repository not initialized"):
                execute(MiniGit(), line)

    def test_reinit_clears_state_and_preserves_session_unique_ids(self):
        old = self.repo.commit("old")
        self.repo.branch("dev")
        self.repo.init("peachily new")
        self.assertEqual(self.repo.commits, {})
        self.assertEqual(self.repo.branches, {"main": None})
        self.assertEqual(self.repo.current_branch, "main")
        self.assertEqual(self.repo.index.keywords, {})
        self.assertEqual(self.repo.index.authors, {})
        new = self.repo.commit("new")
        self.assertNotEqual(new.hash, old.hash)
        self.assertEqual(new.parents, [])
        self.assertEqual(new.author, "peachily new")

    def test_empty_head_branch_and_disconnected_roots(self):
        self.repo.branch("empty")
        first = self.repo.commit("main root")
        self.repo.switch("empty")
        second = self.repo.commit("other root")
        self.assertEqual(second.parents, [])
        self.assertEqual(self.repo.path(first.hash, second.hash), [])

    def test_branch_errors(self):
        with self.assertRaisesRegex(ValueError, "Branch already exists: main"):
            self.repo.branch("main")
        with self.assertRaisesRegex(ValueError, "Unknown branch: missing"):
            self.repo.switch("missing")

    def test_first_and_sequential_commits(self):
        first = self.repo.commit("first")
        second = self.repo.commit("second")
        self.assertEqual(first.hash, "000001")
        self.assertEqual(first.parents, [])
        self.assertEqual(second.parents, [first.hash])
        self.assertEqual(second.author, "peachily")
        self.assertIsNotNone(second.timestamp.tzinfo)
        self.assertEqual(self.repo.branches["main"], second.hash)

    def test_branch_fork_preserves_parents(self):
        root = self.repo.commit("root")
        self.repo.branch("dev")
        main_commit = self.repo.commit("main work")
        self.repo.switch("dev")
        self.assertEqual(len(self.repo.commits), 2)
        dev_commit = self.repo.commit("dev work")
        self.assertEqual(main_commit.parents, [root.hash])
        self.assertEqual(dev_commit.parents, [root.hash])
        self.assertEqual(root.parents, [])
        self.assertEqual(self.repo.branches["main"], main_commit.hash)
        self.assertEqual({commit.hash for commit in self.repo.log()}, set(self.repo.commits))
        for commit in self.repo.commits.values():
            self.assertTrue(all(parent < commit.hash for parent in commit.parents))
        self.assertEqual(self.repo.path(main_commit.hash, dev_commit.hash),
                         [main_commit.hash, root.hash, dev_commit.hash])

    def test_hash_uniqueness_and_fixed_width(self):
        hashes = [self.repo.commit(str(i)).hash for i in range(120)]
        self.assertEqual(len(set(hashes)), 120)
        self.assertTrue(all(len(commit_hash) == 6 for commit_hash in hashes))

    def test_id_limit_does_not_modify_repository(self):
        self.repo._counter = 999999
        with self.assertRaisesRegex(ValueError, "Commit ID limit reached"):
            self.repo.commit("overflow")
        self.assertEqual(self.repo.commits, {})
        self.assertEqual(self.repo.branches["main"], None)

    def test_blank_input_does_not_modify_state(self):
        for action in [self.repo.init, self.repo.commit, self.repo.branch, self.repo.switch]:
            with self.subTest(action=action.__name__), self.assertRaisesRegex(ValueError, "Invalid args"):
                action("  ")
        self.assertEqual(self.repo.user, "peachily")
        self.assertEqual(self.repo.commits, {})

    def test_unknown_commits(self):
        commit = self.repo.commit("one")
        for action in [lambda: self.repo.ancestors("bad"),
                       lambda: self.repo.path("bad", commit.hash),
                       lambda: self.repo.path(commit.hash, "bad")]:
            with self.assertRaisesRegex(ValueError, "Unknown commit: bad"):
                action()


class GraphTests(unittest.TestCase):
    def setUp(self):
        # 삽입 순서와 부모 순서 역전, 다중 부모 DAG
        self.graph = make_graph({
            "000006": ["000004", "000005"],
            "000005": ["000003"],
            "000004": ["000003", "000002"],
            "000003": ["000001"],
            "000002": ["000001"],
            "000001": [],
            "000007": [],
        })

    def test_topological_order_parent_first_and_deterministic(self):
        result = topological_order(self.graph)
        self.assertEqual(set(result), set(self.graph))
        positions = {commit_hash: i for i, commit_hash in enumerate(result)}
        for commit in self.graph.values():
            for parent in commit.parents:
                self.assertLess(positions[parent], positions[commit.hash])
        reversed_graph = dict(reversed(list(self.graph.items())))
        self.assertEqual(result, topological_order(reversed_graph))

    def test_topological_cycle_detection(self):
        graph = make_graph({"000001": ["000002"], "000002": ["000001"]})
        with self.assertRaisesRegex(ValueError, "Cycle detected"):
            topological_order(graph)

    def test_ancestors_distance_hash_order_and_deduplication(self):
        self.assertEqual(ancestors(self.graph, "000006"),
                         ["000004", "000005", "000002", "000003", "000001"])
        self.assertEqual(ancestors(self.graph, "000001"), [])

    def test_path_undirected_and_lexicographic_tie(self):
        self.assertEqual(shortest_path(self.graph, "000001", "000006"),
                         ["000001", "000002", "000004", "000006"])
        self.assertEqual(shortest_path(self.graph, "000006", "000001"),
                         ["000006", "000004", "000002", "000001"])

    def test_path_later_lexicographic_difference(self):
        graph = make_graph({
            "000001": [], "000002": ["000001"],
            "000004": ["000002"], "000003": ["000002"],
            "000005": ["000004", "000003"],
        })
        self.assertEqual(shortest_path(graph, "000001", "000005"),
                         ["000001", "000002", "000003", "000005"])

    def test_path_shortest_distance_precedes_lexicographic_order(self):
        graph = make_graph({
            "000001": [], "000002": ["000001"], "000003": ["000002"],
            "000004": ["000001"], "000005": ["000003", "000004"],
        })
        self.assertEqual(shortest_path(graph, "000001", "000005"),
                         ["000001", "000004", "000005"])

    def test_path_same_commit_and_disconnected(self):
        self.assertEqual(shortest_path(self.graph, "000002", "000002"), ["000002"])
        self.assertEqual(shortest_path(self.graph, "000001", "000007"), [])


class SearchAndSortingTests(unittest.TestCase):
    def setUp(self):
        self.repo = MiniGit()
        self.repo.init("peachily")

    def test_indexes_update_normalize_and_deduplicate(self):
        first = self.repo.commit("Hello HELLO hello, world")
        second = self.repo.commit("hello again")
        self.assertEqual(self.repo.index.keywords["hello"], [first.hash, second.hash])
        self.assertEqual(self.repo.index.keywords["hello,"], [first.hash])
        self.assertEqual(self.repo.index.authors["peachily"], [first.hash, second.hash])
        self.assertEqual(self.repo.search("HELLO"), [first, second])
        self.assertEqual(self.repo.search("peachily", True), [first, second])
        self.assertEqual(self.repo.search("PEACHILY", True), [])
        self.assertEqual(self.repo.search("absent"), [])

    def test_search_uses_index_without_full_scan(self):
        commit = self.repo.commit("target")

        class LookupOnly(dict):
            def __iter__(self):
                raise AssertionError("Full scan")

            def values(self):
                raise AssertionError("Full scan")

            def items(self):
                raise AssertionError("Full scan")

        self.repo.commits = LookupOnly(self.repo.commits)
        self.assertEqual(self.repo.search("target"), [commit])
        self.assertEqual(self.repo.search("peachily", True), [commit])

    def test_multiple_authors_index(self):
        index = InvertedIndex()
        for number, author in enumerate(["peachily-b", "peachily-a", "peachily-b"], 1):
            index.add(Commit(f"{number:06d}", "word", author, TIME, []))
        self.assertEqual(index.search_author("peachily-b"), ["000001", "000003"])

    def test_date_author_sort_ties_and_original_preservation(self):
        a, b, c = [self.repo.commit(message) for message in ["a", "b", "c"]]
        a.timestamp = TIME + timedelta(days=1)
        b.timestamp = c.timestamp = TIME
        a.author, b.author, c.author = "peachily-z", "peachily-a", "peachily-a"
        self.repo.commits = {c.hash: c, a.hash: a, b.hash: b}
        before = list(self.repo.commits.items())
        self.assertEqual(self.repo.log("date"), [b, c, a])
        self.assertEqual(self.repo.log("author"), [b, c, a])
        self.assertEqual(self.repo.log(), [a, b, c])
        self.assertEqual(list(self.repo.commits.items()), before)
        with self.assertRaisesRegex(ValueError, "Invalid args"):
            self.repo.log("unknown")

    def test_merge_sort_stability_and_original_preservation(self):
        values = [(2, "a"), (1, "b"), (2, "c"), (1, "d"), (2, "e")]
        original = values[:]
        self.assertEqual(merge_sort(values, key=lambda value: value[0]),
                         [(1, "b"), (1, "d"), (2, "a"), (2, "c"), (2, "e")])
        self.assertEqual(values, original)
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(merge_sort([1]), [1])
        self.assertEqual(merge_sort([3, -1, 2, 0, -1]), [-1, -1, 0, 2, 3])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.repo = MiniGit()

    def test_case_and_quoted_arguments(self):
        execute(self.repo, 'iNiT "peachily test"')
        execute(self.repo, 'bRaNcH "feature one"')
        execute(self.repo, 'sWiTcH "feature one"')
        result = execute(self.repo, 'cOmMiT "Hello World"')
        self.assertIn("peachily test", result)
        self.assertIn("Hello World", result)
        self.assertIn("000001", execute(self.repo, 'sEaRcH --author="peachily test"'))
        self.assertIn("000001", execute(self.repo, "SEARCH HELLO"))

    def test_invalid_arguments_and_options(self):
        execute(self.repo, "INIT peachily")
        for line in ["INIT", "INIT a b", 'INIT ""', "BRANCH", "SWITCH a b",
                     "COMMIT hello world", 'COMMIT " "', 'COMMIT "unfinished',
                     "LOG --sort-by=bad", "LOG --sort-by date", "LOG extra",
                     "LOG --sort-by=date --sort-by=author", "ANCESTORS", "PATH a",
                     "PATH a b c", "SEARCH", "SEARCH a b", "SEARCH --author=",
                     'SEARCH --author=" "', "SEARCH --bad=peachily", "exit extra", "quit extra"]:
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, "Invalid args"):
                execute(self.repo, line)

    def test_unknown_command_empty_line_and_exit(self):
        with self.assertRaisesRegex(ValueError, "Unknown command: MISSING"):
            execute(self.repo, "missing")
        self.assertEqual(execute(self.repo, "  "), "")
        self.assertIsNone(execute(self.repo, "EXIT"))
        self.assertIsNone(execute(self.repo, "QuIt"))

    def test_all_output_commands_and_empty_results(self):
        execute(self.repo, "INIT peachily")
        self.assertEqual(execute(self.repo, "LOG"), "No commits")
        execute(self.repo, "BRANCH isolated")
        execute(self.repo, 'COMMIT "first message"')
        execute(self.repo, 'COMMIT "second message"')
        for line in ["LOG", "LOG --sort-by=date", "LOG --sort-by=author"]:
            result = execute(self.repo, line)
            self.assertIn("000001 | peachily |", result)
            self.assertIn("second message", result)
        self.assertEqual(execute(self.repo, "ANCESTORS 000002"), "000001")
        self.assertEqual(execute(self.repo, "ANCESTORS 000001"), "No ancestors")
        self.assertEqual(execute(self.repo, "PATH 000002 000001"), "000002 -> 000001")
        self.assertEqual(execute(self.repo, "SEARCH missing"), "No results")
        execute(self.repo, "SWITCH isolated")
        execute(self.repo, "COMMIT root")
        self.assertEqual(execute(self.repo, "PATH 000001 000003"), "No path")

    def test_repl_recovers_after_error(self):
        lines = ["COMMIT early", "INIT peachily", 'COMMIT "unterminated', "COMMIT works", "quit"]
        with patch("builtins.input", side_effect=lines) as read, patch("sys.stdout", new_callable=io.StringIO) as output:
            main()
        self.assertIn("Error: Repository not initialized", output.getvalue())
        self.assertIn("Error: Invalid args", output.getvalue())
        self.assertIn("works", output.getvalue())
        read.assert_called_with("mini-git> ")

    def test_repl_handles_eof_and_interrupt(self):
        for exception in [EOFError, KeyboardInterrupt]:
            with patch("builtins.input", side_effect=exception), patch("sys.stdout", new_callable=io.StringIO):
                main()


if __name__ == "__main__":
    unittest.main()
