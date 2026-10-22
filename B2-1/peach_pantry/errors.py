"""CLI에서 공통으로 사용하는 예외와 오류 처리 데코레이터."""

from functools import wraps
from typing import Callable, ParamSpec

from .formatter import print_error

P = ParamSpec("P")


class PantryError(Exception):
    """사용자에게 안내할 원인, 해결 힌트와 종료 코드를 보관한다."""

    def __init__(self, message: str, hint: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.hint = hint
        self.exit_code = exit_code


def handle_errors(function: Callable[P, int]) -> Callable[P, int]:
    """예상 가능한 실행 오류를 안내 문구와 종료 코드로 변환한다."""
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return function(*args, **kwargs)
        except PantryError as exc:
            print_error(str(exc), exc.hint)
            return exc.exit_code
        except UnicodeError:
            print_error("입력한 문자를 UTF-8로 처리할 수 없습니다.",
                        "터미널과 입력 파일의 인코딩을 UTF-8로 확인한 뒤 다시 입력해 주세요.")
            return 1
        except OSError:
            print_error("파일을 읽거나 저장할 수 없습니다.",
                        "경로, 파일 접근 권한과 저장 공간을 확인해 주세요.")
            return 1
        except EOFError:
            print_error("입력이 종료되었습니다.", "명령을 다시 실행하여 입력해 주세요.")
            return 1
        except KeyboardInterrupt:
            print_error("사용자가 실행을 중단했습니다.", "필요하면 명령을 다시 실행해 주세요.")
            return 130
    return wrapped
