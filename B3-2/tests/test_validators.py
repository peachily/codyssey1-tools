import unittest

from validators import ValidationError, validate_commit, validate_pr

VALID_PR = "파일 읽기 오류 처리\n\n## Why\n- 오류 안내가 필요해요.\n\n## What\n- 오류 처리를 추가해요.\n\n## How to Test\n- 없는 파일을 지정하고 오류 안내를 확인하세요."


class ValidatorTests(unittest.TestCase):
    def test_commit_title_boundary(self):
        self.assertTrue(validate_commit("가" * 72 + "\n\n- 변경 요약").startswith("가" * 72))
        with self.assertRaises(ValidationError):
            validate_commit("가" * 73 + "\n\n- 변경 요약")

    def test_commit_requires_title_and_body(self):
        for text in ["", "feat: 기능 추가", "- 제목 없음\n- 요약", "제목\n설명만 있어요."]:
            with self.subTest(text=text), self.assertRaises(ValidationError):
                validate_commit(text)

    def test_commit_summary_by_changed_filename(self):
        text = "fix: 파일 읽기 수정\n\ngit_utils.py의 파일 읽기 오류를 처리해요."
        self.assertEqual(validate_commit(text, ["git_utils.py"]), text)

    def test_commit_too_many_bullets(self):
        with self.assertRaises(ValidationError):
            validate_commit("제목\n- 하나\n- 둘\n- 셋")

    def test_harmless_formatting_is_normalized(self):
        self.assertEqual(
            validate_commit("```markdown\r\n제목: docs: 안내 수정\r\n\r\n* 실행 방법 정리\r\n```"),
            "docs: 안내 수정\n\n- 실행 방법 정리",
        )

    def test_pr_valid(self):
        self.assertEqual(validate_pr(VALID_PR), VALID_PR)

    def test_pr_title_length(self):
        body = VALID_PR[VALID_PR.index("\n"):]
        validate_pr("가" * 80 + body)
        with self.assertRaises(ValidationError):
            validate_pr("가" * 81 + body)

    def test_every_section_required(self):
        for section in ["Why", "What", "How to Test"]:
            with self.subTest(section=section), self.assertRaises(ValidationError):
                validate_pr(VALID_PR.replace("## " + section, "### " + section))

    def test_every_section_requires_nonempty_bullet(self):
        for content in ["오류 안내가 필요해요.", "오류 처리를 추가해요.", "없는 파일을 지정하고 오류 안내를 확인하세요."]:
            with self.subTest(content=content), self.assertRaises(ValidationError):
                validate_pr(VALID_PR.replace("- " + content, "- \n내용만 있어요."))

    def test_pr_duplicate_header_and_multiline_title(self):
        for text in [VALID_PR + "\n## Why\n- 추가", VALID_PR.replace("\n\n## Why", "\n두 번째 제목\n\n## Why")]:
            with self.subTest(text=text), self.assertRaises(ValidationError):
                validate_pr(text)


if __name__ == "__main__":
    unittest.main()
