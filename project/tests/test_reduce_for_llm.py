"""
Tests for reduce_for_llm.py

Covers status classification and cluster reduction to LLM-ready format.
"""
import pytest
from reduce_for_llm import classify_status, reduce_cluster_for_llm


# ---------------------------------------------------------------------------
# classify_status
# ---------------------------------------------------------------------------

class TestClassifyStatus:
    def _cluster(self, platform="github", handle="Yogscast", features=None, urls=None):
        if features is None:
            features = [
                {"feature": "profile_url", "delta": 0.10, "label": "Profile-like URL structure"},
                {"feature": "exact_handle_match", "delta": 0.30, "label": "Exact handle match"},
            ]
        return {
            "platform": platform,
            "handle": handle,
            "urls": urls or [],
            "score_features": features,
        }

    def test_archive_is_search_or_tooling(self):
        assert classify_status(self._cluster(platform="archive", features=[])) == "search_or_tooling"

    def test_wikimedia_is_search_or_tooling(self):
        assert classify_status(self._cluster(platform="wikimedia", features=[])) == "search_or_tooling"

    def test_discord_is_invite_or_redirect(self):
        assert classify_status(self._cluster(platform="discord", features=[])) == "invite_or_redirect"

    def test_profile_like_reason_gives_candidate_profile(self):
        features = [
            {"feature": "base_score", "delta": 0.20, "label": "Base score"},
            {"feature": "profile_url", "delta": 0.10, "label": "Profile-like URL structure"},
            {"feature": "exact_handle_match", "delta": 0.30, "label": "Exact handle match"},
        ]
        assert classify_status(self._cluster(features=features)) == "candidate_profile"

    def test_non_profile_like_reason_gives_search_or_tooling(self):
        features = [
            {"feature": "base_score", "delta": 0.20, "label": "Base score"},
            {"feature": "non_profile_url", "delta": -0.15, "label": "Non-profile URL"},
        ]
        assert classify_status(self._cluster(features=features)) == "search_or_tooling"

    def test_handle_with_no_profile_feature_gives_candidate_profile(self):
        # Has a handle but no profile_url feature — falls back to handle check
        features = [
            {"feature": "base_score", "delta": 0.20, "label": "Base score"},
            {"feature": "exact_handle_match", "delta": 0.30, "label": "Exact handle match"},
        ]
        assert classify_status(self._cluster(handle="Yogscast", features=features)) == "candidate_profile"

    def test_no_handle_no_signals_gives_unknown(self):
        cluster = {"platform": "github", "handle": None, "urls": [], "score_features": []}
        assert classify_status(cluster) == "unknown_pattern"

    def test_empty_platform_still_classifies(self):
        cluster = {"platform": None, "handle": "Yogscast", "urls": [], "score_features": []}
        # Has a handle so should be candidate_profile
        assert classify_status(cluster) == "candidate_profile"


# ---------------------------------------------------------------------------
# reduce_cluster_for_llm
# ---------------------------------------------------------------------------

class TestReduceClusterForLlm:
    def _cluster(self, platform="github", key="yogscast", handle="Yogscast",
                 confidence=0.9, features=None, accounts=None, urls=None):
        if accounts is None:
            accounts = [
                {
                    "signals": [
                        {"module": "sfp_accounts", "from_event": "ACCOUNT_EXTERNAL_OWNED", "source": "Yogscast"}
                    ]
                }
            ]
        if features is None:
            features = [
                {"feature": "profile_url", "delta": 0.10, "label": "Profile-like URL structure"},
                {"feature": "exact_handle_match", "delta": 0.30, "label": "Exact handle match"},
            ]
        return {
            "platform": platform,
            "key": key,
            "handle": handle,
            "confidence": confidence,
            "score_features": features,
            "source_reliability": "high",
            "accounts": accounts,
            "urls": urls or ["https://github.com/Yogscast"],
        }

    def test_returns_required_fields(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster())
        for field in ("target", "cluster_id", "platform", "handle", "key", "urls",
                      "signals", "event_types", "sources", "heuristic_score",
                      "score_features", "source_reliability", "status", "account_count"):
            assert field in result, f"Missing field: {field}"

    def test_cluster_id_format(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster(platform="github", key="yogscast"))
        assert result["cluster_id"] == "github:yogscast"

    def test_heuristic_score_preserved(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster(confidence=0.85))
        assert result["heuristic_score"] == 0.85

    def test_signals_extracted_from_accounts(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster())
        assert "sfp_accounts" in result["signals"]

    def test_event_types_extracted(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster())
        assert "ACCOUNT_EXTERNAL_OWNED" in result["event_types"]

    def test_account_count_correct(self):
        cluster = self._cluster(accounts=[{"signals": []}, {"signals": []}])
        result = reduce_cluster_for_llm("Yogscast", cluster)
        assert result["account_count"] == 2

    def test_target_preserved(self):
        result = reduce_cluster_for_llm("Yogscast", self._cluster())
        assert result["target"] == "Yogscast"

    def test_urls_preserved(self):
        urls = ["https://github.com/Yogscast", "https://github.com/Yogscast/repo"]
        result = reduce_cluster_for_llm("Yogscast", self._cluster(urls=urls))
        assert result["urls"] == urls

    def test_signals_sorted(self):
        accounts = [
            {"signals": [{"module": "sfp_z", "from_event": "X", "source": "s"}]},
            {"signals": [{"module": "sfp_a", "from_event": "Y", "source": "s"}]},
        ]
        result = reduce_cluster_for_llm("Yogscast", self._cluster(accounts=accounts))
        assert result["signals"] == sorted(result["signals"])

    def test_empty_accounts_give_zero_count(self):
        cluster = self._cluster(accounts=[])
        result = reduce_cluster_for_llm("Yogscast", cluster)
        assert result["account_count"] == 0

    def test_deduplicated_modules(self):
        # Same module in multiple accounts should only appear once
        accounts = [
            {"signals": [{"module": "sfp_accounts", "from_event": "X", "source": "s"}]},
            {"signals": [{"module": "sfp_accounts", "from_event": "X", "source": "s"}]},
        ]
        result = reduce_cluster_for_llm("Yogscast", self._cluster(accounts=accounts))
        assert result["signals"].count("sfp_accounts") == 1
