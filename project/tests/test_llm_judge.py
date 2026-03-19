"""
Tests for llm_judge_gemini.py — pure logic only, no API calls.

Covers: dry-run judging, local noise classification, batch result validation,
post-adjustment capping, and confidence/verdict consistency.
"""
import pytest
from llm_judge_gemini import (
    clamp01,
    judge_cluster_dry,
    judge_cluster_local_noise,
    validate_batch_results,
    post_adjust_result,
    build_batch_prompt,
)


# ---------------------------------------------------------------------------
# clamp01
# ---------------------------------------------------------------------------

class TestClamp01:
    def test_clamps_above_one(self):
        assert clamp01(1.5) == 1.0

    def test_clamps_below_zero(self):
        assert clamp01(-0.5) == 0.0

    def test_passthrough_valid(self):
        assert clamp01(0.75) == 0.75

    def test_boundary_zero(self):
        assert clamp01(0.0) == 0.0

    def test_boundary_one(self):
        assert clamp01(1.0) == 1.0


# ---------------------------------------------------------------------------
# judge_cluster_dry
# ---------------------------------------------------------------------------

class TestJudgeClusterDry:
    def _cluster(self, platform="github", handle="Yogscast", score=0.9, status="candidate_profile"):
        return {
            "platform": platform,
            "handle": handle,
            "heuristic_score": score,
            "status": status,
        }

    def test_returns_required_keys(self):
        result = judge_cluster_dry("Yogscast", self._cluster())
        assert "final_confidence" in result
        assert "verdict" in result
        assert "rationale" in result
        assert "flags" in result

    def test_verdict_likely_for_high_score(self):
        result = judge_cluster_dry("Yogscast", self._cluster(score=0.9))
        assert result["verdict"] == "likely"

    def test_verdict_low_for_search_or_tooling(self):
        # dry judge deducts 0.25 for search_or_tooling; 0.6 - 0.25 = 0.35 → "low"
        result = judge_cluster_dry("Yogscast", self._cluster(score=0.6, status="search_or_tooling"))
        assert result["verdict"] == "low"

    def test_verdict_maybe_for_mid_score(self):
        result = judge_cluster_dry("Yogscast", self._cluster(score=0.6, status="candidate_profile"))
        assert result["verdict"] == "maybe"

    def test_confidence_clamped(self):
        result = judge_cluster_dry("Yogscast", self._cluster(score=0.0, status="search_or_tooling"))
        assert 0.0 <= result["final_confidence"] <= 1.0

    def test_invite_or_redirect_lowers_score(self):
        result_invite = judge_cluster_dry("Yogscast", self._cluster(score=0.8, status="invite_or_redirect"))
        result_normal = judge_cluster_dry("Yogscast", self._cluster(score=0.8, status="candidate_profile"))
        assert result_invite["final_confidence"] < result_normal["final_confidence"]


# ---------------------------------------------------------------------------
# judge_cluster_local_noise
# ---------------------------------------------------------------------------

class TestJudgeClusterLocalNoise:
    def _cluster(self, platform="discord", status="invite_or_redirect", score=0.5):
        return {"platform": platform, "status": status, "heuristic_score": score}

    def test_invite_or_redirect_is_low(self):
        result = judge_cluster_local_noise(self._cluster(status="invite_or_redirect"))
        assert result["verdict"] == "low"
        assert result["final_confidence"] <= 0.25

    def test_search_or_tooling_is_low(self):
        result = judge_cluster_local_noise(self._cluster(status="search_or_tooling"))
        assert result["verdict"] == "low"
        assert result["final_confidence"] <= 0.20

    def test_unknown_pattern_is_low(self):
        result = judge_cluster_local_noise(self._cluster(status="unknown_pattern"))
        assert result["verdict"] == "low"

    def test_no_matching_status_returns_fallback(self):
        result = judge_cluster_local_noise(self._cluster(status="candidate_profile", score=0.8))
        assert "final_confidence" in result
        assert result["final_confidence"] >= 0.0

    def test_result_has_flags(self):
        result = judge_cluster_local_noise(self._cluster(status="invite_or_redirect"))
        assert isinstance(result["flags"], list)


# ---------------------------------------------------------------------------
# validate_batch_results
# ---------------------------------------------------------------------------

class TestValidateBatchResults:
    def _valid_result(self, confidence=0.9, verdict="likely"):
        return {
            "final_confidence": confidence,
            "verdict": verdict,
            "rationale": "Looks good.",
            "flags": [],
        }

    def test_valid_batch_passes(self):
        batch = [self._valid_result(), self._valid_result(0.5, "maybe")]
        result = validate_batch_results(batch, 2)
        assert len(result) == 2

    def test_wrong_length_raises(self):
        batch = [self._valid_result()]
        with pytest.raises(ValueError, match="returned 1 results for batch size 2"):
            validate_batch_results(batch, 2)

    def test_not_a_list_raises(self):
        with pytest.raises(ValueError, match="not a list"):
            validate_batch_results({"error": "oops"}, 1)

    def test_missing_required_key_raises(self):
        bad = {"final_confidence": 0.9, "verdict": "likely"}  # missing rationale
        with pytest.raises(ValueError, match="missing keys"):
            validate_batch_results([bad], 1)

    def test_invalid_verdict_coerced_to_low(self):
        bad_verdict = {**self._valid_result(), "verdict": "unsure"}
        result = validate_batch_results([bad_verdict], 1)
        assert result[0]["verdict"] == "low"

    def test_confidence_clamped_above_one(self):
        over = {**self._valid_result(), "final_confidence": 2.5}
        result = validate_batch_results([over], 1)
        assert result[0]["final_confidence"] == 1.0

    def test_confidence_clamped_below_zero(self):
        under = {**self._valid_result(), "final_confidence": -1.0}
        result = validate_batch_results([under], 1)
        assert result[0]["final_confidence"] == 0.0

    def test_flags_coerced_to_list(self):
        non_list_flags = {**self._valid_result(), "flags": "some_flag"}
        result = validate_batch_results([non_list_flags], 1)
        assert isinstance(result[0]["flags"], list)

    def test_none_item_raises(self):
        with pytest.raises(ValueError, match="not an object"):
            validate_batch_results([None], 1)

    def test_empty_batch(self):
        result = validate_batch_results([], 0)
        assert result == []


# ---------------------------------------------------------------------------
# post_adjust_result
# ---------------------------------------------------------------------------

class TestPostAdjustResult:
    def _cluster(self, platform="github", trust="high", status="candidate_profile", urls=None):
        return {
            "platform": platform,
            "platform_trust": trust,
            "status": status,
            "urls": urls or ["https://github.com/Yogscast"],
        }

    def _result(self, confidence=0.9, verdict="likely"):
        return {"final_confidence": confidence, "verdict": verdict, "rationale": "test", "flags": []}

    def test_search_or_tooling_capped_at_020(self):
        cluster = self._cluster(status="search_or_tooling")
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.20
        assert result["verdict"] == "low"

    def test_invite_or_redirect_capped_at_020(self):
        cluster = self._cluster(status="invite_or_redirect")
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.20

    def test_unknown_trust_capped_below_likely(self):
        cluster = self._cluster(trust="unknown")
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.74

    def test_adult_platform_capped(self):
        cluster = self._cluster(platform="fansly", trust="low", status="candidate_profile",
                                urls=["https://fansly.com/Yogscast"])
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.40

    def test_periscope_capped(self):
        cluster = self._cluster(platform="periscope", trust="low", status="candidate_profile",
                                urls=["https://periscope.tv/Yogscast"])
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.50

    def test_high_trust_profile_unchanged(self):
        cluster = self._cluster(platform="github", trust="high", status="candidate_profile")
        result = post_adjust_result(cluster, self._result(confidence=0.85))
        assert result["final_confidence"] == 0.85
        assert result["verdict"] == "likely"

    def test_verdict_recomputed_after_cap(self):
        cluster = self._cluster(trust="unknown")
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        # Score was capped to 0.70, so verdict should be "maybe"
        assert result["verdict"] == "maybe"

    def test_tip_url_capped(self):
        cluster = self._cluster(urls=["https://somesite.com/Yogscast/tip"])
        result = post_adjust_result(cluster, self._result(confidence=0.9))
        assert result["final_confidence"] <= 0.70


# ---------------------------------------------------------------------------
# build_batch_prompt
# ---------------------------------------------------------------------------

class TestBuildBatchPrompt:
    def test_contains_target(self):
        prompt = build_batch_prompt("Yogscast", [{"platform": "github", "handle": "Yogscast"}])
        assert "Yogscast" in prompt

    def test_contains_json_clusters(self):
        prompt = build_batch_prompt("Yogscast", [{"platform": "github"}])
        assert "github" in prompt

    def test_returns_string(self):
        prompt = build_batch_prompt("Yogscast", [])
        assert isinstance(prompt, str)
        assert len(prompt) > 0
