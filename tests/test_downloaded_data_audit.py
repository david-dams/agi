import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
import downloaded_data_audit as audit


class DownloadedDataAudit(unittest.TestCase):
    def test_release_period_boundaries(self):
        self.assertEqual(audit.period('2025-06-30','half'),'2025H1')
        self.assertEqual(audit.period('2025-07-01','half'),'2025H2')
        self.assertEqual(audit.period('2026-04-01','quarter'),'2026Q2')
        self.assertEqual(audit.period('','year'),'unknown')
        with self.assertRaises(ValueError):audit.period('not-a-date','half')

    def wild_fixture(self,scores):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'wild').mkdir()
            rows=[dict(model=m,task='task',subtask='subtask',item_id=i,score=s)
                  for (m,i),s in zip([('a','q1'),('a','q1'),('a','q2'),('b','q1')],scores)]
            pq.write_table(pa.Table.from_pylist(rows),root/'wild/data.parquet')
            with patch.object(audit,'DATA',root),patch.object(audit,'OUT',root):
                return audit.wild_audit()

    def test_shared_item_coverage_and_conflicts_are_distinct(self):
        r=self.wild_fixture([0,1,1,1])
        self.assertEqual(r['model_task_cells'],2)
        self.assertEqual(r['complete_models_per_task'],{'task':1})
        self.assertEqual(r['common_item_keys_per_task'],{'task':1})
        self.assertEqual(r['repeated_model_item_keys'],1)
        self.assertEqual(r['conflicting_repeated_model_item_cells'],1)
        self.assertEqual(r['models_complete_on_50_model_tasks'],[])

    def test_nonbinary_and_missing_scores_rejected(self):
        for score in [2,None]:
            with self.subTest(score=score),self.assertRaises(ValueError):
                self.wild_fixture([0,score,1,1])


if __name__=='__main__':unittest.main()
