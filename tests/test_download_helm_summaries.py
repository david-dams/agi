import io
import gzip
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'download_helm_summaries.py'


class HelmDownloads(unittest.TestCase):
    def run_fixture(self, bad_size=False, compressed=False):
        with tempfile.TemporaryDirectory() as directory:
            script=Path(directory)/SOURCE.name
            script.write_bytes(SOURCE.read_bytes())
            calls=[]
            body=gzip.compress(b'{}') if compressed else b'{}'
            def fetch(url,timeout):
                calls.append(url)
                if '/download/' in url:
                    self.assertIn('generation=123',url)
                    return io.BytesIO(body)
                from urllib.parse import parse_qs,urlparse
                prefix=parse_qs(urlparse(url).query)['prefix'][0]
                page={'items':[{'name':prefix+'v1/groups/core_scenarios.json','generation':'123','size':str(len(body)+int(bad_size))}]}
                return io.BytesIO(json.dumps(page).encode())
            with patch('urllib.request.urlopen',side_effect=fetch):
                if bad_size:
                    with self.assertRaises(SystemExit):runpy.run_path(str(script),run_name='__main__')
                else:
                    runpy.run_path(str(script),run_name='__main__')
            root=Path(directory)/'public-data/helm-summaries'
            manifest=json.loads((root/'manifest.json').read_text())
            if bad_size:
                self.assertEqual(len(manifest['failures']),3)
                self.assertFalse(list(root.rglob('core_scenarios.json')))
            else:
                self.assertEqual(len(manifest['objects']),3)
                self.assertFalse(manifest['failures'])
                self.assertEqual(len(list(root.rglob('core_scenarios.json'))),3)

    def test_pins_object_generation(self):self.run_fixture()
    def test_size_mismatch_is_recorded_without_completed_file(self):self.run_fixture(bad_size=True)
    def test_gzip_objects_are_decoded_before_json_validation(self):self.run_fixture(compressed=True)
