import os
import re

API_URL = "https://copa.codyssey.kr/v1/chat/completions"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 8192
REQUEST_TIMEOUT = 30


def get_api_key() -> str:
    key = os.environ.get("AI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "AI API 키가 설정되지 않았어요.\n"
            "AI_API_KEY 환경변수를 등록한 뒤 다시 실행해 주세요."
        )
    if any(character.isspace() for character in key) or not key.isascii():
        raise ValueError("AI_API_KEY 값에 공백이나 잘못된 문자가 있어요. 값을 확인해 주세요.")
    return key


def model_parameters(model: str, temperature: float, max_tokens: int) -> dict:
    # 추론 모델의 기본 추론 설정에서는 temperature 생략
    if re.match(r"^(gpt-5(?:[.\-]|$)|o[134](?:-|$))", model):
        return {"max_completion_tokens": max_tokens}
    return {"temperature": temperature, "max_tokens": max_tokens}
