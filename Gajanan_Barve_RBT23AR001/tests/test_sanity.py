"""Textbook-behaviour checks: if these fail, either the code or our understanding is wrong."""
import numpy as np
import pytest
from sklearn.metrics import adjusted_rand_score as ari

from clustering import NOISE, run_dbscan, run_gmm, run_kmeans, suggest_eps
from data import make_shape
from metrics import agreement_matrix, external_metrics, internal_metrics


def test_kmeans_recovers_spherical_blobs():
    X, y = make_shape("blobs")
    assert ari(y, run_kmeans(X, 3).labels) > 0.9


def test_dbscan_beats_kmeans_on_moons():
    X, y = make_shape("moons")
    db = ari(y, run_dbscan(X, eps=0.3, min_samples=5).labels)
    km = ari(y, run_kmeans(X, 2).labels)
    assert db > 0.9
    assert km < 0.6 and db > km + 0.3


def test_dbscan_separates_concentric_circles_kmeans_cannot():
    X, y = make_shape("circles")
    assert ari(y, run_dbscan(X, eps=0.3, min_samples=5).labels) > 0.9
    assert ari(y, run_kmeans(X, 2).labels) < 0.2


def test_gmm_full_covariance_beats_kmeans_on_anisotropic_blobs():
    X, y = make_shape("aniso")
    assert ari(y, run_gmm(X, 3, "full").labels) > ari(y, run_kmeans(X, 3).labels) + 0.05


def test_gmm_exposes_soft_assignment_confidence():
    X, _ = make_shape("blobs")
    r = run_gmm(X, 3)
    assert r.confidence.shape == (len(X),) and 0.33 <= r.confidence.min() and r.confidence.max() <= 1.0


def test_dbscan_noise_is_minus_one_and_excluded_from_internal_metrics():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 0.1, (50, 2)), rng.normal(5, 0.1, (50, 2)), [[2.5, 2.5], [-3, 4]]])
    r = run_dbscan(X, eps=0.5, min_samples=5)
    assert (r.labels[-2:] == NOISE).all() and r.n_clusters == 2
    m = internal_metrics(X, r.labels)
    assert m["noise_fraction"] == pytest.approx(2 / 102) and m["silhouette"] > 0.9


def test_internal_metrics_nan_when_fewer_than_two_clusters():
    X, _ = make_shape("blobs")
    m = internal_metrics(X, np.zeros(len(X), dtype=int))
    assert np.isnan(m["silhouette"])


def test_external_metrics_penalise_noise_instead_of_hiding_it():
    y = np.array([0] * 50 + [1] * 50)
    perfect = external_metrics(y, y)
    all_noise = external_metrics(y, np.full(100, NOISE))
    assert perfect["ARI"] == 1.0 and all_noise["ARI"] == 0.0


def test_suggest_eps_is_in_a_sensible_range_for_moons():
    X, _ = make_shape("moons")
    assert 0.1 < suggest_eps(X, 5) < 0.6


def test_agreement_matrix_is_symmetric_with_unit_diagonal():
    X, _ = make_shape("blobs")
    m = agreement_matrix([run_kmeans(X, 3), run_gmm(X, 3), run_dbscan(X, 0.4, 5)])
    assert np.allclose(m.values, m.values.T) and np.allclose(np.diag(m.values), 1.0)
