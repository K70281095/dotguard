import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from dotguard.cli import main
from dotguard.differ import diff
from dotguard.models import Severity
from dotguard.parser import parse


def codes(left, right, **kwargs):
    issues = diff(parse(left, ".env.staging"), parse(right, ".env.production"), **kwargs)
    return [(i.code, i.key, i.path) for i in issues]


class DiffTests(unittest.TestCase):
    def test_same_keys_is_clean(self):
        self.assertEqual(codes("A=1\nB=2\n", "B=3\nA=4\n"), [])

    def test_keys_missing_on_either_side(self):
        found = codes("A=1\nONLY_STAGING=1\n", "A=1\nONLY_PROD=1\n")
        self.assertEqual(
            found,
            [
                ("DD001", "ONLY_STAGING", ".env.staging"),
                ("DD002", "ONLY_PROD", ".env.production"),
            ],
        )

    def test_values_only_compared_when_asked(self):
        self.assertEqual(codes("A=1\n", "A=2\n"), [])
        (issue,) = diff(parse("A=1\n", "l"), parse("A=2\n", "r"), compare_values=True)
        self.assertEqual((issue.code, issue.severity), ("DD003", Severity.WARNING))

    def test_values_are_never_printed(self):
        left, right = parse("TOKEN=old-secret\n", "l"), parse("TOKEN=new-secret\n", "r")
        (issue,) = diff(left, right, compare_values=True)
        self.assertNotIn("secret", issue.message.replace("TOKEN", ""))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            left, right = os.path.join(tmp, "a.env"), os.path.join(tmp, "b.env")
            with open(left, "w", encoding="utf-8") as handle:
                handle.write("A=1\n")
            with open(right, "w", encoding="utf-8") as handle:
                handle.write("A=2\n")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["diff", left, right]), 0)
                self.assertEqual(main(["diff", left, right, "--values"]), 0)
                self.assertEqual(main(["diff", left, right, "--values", "--fail-on-warning"]), 1)


if __name__ == "__main__":
    unittest.main()
