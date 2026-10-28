"""CLI에서 공통으로 사용하는 예외와 오류 처리 데코레이터."""

from functools import wraps
from typing import Callable, ParamSpec

from .formatter import print_error

P = ParamSpec("P")
# ParamSpec: 함수가 받는 매개변수의 타입 정보를 그대로 가져와서 다른 함수에도 적용할 수 있게 해주는 Python 타입 힌트
#  → 인자들의 타입 정보를 표현하기 위한 도구.. 공통 오류 처리 데코레이터를 구현하면서, 원래 함수의 매개변수 형태가 유지되도록 사용함.
# 함수의 매개변수 타입 정보를 담을 변수 P

class PantryError(Exception):
    """사용자에게 안내할 원인, 해결 힌트와 종료 코드를 보관한다."""

    def __init__(self, message: str, hint: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.hint = hint
        self.exit_code = exit_code


def handle_errors(function: Callable[P, int]) -> Callable[P, int]:
    """예상 가능한 실행 오류를 안내 문구와 종료 코드로 변환한다."""
    # Callable[P, int]: P에 해당하는 매개변수를 받고 정수를 반환하는 함수
    # -> Callable[P, int]: 매개변수 형태와 반환 타입이 같은 함수를 돌려준다는 뜻
    # ( 데코레이터를 적용한 후에도 어떤 인자를 받는지 타입 검사 도구가 알 수 있도록 해줌 )
    @wraps(function)
    # 공통 오류 처리 함수를 감싸는 데코레이터. 명령어마다 동일한 오류 처리 코드를 반복하지 않아도 됨.
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> int:
        # *args: 위치 인자들을 받음 / **kwargs: 키워드 인자들을 받음 → 실제로 인자를 전달하기 위한 문법
        # P.args, P.kwargs: 원래 함수의 매개변수 타입 정보를 유지하도록 표시
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
