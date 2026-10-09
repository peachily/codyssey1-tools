import unittest

from safe_mode import is_sensitive_file, mask_sensitive_data


class SafeModeTests(unittest.TestCase):
    def test_api_keys_email_and_authorization(self):
        text = "sk-test123456789 user@example.com ghp_abcdefghijk Bearer abc.def.ghi"
        masked = mask_sensitive_data(text)
        for secret in ["sk-test123456789", "user@example.com", "ghp_abcdefghijk", "abc.def.ghi"]:
            self.assertNotIn(secret, masked)

    def test_assignments(self):
        for text in [
            'password = "hello world"', "PASSWORD='hello world'",
            '"api_key": "hello world"', "access_token=hello",
            "DB_PASSWORD: hello", "clientSecret = 'hello'", "pwd=hello",
        ]:
            with self.subTest(text=text):
                self.assertNotIn("hello", mask_sensitive_data(text))
                self.assertIn("[MASKED]", mask_sensitive_data(text))

    def test_exact_environment_key_masked(self):
        self.assertEqual(mask_sensitive_data("plain-custom-key", "plain-custom-key"), "[MASKED]")

    def test_password_with_escaped_quotes(self):
        text = r'password = "first\"second"'
        self.assertEqual(mask_sensitive_data(text), "password = [MASKED]")

    def test_private_key_block(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nsecret-body\n-----END RSA PRIVATE KEY-----"
        self.assertEqual(mask_sensitive_data(text), "[MASKED]")

    def test_sensitive_files(self):
        for name in [".env", "sub/.env.local", "key.pem", "secret.key", ".aws/config", "id_ed25519", "credentials.json", "secrets.yaml", "service-account.json"]:
            with self.subTest(name=name):
                self.assertTrue(is_sensitive_file(name))
        for name in ["main.py", "config.py", "README.md", "tests/test_safe_mode.py"]:
            self.assertFalse(is_sensitive_file(name))

    def test_normal_text_unchanged(self):
        text = "def add(a, b):\n    return a + b"
        self.assertEqual(mask_sensitive_data(text), text)


if __name__ == "__main__":
    unittest.main()
