import json
import os
import unittest
from unittest.mock import patch

import requests

from ai_client import APIError, generate_text
from config import get_api_key


def make_response(data, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(data).encode("utf-8")
    return response


def success_response(text="feat: 기능 추가\n\n- 입력 처리를 추가해요.", finish_reason="stop"):
    return make_response({"choices": [{"message": {"content": text}, "finish_reason": finish_reason}]})


class AIClientTests(unittest.TestCase):
    def generate(self, model="gpt-5-mini"):
        return generate_text("test-key", [{"role": "user", "content": "test"}], model, 0.2, 8192)

    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "설정되지"):
                get_api_key()

    def test_invalid_key_does_not_leak(self):
        for key in ["private\nkey", "private 키"]:
            with patch.dict(os.environ, {"AI_API_KEY": key}):
                with self.assertRaises(ValueError) as caught:
                    get_api_key()
                self.assertNotIn("private", str(caught.exception))

    def test_gpt5_parameters_and_one_request(self):
        with patch("ai_client.requests.post", return_value=success_response()) as post:
            self.assertIn("feat:", self.generate())
            post.assert_called_once()
            arguments = post.call_args.kwargs
            self.assertNotIn("temperature", arguments["json"])
            self.assertEqual(arguments["json"]["max_completion_tokens"], 8192)
            self.assertEqual(arguments["timeout"], 30)
            self.assertFalse(arguments["allow_redirects"])

    def test_other_model_parameters(self):
        with patch("ai_client.requests.post", return_value=success_response()) as post:
            self.generate("gpt-4o-mini")
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["temperature"], 0.2)
            self.assertEqual(payload["max_tokens"], 8192)
            self.assertNotIn("max_completion_tokens", payload)

    def test_http_errors_do_not_retry_or_leak_response(self):
        for status, expected in [(400, "요청"), (401, "인증"), (403, "인증"), (429, "한도"), (500, "서버"), (302, "실패")]:
            with self.subTest(status=status):
                response = make_response({"error": {"message": "private-key"}}, status)
                with patch("ai_client.requests.post", return_value=response) as post:
                    with self.assertRaisesRegex(APIError, expected) as caught:
                        self.generate()
                    self.assertNotIn("private-key", str(caught.exception))
                    post.assert_called_once()

    def test_unsupported_parameter_reported_without_retry(self):
        response = make_response({"error": {"param": "max_completion_tokens", "message": "private"}}, 400)
        with patch("ai_client.requests.post", return_value=response) as post:
            with self.assertRaisesRegex(APIError, "max_completion_tokens"):
                self.generate()
            post.assert_called_once()

    def test_malformed_error_parameter(self):
        response = make_response({"error": {"param": ["private"]}}, 400)
        with patch("ai_client.requests.post", return_value=response):
            with self.assertRaises(APIError):
                self.generate()

    def test_network_and_timeout_errors(self):
        for error, expected in [(requests.ConnectionError("private-key"), "연결"), (requests.Timeout("private-key"), "시간")]:
            with self.subTest(error=type(error).__name__):
                with patch("ai_client.requests.post", side_effect=error) as post:
                    with self.assertRaisesRegex(APIError, expected) as caught:
                        self.generate()
                    self.assertNotIn("private-key", str(caught.exception))
                    post.assert_called_once()

    def test_invalid_response_structure(self):
        for data in [None, [], {}, {"choices": []}, {"choices": [None]}, {"choices": [{"message": {}}]}]:
            with self.subTest(data=data):
                with patch("ai_client.requests.post", return_value=make_response(data)):
                    with self.assertRaises(APIError):
                        self.generate()

    def test_invalid_json(self):
        response = make_response({})
        response._content = b"<html>not JSON</html>"
        with patch("ai_client.requests.post", return_value=response):
            with self.assertRaises(APIError):
                self.generate()

    def test_empty_and_non_text_content(self):
        for content in [None, "", "  ", [], 123]:
            with self.subTest(content=content):
                with patch("ai_client.requests.post", return_value=success_response(content)):
                    with self.assertRaises(APIError):
                        self.generate()

    def test_truncated_output_is_rejected(self):
        with patch("ai_client.requests.post", return_value=success_response(finish_reason="length")):
            with self.assertRaisesRegex(APIError, "토큰"):
                self.generate()


if __name__ == "__main__":
    unittest.main()
