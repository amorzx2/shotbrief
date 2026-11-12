import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shotbrief


def sample():
    return {"title": "晨光 / Morning", "shots": [{"duration": 6, "scene": "海边", "camera": "Slow tilt", "action": "Open hands", "ending": "White frame"}]}


class ValidationTests(unittest.TestCase):
    def test_valid_unicode(self):
        self.assertEqual(shotbrief.validate(sample()), sample())

    def test_normalizes_without_mutation(self):
        doc = sample()
        doc['title'] = '  Morning  '
        before = copy.deepcopy(doc)
        self.assertEqual(shotbrief.validate(doc)['title'], 'Morning')
        self.assertEqual(doc, before)

    def test_bad_root(self):
        for value in (None, [], 'text', 1):
            with self.subTest(value=value), self.assertRaises(shotbrief.ValidationError):
                shotbrief.validate(value)

    def test_bad_title(self):
        for value in (None, '', ' \t', 5):
            doc = sample(); doc['title'] = value
            with self.subTest(value=value), self.assertRaises(shotbrief.ValidationError):
                shotbrief.validate(doc)

    def test_empty_shots(self):
        for value in ([], None, {}):
            doc = sample(); doc['shots'] = value
            with self.subTest(value=value), self.assertRaises(shotbrief.ValidationError):
                shotbrief.validate(doc)

    def test_bad_shot(self):
        doc = sample(); doc['shots'] = ['text']
        with self.assertRaisesRegex(shotbrief.ValidationError, r'shots\[1\]'):
            shotbrief.validate(doc)

    def test_duration_bounds(self):
        for value in (True, False, 0, -1, '6', None, float('nan'), float('inf'), 86401, 10**400):
            doc = sample(); doc['shots'][0]['duration'] = value
            with self.subTest(value=str(value)), self.assertRaises(shotbrief.ValidationError):
                shotbrief.validate(doc)

    def test_fractional_duration(self):
        doc = sample(); doc['shots'][0]['duration'] = 0.5
        self.assertEqual(shotbrief.validate(doc)['shots'][0]['duration'], 0.5)

    def test_missing_text_field(self):
        for key in shotbrief.TEXT_FIELDS:
            doc = sample(); del doc['shots'][0][key]
            with self.subTest(key=key), self.assertRaises(shotbrief.ValidationError):
                shotbrief.validate(doc)

    def test_extra_fields(self):
        doc = sample(); doc['titel'] = 'typo'
        with self.assertRaisesRegex(shotbrief.ValidationError, 'unknown fields'):
            shotbrief.validate(doc)
        doc = sample(); doc['shots'][0]['actionn'] = 'typo'
        with self.assertRaisesRegex(shotbrief.ValidationError, 'unknown fields'):
            shotbrief.validate(doc)

    def test_render_cards(self):
        doc = sample(); doc['shots'].append(dict(doc['shots'][0], duration=3.5))
        text = shotbrief.render(doc)
        self.assertIn('2 shots · 9.5 seconds', text)
        self.assertIn('## Shot 02 · 3.5s', text)
        self.assertIn('海边', text)
        self.assertTrue(text.endswith('\n'))

    def test_escape_markdown_html(self):
        doc = sample(); doc['shots'][0]['scene'] = '<script>x</script> [link](url) **bold**\nnext'
        text = shotbrief.render(doc)
        self.assertNotIn('<script>', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertIn(r'\[link\]\(url\)', text)
        self.assertIn('<br>next', text)

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(shotbrief.ValidationError, 'Duplicate'):
            json.loads('{"title":"one","title":"two"}', object_pairs_hook=shotbrief._pairs)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input.json'
        self.source.write_text(json.dumps(sample(), ensure_ascii=False), encoding='utf-8')

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = shotbrief.main([str(arg) for arg in args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_stdout(self):
        code, out, err = self.run_cli(self.source)
        self.assertEqual(code, 0); self.assertIn('晨光', out); self.assertFalse(err)

    def test_check(self):
        code, out, err = self.run_cli(self.source, '--check')
        self.assertEqual(code, 0); self.assertEqual(out, 'Valid shot list.\n')
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_utf8_file(self):
        dest = self.root / 'output.md'
        self.assertEqual(self.run_cli(self.source, '-o', dest)[0], 0)
        self.assertIn('晨光', dest.read_text(encoding='utf-8'))

    def test_overwrite_requires_force(self):
        dest = self.root / 'output.md'; dest.write_text('keep', encoding='utf-8')
        self.assertEqual(self.run_cli(self.source, '-o', dest)[0], 1)
        self.assertEqual(dest.read_text(), 'keep')
        self.assertEqual(self.run_cli(self.source, '-o', dest, '--force')[0], 0)
        self.assertIn('Shot 01', dest.read_text())

    def test_input_cannot_be_output(self):
        before = self.source.read_bytes()
        self.assertEqual(self.run_cli(self.source, '-o', self.source, '--force')[0], 1)
        self.assertEqual(before, self.source.read_bytes())

    def test_hardlink_cannot_overwrite_input(self):
        dest = self.root / 'alias.json'
        try:
            os.link(self.source, dest)
        except OSError:
            self.skipTest('Hard links unavailable')
        self.assertEqual(self.run_cli(self.source, '-o', dest, '--force')[0], 1)
        self.assertEqual(json.loads(self.source.read_text()), sample())

    def test_missing_input(self):
        code, out, err = self.run_cli(self.root / 'missing.json')
        self.assertEqual(code, 1); self.assertFalse(out); self.assertIn('shotbrief:', err)

    def test_bad_json_no_output_created(self):
        self.source.write_text('{broken')
        dest = self.root / 'out.md'
        self.assertEqual(self.run_cli(self.source, '-o', dest)[0], 1)
        self.assertFalse(dest.exists())

    def test_invalid_utf8(self):
        self.source.write_bytes(b'\xff')
        self.assertEqual(self.run_cli(self.source)[0], 1)

    def test_bom(self):
        self.source.write_text(json.dumps(sample()), encoding='utf-8-sig')
        self.assertEqual(self.run_cli(self.source)[0], 0)

    def test_duplicate_json_error(self):
        self.source.write_text('{"title":"a","title":"b"}')
        self.assertEqual(self.run_cli(self.source)[0], 1)

    def test_cli_incompatible_options(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli(self.source, '--check', '-o', self.root / 'out.md')
        self.assertEqual(caught.exception.code, 2)

    def test_real_subprocess(self):
        script = Path(shotbrief.__file__).resolve()
        result = subprocess.run([sys.executable, str(script), str(self.source), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0); self.assertIn('Valid', result.stdout)


if __name__ == '__main__':
    unittest.main()
