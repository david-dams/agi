import unittest
import numpy as np
from aa_residual_cfa import residual_fit


class DomainResidualTests(unittest.TestCase):
    def test_recovers_known_covariance_and_allows_factor_variance_change(self):
        lam=np.array([.7,.6,.8,.65,.5,.55]);theta=np.diag([.5,.4,.3,.45,.5,.6]);theta[1,2]=theta[2,1]=.15
        covs=[v*np.outer(lam,lam)+theta for v in (.5,1.,2.)]
        independent=residual_fit([covs[1]],[1000],[])
        fit=residual_fit([covs[1]],[1000],[[1,2]])
        self.assertLess(fit['chi2'],.001)
        self.assertGreater(independent['chi2']-fit['chi2'],10)
        got=np.array(fit['groups'][0]['residual_covariance'])
        self.assertAlmostEqual(got[1,2],.15,places=3)
        self.assertAlmostEqual(got[0,3],0.)
        free=residual_fit(covs,[1000]*3,[[1,2]])
        equal=residual_fit(covs,[1000]*3,[[1,2]],True)
        self.assertLess(equal['chi2']-free['chi2'],.01)
        changed=[s.copy() for s in covs];scale=np.diag([1,1,1,1,1.7,1]);changed[2]=scale@changed[2]@scale
        self.assertGreater(residual_fit(changed,[1000]*3,[[1,2]],True)['chi2']-residual_fit(changed,[1000]*3,[[1,2]])['chi2'],10)

    def test_rejects_singular_inputs_and_overlapping_blocks(self):
        with self.assertRaises(ValueError):residual_fit([np.ones((6,6))],[100],[])
        with self.assertRaises(ValueError):residual_fit([np.eye(6)],[100],[[0,1],[1,2]])

    def test_three_task_block_and_negative_coding_residual(self):
        lam=np.linspace(.5,.8,9);theta=np.diag(np.linspace(.4,.6,9))
        theta[0,1]=theta[1,0]=.08
        theta[0,2]=theta[2,0]=-.07
        theta[1,2]=theta[2,1]=.06
        theta[6,8]=theta[8,6]=-.12
        S=np.outer(lam,lam)+theta
        f=residual_fit([S],[1500],[[0,1,2],[6,8]])
        self.assertLess(f['chi2'],.001)
        self.assertEqual(f['df'],23)
        np.testing.assert_allclose(f['groups'][0]['residual_covariance'],theta,atol=1e-3)
