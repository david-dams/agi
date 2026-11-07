import unittest
from epoch_data_audit import unique_cells, coverage


class EpochAudit(unittest.TestCase):
    def test_conflicts_are_excluded_without_picking_best(self):
        cells,issues=unique_cells([
            ('a','t','0'),('a','t','0'),('b','t','.4'),('b','t','.8'),
            ('c','t','nan'),('','t','.9'),('d','t','')])
        self.assertEqual(cells,{('a','t'):0.0})
        self.assertEqual(issues['conflicting_cells'],1)
        self.assertEqual(issues['repeated_cells'],2)
        self.assertEqual(issues['invalid_records'],3)

    def test_complete_panels_and_release_cohorts_preserve_exact_ids(self):
        cells={(model,f't{i}'):float(i+j) for j,model in enumerate(['old_low','new_high','unknown']) for i in range(9)}
        del cells['old_low','t8']
        result=coverage(cells,{'old_low':'2024-01-01','new_high':'2026-01-01'}, {})
        self.assertEqual(result['observations'],26)
        self.assertEqual(result['complete_all'],2)
        self.assertEqual(result['greedy_panels']['9']['models'],['new_high','unknown'])
        cohorts={r['year']:r for r in result['cohorts']}
        self.assertEqual(cohorts['2024']['greedy_nine_benchmark_complete'],0)
        self.assertEqual(cohorts['2026']['greedy_nine_benchmark_complete'],1)
        self.assertEqual(cohorts['unknown']['models'],1)


if __name__=='__main__':
    unittest.main()
