import shlex
import sys

from mini_redis import MiniRedis


def wrong_arguments(command):
    """명령어의 인자 개수가 잘못된 경우 에러 메시지를 반환한다."""
    return (
        f"(error) ERR wrong number of arguments "
        f"for '{command.lower()}' command"
    )


def integer_error():
    """정수가 필요한 위치에 잘못된 값이 들어온 경우"""
    return "(error) ERR value is not an integer or out of range"


def execute_command(redis, user_input):
    """사용자가 입력한 한 줄의 명령어를 해석하고 실행한다."""

    try:
        parts = shlex.split(user_input)

    except ValueError:
        return "(error) ERR invalid syntax", False

    if len(parts) == 0:
        return None, False

    command = parts[0].upper()

    # 종료 명령
    if command in ("EXIT", "QUIT"):
        return None, True

    # SET key value
    if command == "SET":
        if len(parts) != 3:
            return wrong_arguments("SET"), False

        return redis.set(
            parts[1],
            parts[2]
        ), False

    # GET key
    if command == "GET":
        if len(parts) != 2:
            return wrong_arguments("GET"), False

        return redis.get(parts[1]), False

    # DEL key
    if command == "DEL":
        if len(parts) != 2:
            return wrong_arguments("DEL"), False

        return redis.delete(parts[1]), False

    # EXISTS key
    if command == "EXISTS":
        if len(parts) != 2:
            return wrong_arguments("EXISTS"), False

        return redis.exists(parts[1]), False

    # DBSIZE
    if command == "DBSIZE":
        if len(parts) != 1:
            return wrong_arguments("DBSIZE"), False

        return redis.dbsize(), False

    # KEYS
    if command == "KEYS":
        if len(parts) != 1:
            return wrong_arguments("KEYS"), False

        return redis.keys(), False

    # CONFIG SET maxmemory bytes
    if command == "CONFIG":
        if (
            len(parts) != 4
            or parts[1].upper() != "SET"
            or parts[2].lower() != "maxmemory"
        ):
            return wrong_arguments("CONFIG"), False

        try:
            maxmemory = int(parts[3])

        except ValueError:
            return integer_error(), False

        return redis.config_set_maxmemory(
            maxmemory
        ), False

    # INFO memory
    if command == "INFO":
        if (
            len(parts) != 2
            or parts[1].lower() != "memory"
        ):
            return wrong_arguments("INFO"), False

        return redis.info_memory(), False

    # EXPIRE key seconds
    if command == "EXPIRE":
        if len(parts) != 3:
            return wrong_arguments("EXPIRE"), False

        try:
            seconds = int(parts[2])

        except ValueError:
            return integer_error(), False

        return redis.expire(
            parts[1],
            seconds
        ), False

    # TTL key
    if command == "TTL":
        if len(parts) != 2:
            return wrong_arguments("TTL"), False

        return redis.ttl(parts[1]), False

    # 알 수 없는 명령어
    return (
        f"(error) ERR unknown command '{parts[0]}'",
        False
    )


def main():
    """Mini Redis CLI 실행"""
    redis = MiniRedis()

    while True:
        try:
            user_input = input(
                "mini-redis> "
            ).strip()

        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input == "":
            continue

        output, should_exit = execute_command(
            redis,
            user_input
        )

        if should_exit:
            break

        if output is not None:
            print(output)


def run_tests():
    """CLI 명령어 파싱과 MiniRedis 연결을 확인하는 테스트"""
    redis = MiniRedis()

    print("=== 기본 명령어 테스트 ===")

    commands = [
        "SET name Soojeong",
        "GET name",
        "SET age 27",
        "SET job teacher",
        "EXISTS name",
        "EXISTS city",
        "DBSIZE",
        "KEYS",
        "DEL age",
        "GET age",
        "DBSIZE"
    ]

    for command in commands:
        print(f"mini-redis> {command}")

        output, _ = execute_command(
            redis,
            command
        )

        if output is not None:
            print(output)


    print("\n=== 따옴표 값 테스트 ===")

    command = (
        'SET intro "special education teacher"'
    )

    print(f"mini-redis> {command}")

    output, _ = execute_command(
        redis,
        command
    )

    print(output)

    print("mini-redis> GET intro")

    output, _ = execute_command(
        redis,
        "GET intro"
    )

    print(output)


    print("\n=== 메모리 명령어 테스트 ===")

    commands = [
        "CONFIG SET maxmemory 50",
        "INFO memory"
    ]

    for command in commands:
        print(f"mini-redis> {command}")

        output, _ = execute_command(
            redis,
            command
        )

        print(output)


    print("\n=== TTL 명령어 테스트 ===")

    commands = [
        "SET nickname peachily",
        "TTL nickname",
        "EXPIRE nickname 30",
        "TTL nickname"
    ]

    for command in commands:
        print(f"mini-redis> {command}")

        output, _ = execute_command(
            redis,
            command
        )

        print(output)


    print("\n=== 잘못된 인자 개수 테스트 ===")

    commands = [
        "SET name",
        "GET",
        "DEL",
        "EXPIRE nickname",
        "TTL nickname extra"
    ]

    for command in commands:
        print(f"mini-redis> {command}")

        output, _ = execute_command(
            redis,
            command
        )

        print(output)


    print("\n=== 정수 변환 오류 테스트 ===")

    commands = [
        "CONFIG SET maxmemory hello",
        "EXPIRE nickname hello"
    ]

    for command in commands:
        print(f"mini-redis> {command}")

        output, _ = execute_command(
            redis,
            command
        )

        print(output)


    print("\n=== 잘못된 문법 테스트 ===")

    command = 'SET name "Soojeong'

    print(f"mini-redis> {command}")

    output, _ = execute_command(
        redis,
        command
    )

    print(output)


    print("\n=== 알 수 없는 명령어 테스트 ===")

    command = "HELLO"

    print(f"mini-redis> {command}")

    output, _ = execute_command(
        redis,
        command
    )

    print(output)


    print("\n=== EXIT / QUIT 테스트 ===")

    for command in ["EXIT", "QUIT"]:
        print(f"mini-redis> {command}")

        output, should_exit = execute_command(
            redis,
            command
        )

        print(
            "종료 여부:",
            should_exit
        )


if __name__ == "__main__":
    if (
        len(sys.argv) > 1
        and sys.argv[1].lower() == "test"
    ):
        run_tests()

    else:
        main()