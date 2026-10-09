import json
import os
import subprocess
from pathlib import Path

from safe_mode import is_sensitive_file


class GitError(Exception):
    pass


def run_git(arguments: list[str], cwd: Path) -> str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_LITERAL_PATHSPECS"] = "1"
    environment["LC_ALL"] = "C"
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=cwd, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, check=False,
        )
    except FileNotFoundError:
        raise GitError("Git을 실행하지 못했어요. Git 설치와 실행 폴더를 확인해 주세요.") from None
    except subprocess.TimeoutExpired:
        raise GitError("Git 작업 시간이 너무 길어요. 저장소 상태를 확인한 뒤 다시 실행해 주세요.") from None
    except OSError:
        raise GitError("Git을 실행할 수 없어요. 폴더 접근 권한을 확인해 주세요.") from None
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace")
        if "not a git repository" in error:
            raise GitError("Git 저장소를 찾지 못했어요.\nGit이 설정된 프로젝트 폴더에서 다시 실행해 주세요.")
        if "dubious ownership" in error:
            raise GitError("Git이 저장소 소유자를 신뢰하지 않아요. 폴더 소유자와 Git 설정을 확인해 주세요.")
        if "Permission denied" in error:
            raise GitError("Git 파일을 읽을 권한이 없어요. 저장소 접근 권한을 확인해 주세요.")
        raise GitError(
            f"Git {arguments[0]} 작업에 실패했어요 (종료 코드 {result.returncode}).\n"
            "터미널에서 git status로 저장소 상태와 설정을 확인해 주세요."
        )
    return os.fsdecode(result.stdout)


def check_repository(cwd: Path | None = None) -> Path:
    current = (cwd or Path.cwd()).resolve()
    root_text = run_git(["rev-parse", "--show-toplevel"], current).rstrip("\n")
    root = Path(root_text).resolve()
    if current != root:
        raise GitError("프로젝트의 Git 최상위 폴더에서 실행해 주세요.\ngit rev-parse --show-toplevel로 위치를 확인할 수 있어요.")
    return root


def read_status(root: Path) -> tuple[bool, list[tuple[str, str | None, bool]]]:
    output = run_git(["status", "--porcelain=v2", "--branch", "-z", "--untracked-files=all"], root)
    initial = "# branch.oid (initial)\0" in output
    records = iter(output.split("\0"))
    files = []
    for record in records:
        if not record or record.startswith("# "):
            continue
        if record.startswith("u "):
            raise GitError("아직 해결하지 않은 Git 충돌이 있어요. 충돌을 해결한 뒤 다시 실행해 주세요.")
        if record.startswith("? "):
            files.append((record[2:], None, True))
        elif record.startswith("1 "):
            files.append((record.split(" ", 8)[8], None, False))
        elif record.startswith("2 "):
            files.append((record.split(" ", 9)[9], next(records), False))
    return initial, files


def new_file_diff(root: Path, filename: str) -> str:
    file = root / filename
    label = json.dumps(filename, ensure_ascii=False)
    try:
        if file.is_symlink():
            return f"신규 심볼릭 링크 {label} (대상 파일 내용은 읽지 않음)"
        if not file.exists():
            return ""
        if not file.is_file():
            return f"신규 경로 {label} (일반 파일 아님)"
        content = file.read_bytes()
    except OSError:
        raise GitError("새 파일을 읽지 못했어요. 파일의 존재 여부와 읽기 권한을 확인해 주세요.") from None
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return f"신규 파일 {label} (바이너리 또는 UTF-8이 아닌 파일, 내용 생략)"
    if "\0" in text:
        return f"신규 바이너리 파일 {label} (내용 생략)"
    lines = "\n".join("+" + line for line in text.splitlines())
    return f"신규 파일 {label}\n--- /dev/null\n+++ {label}\n{lines}"


def collect_changes(root: Path, safe_mode: bool = True) -> tuple[list[str], str, int]:
    initial, entries = read_status(root)
    filenames, patches = [], []
    excluded = 0
    for filename, original, untracked in entries:
        paths = [filename] + ([original] if original else [])
        if safe_mode and any(is_sensitive_file(path) for path in paths):
            excluded += 1
            continue
        if initial or untracked:
            patch = new_file_diff(root, filename)
        else:
            # HEAD와 현재 작업 파일 비교: 스테이징 전후 변경을 한 번만 포함
            patch = run_git([
                "diff", "--no-ext-diff", "--no-textconv", "--no-color",
                "--no-renames", "--submodule=short", "HEAD", "--", *paths,
            ], root)
        if patch:
            filenames.append(filename)
            patches.append(patch)
    return filenames, "\n\n".join(patches), excluded
