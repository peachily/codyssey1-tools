import argparse
import math
import re
import sys

from ai_client import APIError, generate_text
from config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, get_api_key, model_parameters
from git_utils import GitError, check_repository, collect_changes
from prompts import build_messages
from safe_mode import mask_sensitive_data
from validators import ValidationError, validate_commit, validate_pr


class KoreanParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, "[ERROR] 명령이나 옵션 값이 올바르지 않아요.\n"
                  "commit 또는 pr을 선택하고 옵션 범위를 확인해 주세요.\n"
                  "--temperature: 0~2, --max-tokens: 1~128000, --model: 공백 없는 모델 이름\n"
                  "--safe-mode와 --no-safe-mode는 함께 쓸 수 없어요. --help로 사용법을 확인해 주세요.\n")


def parse_temperature(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 2:
        raise argparse.ArgumentTypeError("temperature는 0~2 사이의 숫자여야 해요.")
    return number


def parse_tokens(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 128000:
        raise argparse.ArgumentTypeError("max-tokens는 1~128000 사이의 정수여야 해요.")
    return number


def parse_model(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", value):
        raise argparse.ArgumentTypeError("공백 없는 모델 이름을 입력해 주세요.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = KoreanParser(description="Giteuk: Git 변경사항으로 커밋 메시지와 PR 초안을 만들어요.", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="사용법을 표시하고 종료")
    parser.add_argument("command", choices=["commit", "pr"], help="commit: 커밋 메시지 / pr: PR 초안")
    parser.add_argument("--model", type=parse_model, default=DEFAULT_MODEL, help="AI 모델 (기본: %(default)s)")
    parser.add_argument("--temperature", type=parse_temperature, default=DEFAULT_TEMPERATURE, help="0~2 (기본: %(default)s, 추론 모델은 생략)")
    parser.add_argument("--max-tokens", type=parse_tokens, default=DEFAULT_MAX_TOKENS, help="1~128000 (기본: %(default)s, 모델별 실제 한도는 다를 수 있어요)")
    safety = parser.add_mutually_exclusive_group()
    safety.add_argument("--safe-mode", dest="safe_mode", action="store_true", help="민감정보 마스킹 및 비밀 파일 제외 (기본)")
    safety.add_argument("--no-safe-mode", dest="safe_mode", action="store_false", help="민감정보 보호 없이 전송")
    parser.set_defaults(safe_mode=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    calls = 0
    try:
        root = check_repository()
        if not args.safe_mode:
            print("[INFO] 안전 모드가 꺼져 있어요. 비밀번호와 비밀 파일이 AI로 전송될 수 있어요.")
        print("[INFO] 변경 내용을 읽고 있어요.")
        filenames, diff, excluded = collect_changes(root, args.safe_mode)
        if excluded:
            print(f"[INFO] 민감한 파일 {excluded}개를 전송 대상에서 제외했어요.")
        if not filenames:
            print("[INFO] AI로 보낼 변경사항이 없어요.")
            return 0
        print(f"[INFO] 변경된 파일을 {len(filenames)}개 찾았어요.")
        api_key = get_api_key()
        if args.safe_mode:
            filenames = [mask_sensitive_data(name, api_key) for name in filenames]
            diff = mask_sensitive_data(diff, api_key)
        messages = build_messages(args.command, filenames, diff)
        if "temperature" not in model_parameters(args.model, args.temperature, args.max_tokens):
            print("[INFO] 선택한 추론 모델에는 temperature를 보내지 않아요.")
        label = "커밋 메시지" if args.command == "commit" else "PR 초안"
        object_name = "커밋 메시지를" if args.command == "commit" else "PR 초안을"
        print(f"[INFO] AI가 {object_name} 작성하고 있어요.")
        calls = 1
        result = generate_text(api_key, messages, args.model, args.temperature, args.max_tokens)
        result = mask_sensitive_data(result, api_key)
        visible_filenames = [mask_sensitive_data(name, api_key) for name in filenames]
        result = validate_commit(result, visible_filenames) if args.command == "commit" else validate_pr(result)
        print(f"[DONE] {object_name} 만들었어요.")
        print(f"\n--- {label} ---\n{result}\n--- 결과 끝 ---")
        return 0
    except ValidationError as error:
        print(f"[ERROR] 생성 결과의 형식 검증에 실패했어요. {error}\nAI를 자동으로 다시 호출하지 않았어요.", file=sys.stderr)
        return 1
    except (GitError, APIError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] 작업을 중단했어요.", file=sys.stderr)
        return 130
    finally:
        print(f"[INFO] API 호출 횟수: {calls}")


if __name__ == "__main__":
    sys.exit(main())
