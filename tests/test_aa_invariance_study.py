import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from aa_invariance_study import null_transform,summarize
from aa_residual_cfa import residual_fit


class InvarianceTests(unittest.TestCase):
    def test_partial_release_recovers_specific_loading_change(self):
        lam=np.array([.7,.6,.8,.65,.5,.55]);theta=np.eye(6)*.5;covs=[]
        for g in range(3):
            l=lam.copy();l[4]+=.25*g;covs.append(np.outer(l,l)+theta)
        free=residual_fit(covs,[800]*3,[])
        equal=residual_fit(covs,[800]*3,[],True,initial_fit=free)
        partial=residual_fit(covs,[800]*3,[],True,[4],initial_fit=free)
        self.assertGreater(equal['chi2']-free['chi2'],30)
        self.assertLess(partial['chi2']-free['chi2'],.01)
        self.assertEqual(partial['df']-free['df'],8)
        alternate=residual_fit(covs,[800]*3,[],marker=3,initial_fit=free)
        self.assertAlmostEqual(free['chi2'],alternate['chi2'],places=3)
        for a,b in zip(free['groups'],alternate['groups']):np.testing.assert_allclose(a['sigma'],b['sigma'],atol=1e-4)

    def test_null_recoloring_exactly_matches_covariance(self):
        rng=np.random.default_rng(29);X=rng.normal(size=(100,5));A=rng.normal(size=(5,5));target=A@A.T+np.eye(5)
        Y=null_transform(X,target)
        np.testing.assert_allclose(np.cov(Y,rowvar=False),target,atol=1e-10)
        np.testing.assert_allclose(Y.mean(0),0,atol=1e-10)
        # Identical within-family row differences remain identical after the same linear map.
        X[1]=X[0];Y=null_transform(X,target);np.testing.assert_allclose(Y[1],Y[0])

    def test_boundary_reporting_is_not_silent_deletion(self):
        values=np.linspace(-.1,0,100);status=np.array(['ok']*89+['boundary']*11)
        r=summarize(values,status,-.05)
        self.assertIsNone(r['low']);self.assertEqual(r['finite'],100);self.assertEqual(r['admissible'],89)
        self.assertIsNotNone(r['finite_low'])

    def test_rejects_optimizer_success_without_stationarity(self):
        lam=np.array([.7,.6,.8,.65,.5,.55]);S=np.outer(lam,lam)+np.eye(6)*.5
        initial=residual_fit([S],[800],[])
        def false_success(objective,x,**kwargs):
            return SimpleNamespace(x=x,fun=1.,jac=np.full_like(x,1e4),success=True,nit=1)
        with patch('aa_residual_cfa.optimize.minimize',side_effect=false_success):
            with self.assertRaises(RuntimeError):
                residual_fit([S],[800],[],initial_fit=initial)
