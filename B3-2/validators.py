import re


class ValidationError(Exception):
    pass


def normalize_output(text: str) -> str:
    text = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    if len(lines) >= 2 and re.fullmatch(r"```(?:markdown|md|text)?", lines[0]) and lines[-1] == "```":
        lines = lines[1:-1]
    lines = [line.rstrip() for line in lines]
    return "\n".join(re.sub(r"^[ \t]*[*•][ \t]+", "- ", line) for line in lines).strip()


def split_title(text: str, limit: int) -> tuple[str, str]:
    title, _, body = normalize_output(text).partition("\n")
    title = re.sub(r"^(?:#\s+|(?:PR 제목|제목|Title):\s*)", "", title).strip()
    if not title or title.startswith(("#", "- ", "```")):
        raise ValidationError("제목 한 줄이 필요해요.")
    if len(title) > limit:
        raise ValidationError(f"제목이 {limit}자를 넘었어요. 내용을 확인하고 제목을 줄여 주세요.")
    if any(ord(character) < 32 for character in title):
        raise ValidationError("제목에 줄바꿈이나 제어 문자를 넣을 수 없어요.")
    if not body.strip():
        raise ValidationError("변경 내용을 설명하는 본문이 필요해요.")
    return title, body.strip()


def validate_commit(text: str, filenames: list[str] | None = None) -> str:
    title, body = split_title(text, 72)
    bullets = re.findall(r"^[ \t]*-[ \t]+\S.*$", body, flags=re.MULTILINE)
    mentioned = sum(filename in body for filename in (filenames or []))
    if not 1 <= len(bullets) <= 2 and not 1 <= mentioned <= 3:
        raise ValidationError("본문에 핵심 변경사항 불릿 1~2개 또는 변경 파일 1~3개가 필요해요.")
    return f"{title}\n\n{body}"


def validate_pr(text: str) -> str:
    title, body = split_title(text, 80)
    headers = list(re.finditer(r"^##[ \t]+(.+?)[ \t]*$", body, flags=re.MULTILINE))
    expected = ["Why", "What", "How to Test"]
    if [match[1] for match in headers] != expected:
        raise ValidationError("PR 본문에 ## Why, ## What, ## How to Test 섹션이 순서대로 필요해요.")
    if body[:headers[0].start()].strip():
        raise ValidationError("PR 제목은 한 줄로 쓰고 본문은 ## Why로 시작해 주세요.")
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(body)
        section = body[header.end():end]
        if not re.search(r"^[ \t]*-[ \t]+\S.*$", section, flags=re.MULTILINE):
            raise ValidationError(f"{expected[index]} 섹션에 내용이 있는 불릿이 최소 1개 필요해요.")
    return f"{title}\n\n{body}"
