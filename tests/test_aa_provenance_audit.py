import json
import unittest

from aa_provenance_audit import parse_models


class SourcePayloadTests(unittest.TestCase):
    def test_richer_array_wins_over_navigation(self):
        stream = '"models":[{"id":"a","slug":"a"}]\n' + '"models":[{"id":"a","slug":"a","gpqa":0.5}]'
        html = 'self.__next_f.push([1,' + json.dumps(stream) + '])'
        self.assertEqual(parse_models(html)[0]['gpqa'], 0.5)

    def test_missing_array_rejected(self):
        with self.assertRaises(ValueError):
            parse_models('<html></html>')
