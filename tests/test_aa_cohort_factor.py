import unittest
import numpy as np
from aa_cohort_factor import identity, effort, metric_invariance


class CohortTests(unittest.TestCase):
    def test_setting_removed_but_release_version_preserved(self):
        m=dict(name="Model (Sep '25) (Reasoning)", modelCreatorName='Lab',isReasoning=True)
        self.assertEqual(identity(m), "Lab/Model (Sep '25)")
        self.assertNotEqual(identity(m),identity(dict(m,name="Model (Aug '25) (Reasoning)")))
        self.assertEqual(identity(dict(m,name='Model (high)')),identity(dict(m,name='Model (low)')))
        self.assertGreater(effort(dict(m,name='Model (xhigh)')),effort(dict(m,name='Model (high)')))

    def test_metric_test_allows_different_factor_variances(self):
        # Exact sample covariances isolate metric constraints from sampling noise.
        rng=np.random.default_rng(29);p=5;n=1200;Q=np.linalg.qr(rng.normal(size=(n,p+1)))[0]
        Q=Q-Q.mean(0);Q=Q@np.linalg.inv(np.linalg.cholesky(Q.T@Q)).T*np.sqrt(n-1)
        lam=np.array([.7,.6,.8,.5,.65]);matrices=[]
        for phi in (.5,1.,2.):
            S=phi*np.outer(lam,lam)+np.diag([.4,.6,.3,.7,.5])
            matrices.append(Q[:,:p]@np.linalg.cholesky(S).T)
        result=metric_invariance(matrices)
        self.assertLess(result['delta_chi2'],.01)
        changed=[x.copy() for x in matrices];changed[2][:,1]*=1.8
        self.assertGreater(metric_invariance(changed)['delta_chi2'],20)
