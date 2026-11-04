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

    def test_multiline_double_quoted(self):
        env = parse('CERT="line one\nline two"\nNEXT=1\n')
        self.assertEqual(env.get("CERT").value, "line one\nline two")
        self.assertEqual(env.get("CERT").line, 1)
        self.assertEqual(env.get("NEXT").line, 3)

    def test_multiline_single_quoted_keeps_hashes_and_dollars(self):
        env = parse("KEY='-----BEGIN-----\n# not a comment $HOME\n-----END-----' # note\n")
        self.assertEqual(env.get("KEY").value, "-----BEGIN-----\n# not a comment $HOME\n-----END-----")

    def test_unterminated_multiline_reports_start_line(self):
        with self.assertRaises(ParseError) as ctx:
            parse('A=1\nB="never closed\nC=3\n', path=".env")
        self.assertIn(".env:2:", str(ctx.exception))

    def test_interpolation(self):
        env = parse(
            "HOST=db\nPORT=5432\n"
            "URL=postgres://${HOST}:$PORT/app\n"
            'QUOTED="${HOST}-x"\n'
            "LITERAL='${HOST}'\n"
            'ESCAPED="\\${HOST}"\n'
            "BARE_ESCAPED=\\$HOST\n"
        )
        self.assertEqual(env.get("URL").value, "postgres://db:5432/app")
        self.assertEqual(env.get("QUOTED").value, "db-x")
        self.assertEqual(env.get("LITERAL").value, "${HOST}")
        self.assertEqual(env.get("ESCAPED").value, "${HOST}")
        self.assertEqual(env.get("BARE_ESCAPED").value, "$HOST")

    def test_interpolation_defaults(self):
        env = parse("EMPTY=\nA=${MISSING:-one}\nB=${EMPTY:-two}\nC=${EMPTY-three}\nD=${MISSING-four}\n")
        self.assertEqual(
            [env.get(k).value for k in "ABCD"],
            ["one", "two", "", "four"],
        )
        self.assertEqual(env.get("A").unresolved, [])

    def test_unresolved_references_are_recorded(self):
        env = parse("A=${LATER}/$LATER\nLATER=x\n")
        self.assertEqual(env.get("A").value, "/")
        self.assertEqual(env.get("A").unresolved, ["LATER"])

    def test_interpolation_can_be_disabled(self):
        env = parse("A=1\nB=${A}\n", interpolate=False)
        self.assertEqual(env.get("B").value, "${A}")

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
