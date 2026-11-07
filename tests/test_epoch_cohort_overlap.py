import itertools
import unittest
from epoch_cohort_overlap import shared_batteries


class SharedBatteries(unittest.TestCase):
    def test_matches_brute_force_and_uses_same_tasks_in_each_cohort(self):
        observed={'a':{'old1','old2','new1','new2','new3'},
                  'b':{'old1','old2','new1','new2'},
                  'c':{'old2','new2','new3'},
                  'd':{'old1','new1','new2'}}
        cohorts={'2024':{'old1','old2'},'2026':{'new1','new2','new3'}}
        result=shared_batteries(observed,cohorts,min_support=1,max_tasks=4)
        expected={}
        for p in range(1,5):
            for tasks in itertools.combinations(sorted(observed),p):
                common=set.intersection(*(observed[t] for t in tasks))
                counts=[len(common&models) for models in cohorts.values()]
                if min(counts)<1: continue
                key=(min(counts),sum(counts))
                expected[p]=max(expected.get(p,(0,0)),key)
        self.assertEqual({int(p):tuple(v['objective']) for p,v in result['best'].items()},expected)
        for panel in result['best'].values():
            for year,models in panel['models'].items():
                self.assertEqual(len(models),panel['counts'][year])
                self.assertTrue(set(models)<=cohorts[year])
                self.assertTrue(all(m in observed[t] for m in models for t in panel['tasks']))

    def test_individual_coverage_does_not_imply_shared_battery(self):
        cohorts={'2024':{'a','b'},'2025':{'c','d'}}
        observed={'task1':{'a','c'},'task2':{'b','d'}}
        result=shared_batteries(observed,cohorts,min_support=1,max_tasks=2)
        self.assertIn('1',result['best'])
        self.assertNotIn('2',result['best'])


if __name__=='__main__':
    unittest.main()
