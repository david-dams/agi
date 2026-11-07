import unittest
from datetime import date,timedelta
import numpy as np
from aa_cohort_pca import pc1,similarity
from parallel_rolling_pca import complete_rows,monthly_windows,weighted_axes,prepare
from rolling_pca_sources import record,panel,iso,normalized

class RollingTests(unittest.TestCase):
    def test_complete_panel_precedes_window_selection_and_ties(self):
        start=date(2024,1,1)
        rows=[record(str(i),str(i),(start+timedelta(days=i)).isoformat(),{'a':i,'b':i+1,'c':i+2},'fixture') for i in range(60)]
        rows += [record('incomplete'+str(i),'x'+str(i),'2020-01-01',{'a':1},'fixture') for i in range(300)]
        p=prepare(panel('x','x','x','release',['a','b','c'],rows))
        self.assertEqual(len(p['rows']),60)
        ws=monthly_windows(p['base_dates']);self.assertTrue(all(len(w['bases'])>=50 for w in ws))
        self.assertEqual(ws[0]['date'],'2024-01-15')
        tied={str(i):'2024-01-01' for i in range(51)}
        self.assertEqual(len(monthly_windows(tied)[0]['bases']),51)

    def test_conflicts_and_zero_scores(self):
        a=record('a','a','2024-01-01',{'x':0,'y':1},'fixture')
        b=record('b','b','2024-01-01',{'x':1,'y':1},'fixture')
        rows,issues=complete_rows([a,a,b,dict(b,date='2024-02-01')],['x','y'])
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['scores']['x'],0)
        self.assertEqual(issues['conflicting_configurations'],1)

    def test_weighted_covariance_matches_literal_cluster_resampling(self):
        rng=np.random.default_rng(9);X=rng.normal(size=(6,4));weights=np.array([[2,2,0,3,3,1],[1,1,1,1,1,1]])
        axes,ev,gap,valid=weighted_axes(X,weights)
        for j,w in enumerate(weights):
            fit=pc1(np.repeat(X,w,axis=0));self.assertTrue(valid[j])
            self.assertAlmostEqual(abs(axes[j]@fit['weights']),1)
            self.assertAlmostEqual(ev[j],fit['explained_variance'])
            self.assertAlmostEqual(gap[j],fit['relative_gap'])

    def test_degenerate_bootstraps_are_rejected(self):
        X=np.zeros((8,3));axes,ev,gap,valid=weighted_axes(X,np.ones((4,8)))
        self.assertFalse(valid.any());self.assertTrue(np.isnan(axes).all())

    def test_selected_configuration_does_not_choose_best_score(self):
        rows=[]
        for i in range(25):
            rows += [record(f'{i}a',str(i),'2024-01-01',{'a':99,'b':90,'c':80},'fixture',priority=0),record(f'{i}z',str(i),'2024-02-01',{'a':1,'b':2,'c':3},'fixture',priority=1)]
        spec=panel('x','x','x','release',['a','b','c'],rows);spec['select_one']=True
        p=prepare(spec);self.assertTrue(all(r['model'].endswith('z') for r in p['rows']))
        self.assertEqual(set(p['base_dates'].values()),{'2024-01-01'})
        self.assertEqual(p['mode'],'whole-panel (20–49 dated bases)')

    def test_affine_units_do_not_change_fixed_scaled_axis(self):
        rng=np.random.default_rng(2);X=rng.normal(size=(80,4));Y=X*np.array([1,100,.01,3])+np.arange(4)
        z=lambda x:(x-x.mean(0))/x.std(0,ddof=1)
        self.assertAlmostEqual(abs(pc1(z(X)[:50])['weights']@pc1(z(Y)[:50])['weights']),1)

    def test_known_rotation_and_date_semantics(self):
        a=np.array([1.,0,0]);b=np.array([np.sqrt(3)/2,.5,0])
        self.assertAlmostEqual(similarity(a,b)['angle_degrees'],30)
        self.assertEqual(iso('2024-02-30'),'')
        self.assertEqual(iso('2024-03-01T12:00:00Z'),'2024-03-01')
        self.assertNotEqual(normalized('model high'),normalized('model low'))

if __name__=='__main__':unittest.main()
