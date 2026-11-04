import unittest

from dotguard.checker import check
from dotguard.models import Severity
from dotguard.parser import parse


def codes(env_text, example_text, **kwargs):
    issues = check(parse(env_text, ".env"), parse(example_text, ".env.example"), **kwargs)
    return [(i.code, i.key) for i in issues]


class CheckerTests(unittest.TestCase):
    def test_clean_file_has_no_issues(self):
        self.assertEqual(codes("A=1\nB=x\n", "A=\nB=\n"), [])

    def test_missing_key(self):
        self.assertEqual(codes("A=1\n", "A=\nB=\n"), [("DG001", "B")])

    def test_optional_key_may_be_missing(self):
        self.assertEqual(codes("A=1\n", "A=\n# @optional\nB=\n"), [])

    def test_undocumented_key_is_warning_or_error_in_strict_mode(self):
        env, example = parse("A=1\nEXTRA=1\n", ".env"), parse("A=\n", ".env.example")
        (issue,) = check(env, example)
        self.assertEqual((issue.code, issue.severity), ("DG002", Severity.WARNING))
        (issue,) = check(env, example, strict=True)
        self.assertEqual(issue.severity, Severity.ERROR)

    def test_required_empty(self):
        self.assertEqual(codes("A=\n", "# @required\nA=\n"), [("DG003", "A")])

    def test_empty_optional_value_skips_type_check(self):
        self.assertEqual(codes("A=\n", "# @type int\nA=\n"), [])

    def test_types(self):
        cases = [
            ("int", "12", True), ("int", "1.5", False),
            ("float", "1.5", True), ("float", "abc", False),
            ("bool", "yes", True), ("bool", "maybe", False),
            ("port", "8080", True), ("port", "70000", False), ("port", "0", False),
            ("url", "https://example.com/x", True), ("url", "example.com", False),
            ("email", "dev@example.com", True), ("email", "dev@", False),
        ]
        for type_name, value, ok in cases:
            with self.subTest(type=type_name, value=value):
                found = codes(f"A={value}\n", f"# @type {type_name}\nA=\n")
                self.assertEqual(found, [] if ok else [("DG004", "A")])

    def test_pattern(self):
        example = "# @pattern [a-z]+-[0-9]+\nA=\n"
        self.assertEqual(codes("A=abc-12\n", example), [])
        self.assertEqual(codes("A=abc\n", example), [("DG005", "A")])

    def test_values(self):
        example = "# @values development, staging, production\nAPP_ENV=\n"
        self.assertEqual(codes("APP_ENV=staging\n", example), [])
        self.assertEqual(codes("APP_ENV=prod\n", example), [("DG007", "APP_ENV")])

    def test_min_max(self):
        example = "# @type int\n# @min 1\n# @max 10\nA=\n"
        self.assertEqual(codes("A=5\n", example), [])
        self.assertEqual(codes("A=0\n", example), [("DG006", "A")])
        self.assertEqual(codes("A=11\n", example), [("DG006", "A")])

    def test_deprecated(self):
        found = codes("OLD=1\n", "# @deprecated use NEW instead\n# @optional\nOLD=\n")
        self.assertEqual(found, [("DG008", "OLD")])

    def test_bad_annotations(self):
        self.assertIn(("DG009", "A"), codes("A=1\n", "# @requird\nA=\n"))
        self.assertIn(("DG010", "A"), codes("A=1\n", "# @type colour\nA=\n"))
        self.assertIn(("DG010", "A"), codes("A=1\n", "# @pattern [unclosed\nA=\n"))

    def test_unresolved_reference_warning(self):
        issues = check(parse("A=${NOPE}\n", ".env"), parse("A=\n", ".env.example"))
        self.assertEqual([(i.code, i.severity) for i in issues], [("DG011", Severity.WARNING)])

    def test_secret_values_are_masked_in_messages(self):
        issues = check(
            parse("TOKEN=hunter2\n", ".env"),
            parse("# @secret\n# @type int\nTOKEN=\n", ".env.example"),
        )
        self.assertNotIn("hunter2", issues[0].message)
        self.assertIn("****", issues[0].message)


if __name__ == "__main__":
    unittest.main()
