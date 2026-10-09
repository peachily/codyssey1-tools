import requests

from config import API_URL, REQUEST_TIMEOUT, model_parameters


class APIError(Exception):
    pass


def response_error(response: requests.Response) -> APIError:
    status = response.status_code
    if status in {401, 403}:
        message = "AI API 인증에 실패했어요. AI_API_KEY와 모델 사용 권한을 확인해 주세요."
    elif status == 429:
        message = "AI API 요청 한도에 도달했어요. 사용량을 확인하거나 잠시 뒤 다시 시도해 주세요."
    elif status >= 500:
        message = "AI 서버에 문제가 생겼어요. 잠시 뒤 다시 시도해 주세요."
    elif status in {400, 404, 422}:
        message = "요청을 처리할 수 없어요. Codyssey의 모델 지원 여부와 요청 설정을 확인해 주세요."
        try:
            error = response.json().get("error", {})
            parameter = error.get("param") if isinstance(error, dict) else None
        except (ValueError, AttributeError):
            parameter = None
        if isinstance(parameter, str) and parameter in {"model", "temperature", "max_tokens", "max_completion_tokens"}:
            message += f"\n문제가 보고된 항목: {parameter}. config.py의 model_parameters 설정을 확인해 주세요."
    else:
        message = "AI API 요청에 실패했어요. Codyssey API의 주소와 서비스 상태를 확인해 주세요."
    return APIError(f"{message} (HTTP {status})")


def generate_text(api_key: str, messages: list[dict[str, str]], model: str,
                  temperature: float, max_tokens: int) -> str:
    payload = {"model": model, "messages": messages,
               **model_parameters(model, temperature, max_tokens)}
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload, timeout=REQUEST_TIMEOUT, allow_redirects=False,
        )
        if not 200 <= response.status_code < 300:
            raise response_error(response)
        response.raise_for_status()
    except requests.Timeout:
        raise APIError("AI 응답을 기다리는 시간이 지났어요. 잠시 뒤 다시 시도해 주세요.") from None
    except requests.RequestException:
        raise APIError("AI와 연결하지 못했어요.\n인터넷 연결을 확인한 뒤 다시 시도해 주세요.") from None
    try:
        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason")
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise APIError("AI 응답 형식이 올바르지 않아요. Codyssey의 응답 JSON 구조를 확인해 주세요.") from None
    if finish_reason == "length":
        raise APIError("토큰 제한으로 AI 응답이 끊겼어요. --max-tokens 값을 늘려 직접 다시 실행해 주세요.")
    if finish_reason == "content_filter":
        raise APIError("AI가 응답을 제한했어요. 전송할 변경 내용을 검토해 주세요.")
    if not isinstance(content, str) or not content.strip():
        raise APIError("AI가 비어 있거나 텍스트가 아닌 응답을 보냈어요. 모델과 토큰 제한을 확인해 주세요.")
    return content.strip()
