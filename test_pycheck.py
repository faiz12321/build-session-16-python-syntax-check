import os
from unittest import mock
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import make_sample
import pycheck


def check_source(source):
    data = source if isinstance(source, bytes) else source.encode("utf-8")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d, "s.py")
        p.write_bytes(data)
        return pycheck.check(str(p))


def run_main(data=None, args=None):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d, "s.py")
        if data is not None:
            p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = pycheck.main(["pycheck.py"] + (args if args is not None else [str(p)]))
    return rc, buf.getvalue()


class ErrorTests(unittest.TestCase):
    def test_missing_colon_reports_line(self):
        r = check_source("x = 1\ndef f()\n    pass\n")
        self.assertEqual(r["error"]["line"], 2)

    def test_indentation_error_reports_line(self):
        r = check_source("def f():\nreturn 1\n")
        self.assertEqual((r["error"]["kind"], r["error"]["line"]), ("IndentationError", 2))

    def test_unindent_mismatch_reports_line(self):
        r = check_source("def f():\n    a = 1\n  b = 2\n")
        self.assertEqual((r["error"]["kind"], r["error"]["line"]), ("IndentationError", 3))

    def test_mixed_tabs_and_spaces(self):
        r = check_source("if True:\n        a = 1\n\tb = 2\n")
        self.assertEqual(r["error"]["line"], 3)

    def test_unterminated_string(self):
        r = check_source("x = 1\ny = 'abc\n")
        self.assertEqual(r["error"]["line"], 2)

    def test_unclosed_bracket_is_an_error(self):
        self.assertIsNotNone(check_source("x = (1,\ny = 2\n")["error"])

    def test_null_byte_is_an_error(self):
        self.assertIsNotNone(check_source(b"x = 1\x00\n")["error"])

    def test_first_error_only(self):
        r = check_source("def a()\n    pass\ndef b()\n    pass\n")
        self.assertEqual(r["error"]["line"], 1)


class CountTests(unittest.TestCase):
    def test_valid_file_has_no_error(self):
        self.assertIsNone(check_source("x = 1\n")["error"])

    def test_empty_file_is_valid(self):
        r = check_source("")
        self.assertEqual((r["error"], r["lines"]), (None, 0))

    def test_functions_and_classes_counted(self):
        r = check_source("def a():\n    def b():\n        pass\nclass C:\n    def m(self):\n        pass\nasync def d():\n    pass\n")
        self.assertEqual((r["functions"], r["classes"]), (4, 1))

    def test_imports_listed_by_top_name(self):
        r = check_source("import os.path\nimport json, re\nfrom collections.abc import Mapping\nfrom . import sibling\nfrom .pkg import x\n")
        self.assertEqual(r["imports"], ["collections", "json", "os", "re"])

    def test_import_inside_function_is_listed(self):
        self.assertEqual(check_source("def f():\n    import csv\n")["imports"], ["csv"])

    def test_utf8_bom_is_accepted(self):
        self.assertIsNone(check_source(b"\xef\xbb\xbfx = 1\n")["error"])

    def test_encoding_declaration_is_used(self):
        data = b"# -*- coding: latin-1 -*-\nname = '\xe9'\n"
        self.assertIsNone(check_source(data)["error"])


class ReportTests(unittest.TestCase):
    def test_good_file_exit_zero(self):
        rc, out = run_main("import os\n")
        self.assertEqual(rc, 0)
        self.assertIn("No syntax errors found. The code was not run.", out)

    def test_error_exit_one_with_line_and_caret(self):
        rc, out = run_main("def f()\n    pass\n")
        self.assertEqual(rc, 1)
        self.assertIn("on line 1", out)
        self.assertIn("1 | def f()", out)
        self.assertIn("^", out)

    def test_missing_file_exit_two(self):
        self.assertEqual(run_main(args=["no-such-file.py"])[0], 2)

    def test_wrong_arguments_exit_two(self):
        self.assertEqual(run_main(args=[])[0], 2)


class SafetyTests(unittest.TestCase):
    def test_checking_does_not_run_the_code(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d, "marker.txt")
            script = Path(d, "s.py")
            script.write_text(f"open({str(marker)!r}, 'w').write('ran')\n")
            pycheck.check(str(script))
            self.assertFalse(marker.exists())

    def test_checking_does_not_change_the_file(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "s.py")
            p.write_bytes(b"x = 1\n")
            os.utime(p, (1_000_000_000, 1_000_000_000))
            before = (p.read_bytes(), p.stat().st_mtime)
            pycheck.check(str(p))
            after = (p.read_bytes(), p.stat().st_mtime)
        self.assertEqual(before, after)


class SampleTests(unittest.TestCase):
    def test_sample_files(self):
        with tempfile.TemporaryDirectory() as d:
            folder = make_sample.make(Path(d, "sample"))
            good = pycheck.check(str(folder / "good.py"))
            colon = pycheck.check(str(folder / "colon.py"))
            indent = pycheck.check(str(folder / "indent.py"))
        self.assertEqual((good["error"], good["functions"], good["classes"], good["imports"]), (None, 1, 1, ["json", "pathlib"]))
        self.assertEqual(colon["error"]["line"], 4)
        self.assertEqual((indent["error"]["kind"], indent["error"]["line"]), ("IndentationError", 5))


class SetupSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sample = self.root / 'sample'

    def test_existing_folder_preserves_nested_bytes_and_metadata(self):
        (self.sample / 'nested').mkdir(parents=True)
        keep = self.sample / 'nested' / 'keep.bin'
        keep.write_bytes(b'KEEP')
        before = (keep.read_bytes(), keep.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (keep.read_bytes(), keep.stat().st_mtime_ns))
        self.assertEqual(sorted(p.relative_to(self.sample).as_posix() for p in self.sample.rglob('*')), ['nested','nested/keep.bin'])

    def test_existing_file_preserved(self):
        self.sample.write_bytes(b'KEEP')
        before = (self.sample.read_bytes(), self.sample.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (self.sample.read_bytes(), self.sample.stat().st_mtime_ns))

    def test_repeat_setup_preserves_generated_bytes_and_metadata(self):
        make_sample.make(self.sample)
        before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()}
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()})

    def test_cli_refuses_without_replacing(self):
        import shutil, subprocess, sys
        script = self.root / 'make_sample.py'
        shutil.copyfile(Path(__file__).resolve().parent / 'make_sample.py', script)
        self.sample.mkdir()
        keep = self.sample / 'keep'
        keep.write_bytes(b'KEEP')
        result = subprocess.run([sys.executable,str(script)],capture_output=True,text=True,cwd=self.root)
        self.assertEqual(result.returncode,1)
        self.assertIn('Nothing was replaced or deleted',result.stderr)
        self.assertEqual(keep.read_bytes(),b'KEEP')






class PathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'sample'
        make_sample.make(self.root);self.file=self.root/'good.py'
    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlink creation unavailable')
    def code(self,path):
        with redirect_stdout(io.StringIO()) as out:code=pycheck.main(['pycheck.py',str(path)])
        return code,out.getvalue()
    def test_file_link_refuses(self):
        p=self.base/'linked';self.link(p,self.file)
        with self.assertRaises(OSError):pycheck.safe_input(p)
        self.assertEqual(self.code(p)[0],2)
    def test_linked_ancestor_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        self.assertEqual(self.code(p/'good.py')[0],2)
    def test_dangling_link_refuses(self):
        p=self.base/'linked';self.link(p,self.base/'missing')
        self.assertEqual(self.code(p)[0],2)
    def test_self_loop_refuses(self):
        p=self.base/'linked';self.link(p,p)
        self.assertEqual(self.code(p)[0],2)
    def test_hardlink_refuses(self):
        p=self.base/'hard';os.link(self.file,p)
        self.assertEqual(self.code(p)[0],2)
    def test_pipe_refuses_without_blocking(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        p=self.base/'pipe';os.mkfifo(p)
        self.assertEqual(self.code(p)[0],2)
    def test_directory_refuses(self):self.assertEqual(self.code(self.root)[0],2)
    def test_traversal_refuses(self):self.assertEqual(self.code(self.root/'..'/'sample'/'good.py')[0],2)
    def test_reparse_attribute_refuses(self):
        real=Path.lstat;target=self.file
        def fake(path,*args,**kwargs):
            value=real(path,*args,**kwargs)
            if path==target:return type('Reparse',(),{'st_mode':value.st_mode,'st_file_attributes':0x400})()
            return value
        with mock.patch.object(Path,'lstat',fake):self.assertEqual(self.code(self.file)[0],2)
    def test_metadata_failure_nonzero(self):
        with mock.patch.object(Path,'lstat',side_effect=OSError('forced metadata error')):
            code,text=self.code(self.file);self.assertEqual(code,2);self.assertIn('forced metadata error',text)
    def test_setup_linked_parent_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        with self.assertRaises(OSError):make_sample.make(p/'new')
        self.assertFalse((self.root/'new').exists())
    def test_setup_traversal_refuses(self):
        with self.assertRaises(OSError):make_sample.make(self.root/'..'/'new')



if __name__ == "__main__":
    unittest.main()
