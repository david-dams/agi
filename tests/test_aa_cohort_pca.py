import unittest
import numpy as np
from aa_cohort_pca import pc1,similarity


class CohortPCATests(unittest.TestCase):
    def test_sign_and_scalar_invariance_and_known_angle(self):
        a=np.array([1.,0.,0.]);b=np.array([1.,1.,0.])
        for v in (b,-b,4*b):
            s=similarity(a,v)
            self.assertAlmostEqual(s['angle_degrees'],45.)
            self.assertAlmostEqual(s['tucker_congruence'],2**-.5)
            self.assertEqual(s['cosine_similarity'],s['tucker_congruence'])
        with self.assertRaises(ValueError):similarity(a,np.zeros(3))

    def test_covariance_direction_uses_fixed_units_and_local_centering(self):
        # Exact covariance eigenvector differs from that of its correlation matrix.
        target=np.array([[9.,1.],[1.,1.]])
        Q=np.array([[1.,1.],[1.,-1.],[-1.,1.],[-1.,-1.]])*np.sqrt(3/4)
        X=Q@np.linalg.cholesky(target).T
        f=pc1(X);translated=pc1(X+[100,200])
        np.testing.assert_allclose(f['weights'],translated['weights'],atol=1e-12)
        expected=np.linalg.eigh(target)[1][:,-1]
        self.assertAlmostEqual(similarity(f['weights'],expected)['cosine_similarity'],1.)
        self.assertGreater(similarity(f['weights'],pc1(X/X.std(0,ddof=1))['weights'])['angle_degrees'],20)
        self.assertAlmostEqual(f['explained_variance'],np.linalg.eigvalsh(target)[-1]/10.)

    def test_singular_covariance_allowed_but_top_tie_rejected(self):
        x=np.arange(8.);X=np.column_stack([x,2*x,np.zeros(8)])
        f=pc1(X);self.assertEqual(f['rank'],1);self.assertEqual(f['constant_tasks'],1)
        self.assertAlmostEqual(f['explained_variance'],1.)
        with self.assertRaises(ValueError):pc1(np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]]))
        with self.assertRaises(ValueError):pc1(np.zeros((10,3)))
