import unittest
import numpy as np
from aa_pca_null import construct_null,minimum_rotation,transform_rows,consensus_axis,cluster_strata,resample_indices,tail_result


class SharedAxisNullTests(unittest.TestCase):
    def test_common_axis_is_leading_and_spectrum_sensitivity_is_exact(self):
        S=np.diag([8.,2.,1.]);u=np.array([np.cos(.2),np.sin(.2),0.])
        for method in ('projected','rotated_spectrum'):
            target=construct_null(S,u,method);values,vectors=np.linalg.eigh(target)
            self.assertGreater(values[0],0);self.assertAlmostEqual(abs(vectors[:,-1]@u),1.)
            self.assertAlmostEqual(np.trace(target),11.)
            if method=='rotated_spectrum':np.testing.assert_allclose(values,np.linalg.eigvalsh(S),atol=1e-12)
        with self.assertRaises(ValueError):construct_null(S,np.array([0.,0.,1.]),'projected')

    def test_rotations_and_empirical_covariance_preserve_expected_geometry(self):
        a=np.array([1.,0.,0.]);b=np.array([.8,.6,0.]);R=minimum_rotation(a,b)
        np.testing.assert_allclose(R@a,b,atol=1e-12);np.testing.assert_allclose(R@R.T,np.eye(3),atol=1e-12)
        rng=np.random.default_rng(5);X=rng.normal(size=(100,3))*[3.,1.,.5];X[1]=X[0]
        for method in ('projected','rotated_spectrum'):
            target=construct_null(np.cov(X,rowvar=False),b,method);Y=transform_rows(X,target,method,b)
            np.testing.assert_allclose(np.cov(Y,rowvar=False),target,atol=1e-10)
            np.testing.assert_allclose(Y[0],Y[1],atol=1e-12)
            if method=='rotated_spectrum':self.assertAlmostEqual(np.linalg.norm(X[2]-X[3]),np.linalg.norm(Y[2]-Y[3]))
        np.testing.assert_allclose(abs(consensus_axis([a,-a],[10,20])),a)

    def test_fixed_size_sampling_never_splits_clusters(self):
        members=[dict(base_cluster=k,cohort='2025H1',selected=str(j==0)) for k,n in [('a',2),('b',2),('c',1)] for j in range(n)]
        families,strata=cluster_strata(members)
        for seed in range(20):
            ix=resample_indices(families,strata,np.random.default_rng(seed),'fixed_sizes')
            self.assertEqual(len(ix),5);self.assertEqual(sum(members[i]['selected']=='True' for i in ix),3)
            for indices in families.values():self.assertEqual(len({ix.count(i) for i in indices}),1)

    def test_plus_one_p_and_mc_uncertainty(self):
        r=tail_result(np.arange(2000.),3000.,2000)
        self.assertEqual(r['exceedances'],0);self.assertEqual(r['p_calibrated'],1/2001)
        self.assertGreater(r['mc_exceedance_high'],0)
        r=tail_result([1.,np.nan],2.,2)
        self.assertIsNone(r['p_calibrated']);self.assertEqual(r['p_invalid_upper'],2/3)
