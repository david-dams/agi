from collections import Counter
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from scipy.special import expit

import factor_models as factors
import public_gai_factor as public


def hierarchy_covariance():
    groups = [list(range(0, 3)), list(range(3, 6)), list(range(6, 9))]
    loadings = np.zeros((9, 3))
    for k, members in enumerate(groups):
        loadings[members, k] = [.65, .75, .8]
    gamma = np.array([.55, .7, .8])
    phi = np.outer(gamma, gamma)
    np.fill_diagonal(phi, 1)
    R = loadings @ phi @ loadings.T + np.diag(1 - np.sum(loadings ** 2, axis=1))
    return R, groups, loadings, gamma


class FactorTests(unittest.TestCase):
    def test_recovers_one_factor_and_reliability(self):
        lam = np.array([.55, .65, .75, .8, .85])
        R = np.outer(lam, lam) + np.diag(1 - lam ** 2)
        fit = factors.fit_higher_order(R, 500, [list(range(5))])
        np.testing.assert_allclose(fit.standardized_g, lam, atol=2e-4)
        self.assertAlmostEqual(fit.g_variance_share, np.mean(lam ** 2), places=4)
        self.assertAlmostEqual(fit.omega_h, lam.sum() ** 2 / R.sum(), places=4)
        self.assertNotAlmostEqual(fit.omega_h, fit.g_variance_share, places=2)
        self.assertFalse(fit.boundary)

    def test_recovers_identified_three_group_model(self):
        R, groups, loadings, gamma = hierarchy_covariance()
        fit = factors.fit_higher_order(R, 500, groups)
        np.testing.assert_allclose(fit.gamma, gamma, atol=2e-3)
        np.testing.assert_allclose(fit.standardized_g, loadings @ gamma, atol=2e-3)
        np.testing.assert_allclose(fit.sigma, R, atol=2e-4)
        self.assertLess(fit.residual_rms, 1e-4)

    def test_retains_negative_loading_and_positive_global_orientation(self):
        lam = np.array([-.4, .6, .7, .8])
        fit = factors.fit_higher_order(np.outer(lam, lam) + np.diag(1 - lam ** 2), 300, [list(range(4))])
        self.assertLess(fit.standardized_g[0], 0)
        self.assertGreater(fit.standardized_g.sum(), 0)

    def test_rejects_unidentified_or_invalid_inputs(self):
        R, _, _, _ = hierarchy_covariance()
        with self.assertRaisesRegex(ValueError, "two-group"):
            factors.fit_higher_order(R, 100, [list(range(4)), list(range(4, 9))])
        with self.assertRaisesRegex(ValueError, "three indicators"):
            factors.fit_higher_order(R, 100, [[0, 1], [2, 3, 4], [5, 6, 7, 8]])
        with self.assertRaisesRegex(ValueError, "positive definite"):
            factors.fit_higher_order(np.ones((4, 4)), 100, [list(range(4))])
        with self.assertRaisesRegex(ValueError, "constant"):
            factors.standardize(np.ones((10, 4)))

    def test_nonconvergence_is_not_a_fit(self):
        with patch.object(factors.optimize, "minimize", return_value=SimpleNamespace(success=False, fun=0)):
            with self.assertRaisesRegex(RuntimeError, "converged"):
                factors.fit_higher_order(np.eye(4), 100, [list(range(4))])

    def test_boundary_is_reported(self):
        R = np.full((4, 4), .99999)
        np.fill_diagonal(R, 1)
        self.assertTrue(factors.fit_higher_order(R, 100, [list(range(4))]).boundary)


class BootstrapTests(unittest.TestCase):
    def test_item_draws_preserve_identical_paired_responses(self):
        row = np.array([0., 1., .25, 1., 0.])
        items = [np.vstack([row, row, 1 - row]), np.vstack([row, row, .5 * row])]
        for seed in range(10):
            sampled = public.resample_items(items, np.random.default_rng(seed))
            np.testing.assert_array_equal(sampled[0], sampled[1])
            self.assertTrue(np.logical_and(sampled >= 0, sampled <= 1).all())

    def test_whole_family_is_resampled_as_one_cluster(self):
        for seed in range(10):
            counts = Counter(public.family_rows([[0, 1], [2, 3], [4]], np.random.default_rng(seed)))
            self.assertEqual(counts[0], counts[1])
            self.assertEqual(counts[2], counts[3])

    def test_intervals_withheld_below_ninety_percent(self):
        values = np.arange(20, dtype=float).reshape(10, 2)
        values[:2] = np.nan
        self.assertIsNone(public.intervals(values, 10))
        values[1] = [2, 3]
        self.assertEqual(public.intervals(values, 10).shape, (2, 2))

    def test_bootstrap_is_deterministic_and_does_not_change_groups(self):
        rng = np.random.default_rng(4)
        _, groups, _, _ = hierarchy_covariance()
        common = rng.normal(size=(55, 1))
        latent = .7 * common + np.sqrt(.51) * rng.normal(size=(55, 3))
        items = [expit(latent[:, j // 3, None] + rng.normal(size=(55, 50))) for j in range(9)]
        view = dict(items=items, scores=np.column_stack([a.mean(axis=1) for a in items]))
        clusters = [list(range(i, min(i + 2, 55))) for i in range(0, 55, 2)]
        before = [g[:] for g in groups]
        a, ad, _ = public.bootstrap(view, clusters, groups, 3, 0)
        b, bd, _ = public.bootstrap(view, clusters, groups, 3, 0)
        self.assertEqual(ad, bd)
        self.assertEqual(groups, before)
        for mode in a:
            for N in a[mode]:
                for key in a[mode][N]:
                    np.testing.assert_array_equal(a[mode][N][key], b[mode][N][key])



if __name__ == "__main__":
    unittest.main()
