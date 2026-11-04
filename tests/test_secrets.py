import unittest

from dotguard.parser import parse
from dotguard.secrets import scan, shannon_entropy


def codes(text):
    return [(i.code, i.key) for i in scan(parse(text, ".env.example"))]


# Built from pieces so this test file never looks like a leaked secret itself.
FAKE_AWS = "AKIA" + "Z" * 16
FAKE_GITHUB = "ghp_" + "a1B2c3D4e5" * 4


class SecretScanTests(unittest.TestCase):
    def test_known_token_formats(self):
        self.assertEqual(codes(f"AWS_KEY={FAKE_AWS}\n"), [("DS001", "AWS_KEY")])
        self.assertEqual(codes(f"GH={FAKE_GITHUB}\n"), [("DS001", "GH")])

    def test_private_key_header(self):
        found = codes('KEY="-----BEGIN RSA PRIVATE KEY-----\\nabc"\n')
        self.assertEqual(found, [("DS001", "KEY")])

    def test_placeholders_are_ignored(self):
        text = "\n".join(
            f"API_TOKEN_{i}={value}"
            for i, value in enumerate(["", "changeme", "<your-token>", "xxxxxxxx", "${TOKEN}", "your_api_key"])
        )
        self.assertEqual(codes(text + "\n"), [])

    def test_high_entropy_value_under_sensitive_name(self):
        self.assertEqual(codes("DB_PASSWORD=q8Zr2LmV9xT4pW7nK3s\n"), [("DS002", "DB_PASSWORD")])

    def test_high_entropy_value_under_plain_name_is_fine(self):
        self.assertEqual(codes("BUILD_ID=q8Zr2LmV9xT4pW7nK3s\n"), [])

    def test_secret_annotation_marks_any_name_sensitive(self):
        self.assertEqual(codes("# @secret\nDSN=q8Zr2LmV9xT4pW7nK3s\n"), [("DS002", "DSN")])

    def test_entropy(self):
        self.assertEqual(shannon_entropy(""), 0.0)
        self.assertEqual(shannon_entropy("aaaa"), 0.0)
        self.assertAlmostEqual(shannon_entropy("abcd"), 2.0)


if __name__ == "__main__":
    unittest.main()
