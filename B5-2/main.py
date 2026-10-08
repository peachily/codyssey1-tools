import shlex

from commit import Commit
from mini_git import MiniGit


def format_commits(commits: list[Commit]) -> str:
    return "\n".join(
        f"{commit.hash} | {commit.author} | {commit.timestamp.isoformat()} | {commit.message}"
        for commit in commits
    ) or "No commits"


def execute(repository: MiniGit, line: str) -> str | None:
    """명령 파싱·검증·실행. 종료 명령은 None 반환."""
    try:
        tokens = shlex.split(line)
    except ValueError:
        raise ValueError("Invalid args") from None
    if not tokens:
        return ""
    command, *args = tokens
    command = command.upper()
    if command in {"EXIT", "QUIT"}:
        if args:
            raise ValueError("Invalid args")
        return None
    if command not in {"INIT", "BRANCH", "SWITCH", "COMMIT", "LOG", "PATH", "ANCESTORS", "SEARCH"}:
        raise ValueError(f"Unknown command: {command}")
    if command == "LOG":
        if not args:
            return format_commits(repository.log())
        if len(args) != 1 or args[0] not in {"--sort-by=date", "--sort-by=author"}:
            raise ValueError("Invalid args")
        return format_commits(repository.log(args[0].split("=", 1)[1]))
    expected = 2 if command == "PATH" else 1
    if len(args) != expected or any(not arg.strip() for arg in args):
        raise ValueError("Invalid args")
    value = args[0]
    if command == "INIT":
        repository.init(value)
        return f"Initialized main | user: {value}"
    if command == "BRANCH":
        repository.branch(value)
        return f"Created branch: {value}"
    if command == "SWITCH":
        repository.switch(value)
        return f"Switched to: {value}"
    if command == "COMMIT":
        return format_commits([repository.commit(value)])
    if command == "ANCESTORS":
        return "\n".join(repository.ancestors(value)) or "No ancestors"
    if command == "PATH":
        return " -> ".join(repository.path(*args)) or "No path"
    by_author = value.startswith("--author=")
    if value.startswith("--") and not by_author:
        raise ValueError("Invalid args")
    if by_author:
        value = value.split("=", 1)[1]
    results = repository.search(value, by_author)
    return format_commits(results) if results else "No results"


def main() -> None:
    """입력 오류에서 복구하는 Mini Git REPL."""
    repository = MiniGit()
    while True:
        try:
            line = input("mini-git> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        try:
            result = execute(repository, line)
            if result is None:
                break
            if result:
                print(result)
        except ValueError as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
