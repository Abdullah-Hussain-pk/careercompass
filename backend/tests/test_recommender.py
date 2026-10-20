"""
CareerCompass – Unit tests for core recommendation engine logic.
Tests RIASEC scoring, cosine similarity, skill coverage, explanation ordering.
"""
import pytest
from app.services.assessment.scoring import normalise_score, compute_riasec_scores
from app.services.recommender.engine import (
    compute_interest_similarity,
    compute_skill_coverage,
    compute_degree_eligibility,
    compute_match_score,
    build_explanation,
    rank_careers,
)


# ── RIASEC Scoring (FR-4) ──────────────────────────────────────────────────

class TestNormaliseScore:
    """Tests for RIASEC score normalisation."""

    def test_all_ones_gives_zero(self):
        """All 1s → raw sum = 8 → normalised = 0."""
        assert normalise_score(8) == 0.0

    def test_all_fives_gives_hundred(self):
        """All 5s → raw sum = 40 → normalised = 100."""
        assert normalise_score(40) == 100.0

    def test_midpoint(self):
        """All 3s → raw sum = 24 → midpoint of 0-100 = 50."""
        assert normalise_score(24) == pytest.approx(50.0, abs=1e-2)

    def test_clamp_below_zero(self):
        """Raw sum below min is clamped to 0."""
        assert normalise_score(0) == 0.0

    def test_clamp_above_max(self):
        """Raw sum above max is clamped to 100."""
        assert normalise_score(99) == 100.0


class TestComputeRIASECScores:
    """Tests for batch RIASEC type scoring."""

    def test_all_types_present(self):
        answers = {t: [3, 3, 3, 3, 3, 3, 3, 3] for t in "RIASEC"}
        scores = compute_riasec_scores(answers)
        assert set(scores.keys()) == set("RIASEC")
        for v in scores.values():
            assert v == pytest.approx(50.0, abs=1e-2)

    def test_missing_type_gives_zero(self):
        scores = compute_riasec_scores({})
        assert all(v == 0.0 for v in scores.values())

    def test_mixed_scores(self):
        answers = {
            "R": [1, 1, 1, 1, 1, 1, 1, 1],  # all 1s → 0
            "I": [5, 5, 5, 5, 5, 5, 5, 5],  # all 5s → 100
            "A": [3, 3, 3, 3, 3, 3, 3, 3],  # all 3s → 50
            "S": [3, 3, 3, 3, 3, 3, 3, 3],
            "E": [3, 3, 3, 3, 3, 3, 3, 3],
            "C": [3, 3, 3, 3, 3, 3, 3, 3],
        }
        scores = compute_riasec_scores(answers)
        assert scores["R"] == 0.0
        assert scores["I"] == 100.0
        assert scores["A"] == pytest.approx(50.0, abs=1e-2)


# ── Interest Similarity (cosine) ───────────────────────────────────────────

class TestInterestSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_vectors_give_one(self):
        v = [80, 70, 50, 40, 60, 30]
        assert compute_interest_similarity(v, v) == pytest.approx(1.0, abs=1e-6)

    def test_zero_vector_gives_zero(self):
        v = [80, 70, 50, 40, 60, 30]
        z = [0, 0, 0, 0, 0, 0]
        assert compute_interest_similarity(v, z) == 0.0
        assert compute_interest_similarity(z, v) == 0.0

    def test_orthogonal_vectors(self):
        """These specific non-negative vectors are not truly orthogonal;
        but with negative cosine clamped we should get >= 0."""
        v1 = [100, 0, 0, 0, 0, 0]
        v2 = [0, 100, 0, 0, 0, 0]
        sim = compute_interest_similarity(v1, v2)
        assert sim == pytest.approx(0.0, abs=1e-6)

    def test_partial_overlap(self):
        v1 = [100, 50, 0, 0, 0, 0]
        v2 = [50, 100, 0, 0, 0, 0]
        sim = compute_interest_similarity(v1, v2)
        assert 0.0 < sim < 1.0

    def test_symmetric(self):
        v1 = [60, 80, 50, 40, 30, 20]
        v2 = [70, 75, 55, 45, 35, 25]
        assert compute_interest_similarity(v1, v2) == pytest.approx(
            compute_interest_similarity(v2, v1), abs=1e-6
        )


# ── Skill Coverage ─────────────────────────────────────────────────────────

class TestSkillCoverage:
    """Tests for skill coverage formula."""

    def test_full_coverage(self):
        """Student meets all required skill levels exactly."""
        ratings = {"sk-a": 4, "sk-b": 3}
        reqs = [{"skill_id": "sk-a", "required_level": 4},
                {"skill_id": "sk-b", "required_level": 3}]
        assert compute_skill_coverage(ratings, reqs) == pytest.approx(1.0)

    def test_zero_coverage(self):
        """Student has none of the required skills."""
        ratings = {}
        reqs = [{"skill_id": "sk-a", "required_level": 4},
                {"skill_id": "sk-b", "required_level": 3}]
        assert compute_skill_coverage(ratings, reqs) == pytest.approx(0.0)

    def test_partial_coverage(self):
        """Student meets half of total required levels."""
        ratings = {"sk-a": 2, "sk-b": 0}
        reqs = [{"skill_id": "sk-a", "required_level": 4},
                {"skill_id": "sk-b", "required_level": 4}]
        # earned = min(2,4) + min(0,4) = 2; total = 8; coverage = 2/8 = 0.25
        assert compute_skill_coverage(ratings, reqs) == pytest.approx(0.25)

    def test_over_qualified_capped(self):
        """Student has higher rating than required – capped at required."""
        ratings = {"sk-a": 5}
        reqs = [{"skill_id": "sk-a", "required_level": 3}]
        # earned = min(5,3) = 3; total = 3; coverage = 1.0
        assert compute_skill_coverage(ratings, reqs) == pytest.approx(1.0)

    def test_no_requirements_returns_one(self):
        """Career with no required skills → coverage is 1.0 (trivially met)."""
        assert compute_skill_coverage({}, []) == 1.0

    def test_cold_start_no_ratings(self):
        """Cold-start: empty ratings → 0 coverage."""
        reqs = [{"skill_id": "sk-a", "required_level": 4}]
        assert compute_skill_coverage({}, reqs) == pytest.approx(0.0)


# ── Degree Eligibility ─────────────────────────────────────────────────────

class TestDegreeEligibility:
    """Tests for degree eligibility scoring."""

    def test_eligible_degree(self):
        assert compute_degree_eligibility("deg-cs", ["deg-cs", "deg-se"]) == 1.0

    def test_ineligible_degree_default_penalty(self):
        result = compute_degree_eligibility("deg-other", ["deg-cs"])
        assert result == pytest.approx(0.6)

    def test_ineligible_degree_custom_penalty(self):
        result = compute_degree_eligibility("deg-other", ["deg-cs"], not_eligible_penalty=0.4)
        assert result == pytest.approx(0.4)

    def test_no_degree_cold_start(self):
        """Student without a degree → neutral (1.0, no penalty)."""
        assert compute_degree_eligibility(None, ["deg-cs"]) == 1.0

    def test_career_no_degree_restriction(self):
        """Career with no eligible degrees → always 1.0."""
        assert compute_degree_eligibility("deg-cs", []) == 1.0


# ── Match Score ────────────────────────────────────────────────────────────

class TestMatchScore:
    """Tests for final weighted match score (0-100 scale)."""

    def test_perfect_match(self):
        """All components are 1.0 → score = 100."""
        score = compute_match_score(1.0, 1.0, 1.0, 0.5, 0.3, 0.2)
        assert score == pytest.approx(100.0)

    def test_zero_match(self):
        """All components are 0 → score = 0."""
        score = compute_match_score(0.0, 0.0, 0.0, 0.5, 0.3, 0.2)
        assert score == pytest.approx(0.0)

    def test_weights_applied(self):
        """Only interest = 1.0, others = 0. Score = w1 * 100 = 50."""
        score = compute_match_score(1.0, 0.0, 0.0, 0.5, 0.3, 0.2)
        assert score == pytest.approx(50.0)

    def test_clamped_to_100(self):
        """Result cannot exceed 100."""
        score = compute_match_score(1.5, 1.5, 1.5, 0.5, 0.3, 0.2)
        assert score == 100.0


# ── Weight Normalisation ───────────────────────────────────────────────────

class TestWeightNormalisation:
    """Tests that weights must sum to 1.0 (via Pydantic schema)."""

    def test_weights_must_sum_to_one(self):
        from app.schemas.schemas import WeightsUpdate
        import pytest
        with pytest.raises(Exception):
            WeightsUpdate(w1=0.5, w2=0.4, w3=0.4)  # sums to 1.3

    def test_valid_weights(self):
        from app.schemas.schemas import WeightsUpdate
        w = WeightsUpdate(w1=0.5, w2=0.3, w3=0.2)
        assert w.w1 + w.w2 + w.w3 == pytest.approx(1.0)


# ── Explanation Top-3 Ordering ─────────────────────────────────────────────

class TestExplanation:
    """Tests that explanation returns top-3 sentences ordered by contribution."""

    def test_returns_three_sentences(self):
        sentences = build_explanation(
            career_title="Software Engineer",
            career_riasec=[30, 80, 40, 40, 60, 60],
            student_riasec=[25, 85, 35, 45, 65, 55],
            interest_similarity=0.98,
            skill_coverage=0.9,
            degree_eligibility=1.0,
            interest_contribution=0.49,
            skill_contribution=0.27,
            degree_contribution=0.20,
            student_degree_id="deg-cs",
            eligible_degree_ids=["deg-cs"],
            is_cold_start=False,
        )
        assert len(sentences) == 3
        assert all(isinstance(s, str) and len(s) > 10 for s in sentences)

    def test_cold_start_flagged_in_explanation(self):
        """Cold-start path produces a note about no skills rated."""
        sentences = build_explanation(
            career_title="Test Career",
            career_riasec=[50, 50, 50, 50, 50, 50],
            student_riasec=[50, 50, 50, 50, 50, 50],
            interest_similarity=1.0,
            skill_coverage=0.0,
            degree_eligibility=1.0,
            interest_contribution=0.5,
            skill_contribution=0.0,
            degree_contribution=0.2,
            student_degree_id=None,
            eligible_degree_ids=[],
            is_cold_start=True,
        )
        assert any("cold-start" in s.lower() or "no skills" in s.lower() or "rate" in s.lower()
                   for s in sentences)


# ── Full Rank Careers ──────────────────────────────────────────────────────

class TestRankCareers:
    """Integration tests for the ranking function."""

    def _make_career(self, cid, r=50, i=50, a=50, s=50, e=50, c=50, skills=None):
        return {
            "id": cid,
            "title": f"Career {cid}",
            "r_score": r, "i_score": i, "a_score": a,
            "s_score": s, "e_score": e, "c_score": c,
            "required_skills": skills or [],
            "eligible_degree_ids": ["deg-cs"],
        }

    def test_returns_top_n(self):
        careers = [self._make_career(f"c{i}") for i in range(20)]
        results = rank_careers([50]*6, {}, "deg-cs", careers, 0.5, 0.3, 0.2, top_n=10)
        assert len(results) == 10

    def test_sorted_descending(self):
        careers = [
            self._make_career("high", i=100),
            self._make_career("low",  i=0),
        ]
        results = rank_careers([0, 100, 0, 0, 0, 0], {}, None, careers, 0.5, 0.3, 0.2)
        assert results[0]["career_id"] == "high"

    def test_cold_start_flag(self):
        """Cold-start: no skill ratings → is_cold_start=True in explanation."""
        careers = [self._make_career("c1", skills=[{"skill_id": "sk-a", "required_level": 4}])]
        results = rank_careers([50]*6, {}, None, careers, 0.5, 0.3, 0.2)
        assert results[0]["factor_breakdown"]["is_cold_start"] is True

    def test_variant_interest_only(self):
        """interest_only variant should use full score from interest, not skill."""
        careers = [self._make_career("c1")]
        results = rank_careers(
            [50]*6, {"sk-a": 1}, None, careers,
            0.5, 0.3, 0.2, variant="interest_only"
        )
        fb = results[0]["factor_breakdown"]
        assert fb["skill_contribution"] == pytest.approx(0.0)
        assert fb["degree_contribution"] == pytest.approx(0.0)
