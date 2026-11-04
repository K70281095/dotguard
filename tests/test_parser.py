import unittest

from dotguard.parser import ParseError, parse


class ParserTests(unittest.TestCase):
    def test_basic_assignments(self):
        env = parse("A=1\nexport B=two\nC=\n")
        self.assertEqual([(e.key, e.value) for e in env.entries], [("A", "1"), ("B", "two"), ("C", "")])

    def test_line_numbers_skip_comments_and_blanks(self):
        env = parse("# comment\n\nA=1\n")
        self.assertEqual(env.get("A").line, 3)

    def test_double_quotes_and_escapes(self):
        env = parse('A="hello\\nworld"\nB="say \\"hi\\""\n')
        self.assertEqual(env.get("A").value, "hello\nworld")
        self.assertEqual(env.get("B").value, 'say "hi"')

    def test_single_quotes_are_literal(self):
        env = parse("A='no\\nescape # here'\n")
        self.assertEqual(env.get("A").value, "no\\nescape # here")

    def test_inline_comments(self):
        env = parse('A=value # note\nB="quoted" # note\nC=http://x/#anchor\n')
        self.assertEqual(env.get("A").value, "value")
        self.assertEqual(env.get("B").value, "quoted")
        self.assertEqual(env.get("C").value, "http://x/#anchor")

    def test_annotations_and_docs_attach_to_next_key(self):
        env = parse("# The HTTP port\n# @type port\n# @required\nPORT=8080\n")
        entry = env.get("PORT")
        self.assertEqual(entry.annotations, {"type": "port", "required": ""})
        self.assertEqual(entry.doc, ["The HTTP port"])

    def test_blank_line_detaches_annotations(self):
        env = parse("# @required\n\nA=1\n")
        self.assertEqual(env.get("A").annotations, {})

    def test_errors(self):
        cases = {
            "NOEQUALS\n": "expected KEY=value",
            "1BAD=x\n": "invalid key",
            'A="open\n': "unterminated",
            'A="x" junk\n': "unexpected text",
            "A=1\nA=2\n": "duplicate key",
        }
        for text, message in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(ParseError) as ctx:
                    parse(text, path=".env")
                self.assertIn(message, str(ctx.exception))
                self.assertTrue(str(ctx.exception).startswith(".env:"))


if __name__ == "__main__":
    unittest.main()
