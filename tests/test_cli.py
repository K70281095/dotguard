import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from dotguard.cli import main, render_example
from dotguard.parser import parse


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self._cwd = os.getcwd()
        os.chdir(self.dir)
        os.environ["NO_COLOR"] = "1"

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_check_passes(self):
        self.write(".env", "PORT=8080\n")
        self.write(".env.example", "# @type port\nPORT=\n")
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("no problems found", out)

    def test_check_fails_with_exit_code_1(self):
        self.write(".env", "PORT=nope\n")
        self.write(".env.example", "# @type port\nPORT=\n")
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn(".env:1  error DG004", out)

    def test_warnings_only_fail_when_asked(self):
        self.write(".env", "PORT=1\nEXTRA=1\n")
        self.write(".env.example", "PORT=\n")
        self.assertEqual(self.run_cli("check")[0], 0)
        self.assertEqual(self.run_cli("check", "--fail-on-warning")[0], 1)

    def test_json_output(self):
        self.write(".env", "")
        self.write(".env.example", "A=\n")
        code, out, _ = self.run_cli("check", "--format", "json")
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(data["summary"], {"errors": 1, "warnings": 0})
        self.assertEqual(data["issues"][0]["code"], "DG001")

    def test_github_output(self):
        self.write(".env", "PORT=x\n")
        self.write(".env.example", "# @type port\nPORT=\n")
        _, out, _ = self.run_cli("check", "--format", "github")
        self.assertTrue(out.startswith("::error file=.env,line=1,title=dotguard DG004::"))

    def test_missing_file_is_usage_error(self):
        code, _, err = self.run_cli("check", "--env", "nope.env")
        self.assertEqual(code, 2)
        self.assertIn("file not found", err)

    def test_parse_error_is_usage_error(self):
        self.write(".env", "BROKEN\n")
        self.write(".env.example", "")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 2)
        self.assertIn(".env:1", err)

    def test_scan(self):
        self.write(".env.example", "API_TOKEN=changeme\n")
        self.assertEqual(self.run_cli("scan")[0], 0)

    def test_init_writes_example_and_refuses_overwrite(self):
        self.write(".env", "PORT=8080\nAPI_TOKEN=abc123\nDEBUG=true\n")
        code, _, _ = self.run_cli("init")
        self.assertEqual(code, 0)
        with open(".env.example", encoding="utf-8") as handle:
            example = parse(handle.read())
        self.assertEqual(example.get("PORT").annotations, {"type": "port"})
        self.assertIn("secret", example.get("API_TOKEN").annotations)
        self.assertEqual(example.get("API_TOKEN").value, "")
        self.assertEqual(self.run_cli("init")[0], 2)

    def test_render_example_keep_values_never_keeps_secrets(self):
        source = parse("HOST=localhost\nDB_PASSWORD=s3cret\n")
        example = parse(render_example(source, keep_values=True))
        self.assertEqual(example.get("HOST").value, "localhost")
        self.assertEqual(example.get("DB_PASSWORD").value, "")

    def test_render_example_round_trips_awkward_values(self):
        source = parse('GREETING="hello world # not a comment"\n')
        example = parse(render_example(source, keep_values=True))
        self.assertEqual(example.get("GREETING").value, "hello world # not a comment")


if __name__ == "__main__":
    unittest.main()
