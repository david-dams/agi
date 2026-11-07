"""Aggregate input boundaries and bootstrap failure behavior."""
import tempfile
import json
from pathlib import Path
import unittest
import numpy as np
from modern_gai_factor import load_table, subset, attempt, analyze


class ModernTables(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'table.csv'
            path.write_text(text)
            return load_table(path)

    def test_invalid_downloads_rejected(self):
        for text in (
            'model,a,a\nx,1,2\ny,2,3\nz,3,4\n',
            'model,a\nx,1\nx,2\nz,3\n',
            'model,a\nx,nan\ny,2\nz,3\n',
            'model,a\nx,101\ny,2\nz,3\n',
            'model,a\nx,1\ny,1\nz,1\n',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load(text)

    def test_zero_retained_and_subset_order_preserved(self):
        table=self.load('model,a,b\nx,0,9\ny,2,8\nz,3,6\n')
        selected=subset(table,['z','x'],['b','a'])
        np.testing.assert_array_equal(selected['X'],[[6,3],[9,0]])

    def test_singular_resample_is_rejected(self):
        fit,status=attempt(np.array([[1,2,3],[1,2,3],[2,3,5],[3,4,6]]),[[0,1,2]])
        self.assertIsNone(fit)
        self.assertEqual(status,'singular')

    def test_unavailable_shared_partition_is_not_rediscovered(self):
        rng=np.random.default_rng(5)
        table=dict(models=[str(i) for i in range(30)],tasks=list('abcdefghi'),X=rng.normal(size=(30,9)))
        result=analyze('test',table,2,0,fixed_groups=[])
        self.assertEqual(result['fits']['3']['status'],'no viable three-group partition')
        self.assertIsNone(result['fits']['3']['resampling']['intervals'])
        json.dumps(result, allow_nan=False)


if __name__=='__main__':
    unittest.main()
