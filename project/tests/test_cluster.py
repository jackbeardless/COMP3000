"""
Tests for cluster.py

Covers handle normalisation, handle extraction, profile-like detection,
account scoring, and the full cluster_accounts pipeline.
"""
import pytest
from cluster import (
    normalized_handle,
    extract_handle,
    is_profile_like,
    score_account,
    cluster_accounts,
    platform_guess,
    HIGH_SIGNAL_PLATFORMS,
    LOW_SIGNAL_PLATFORMS,
)


# ---------------------------------------------------------------------------
# normalized_handle
# ---------------------------------------------------------------------------

class TestNormalizedHandle:
    def test_lowercases(self):
        assert normalized_handle("Yogscast") == "yogscast"

    def test_strips_special_chars(self):
        assert normalized_handle("yogs cast!") == "yogscast"

    def test_keeps_dots_dashes_underscores(self):
        assert normalized_handle("yogs.cast_test-1") == "yogs.cast_test-1"

    def test_empty_string(self):
        assert normalized_handle("") == ""

    def test_numbers_kept(self):
        assert normalized_handle("user123") == "user123"


# ---------------------------------------------------------------------------
# platform_guess
# ---------------------------------------------------------------------------

class TestPlatformGuess:
    def test_uses_platform_field_when_present(self):
        assert platform_guess("https://anything.com/foo", "github") == "github"

    def test_infers_from_url_when_no_field(self):
        assert platform_guess("https://github.com/foo", None) == "github"

    def test_www_stripped_for_lookup(self):
        assert platform_guess("https://www.reddit.com/user/foo", None) == "reddit"

    def test_unknown_for_unrecognised_domain(self):
        assert platform_guess("https://unknownsite.xyz/foo", None) == "unknown"


# ---------------------------------------------------------------------------
# extract_handle
# ---------------------------------------------------------------------------

class TestExtractHandle:
    def test_github(self):
        assert extract_handle("github", "https://github.com/Yogscast") == "Yogscast"

    def test_reddit(self):
        assert extract_handle("reddit", "https://reddit.com/user/Yogscast") == "Yogscast"

    def test_reddit_no_prefix_returns_none(self):
        assert extract_handle("reddit", "https://reddit.com/Yogscast") is None

    def test_lastfm(self):
        assert extract_handle("lastfm", "https://last.fm/user/Yogscast") == "Yogscast"

    def test_lastfm_no_user_prefix_returns_none(self):
        assert extract_handle("lastfm", "https://last.fm/Yogscast") is None

    def test_steam_id(self):
        assert extract_handle("steam", "https://steamcommunity.com/id/Yogscast") == "Yogscast"

    def test_steam_profiles(self):
        assert extract_handle("steam", "https://steamcommunity.com/profiles/76561198000000000") == "76561198000000000"

    def test_steam_no_prefix_returns_none(self):
        assert extract_handle("steam", "https://steamcommunity.com/Yogscast") is None

    def test_pastebin(self):
        assert extract_handle("pastebin", "https://pastebin.com/u/Yogscast") == "Yogscast"

    def test_chess(self):
        assert extract_handle("chess", "https://chess.com/member/Yogscast") == "Yogscast"

    def test_disqus(self):
        assert extract_handle("disqus", "https://disqus.com/by/Yogscast") == "Yogscast"

    def test_stackoverflow_with_display_name(self):
        result = extract_handle("stackoverflow", "https://stackoverflow.com/users/12345/yogscast")
        assert result == "yogscast"

    def test_stackoverflow_filter_returns_none(self):
        assert extract_handle("stackoverflow", "https://stackoverflow.com/users/filter") is None

    def test_discord_returns_none(self):
        # Discord URLs are invite codes, not user profiles
        assert extract_handle("discord", "https://discord.com/invite/ABCDEF") is None

    def test_archive_returns_none(self):
        assert extract_handle("archive", "https://web.archive.org/web/20200101/https://example.com") is None

    def test_no_path_returns_none(self):
        assert extract_handle("github", "https://github.com") is None

    def test_truckersmp_search_returns_none(self):
        assert extract_handle("truckersmp", "https://truckersmp.com/user/search") is None

    def test_kongregate(self):
        assert extract_handle("kongregate", "https://kongregate.com/accounts/Yogscast") == "Yogscast"

    def test_zepeto(self):
        result = extract_handle("zepeto", "https://web.zepeto.me/share/user/profile/Yogscast")
        assert result == "Yogscast"

    def test_zepeto_wrong_structure_returns_none(self):
        assert extract_handle("zepeto", "https://web.zepeto.me/Yogscast") is None


# ---------------------------------------------------------------------------
# is_profile_like
# ---------------------------------------------------------------------------

class TestIsProfileLike:
    def test_github_profile(self):
        assert is_profile_like("github", "https://github.com/Yogscast") is True

    def test_reddit_profile(self):
        assert is_profile_like("reddit", "https://reddit.com/user/Yogscast") is True

    def test_discord_invite_not_profile(self):
        assert is_profile_like("discord", "https://discord.com/invite/ABCDEF") is False

    def test_archive_not_profile(self):
        assert is_profile_like("archive", "https://web.archive.org/web/20200101/https://example.com") is False

    def test_search_url_not_profile(self):
        assert is_profile_like("reddit", "https://reddit.com/search?q=yogscast") is False

    def test_stackoverflow_filter_not_profile(self):
        assert is_profile_like("stackoverflow", "https://stackoverflow.com/users/filter") is False

    def test_empty_path_not_profile(self):
        assert is_profile_like("github", "https://github.com") is False

    def test_api_path_not_profile(self):
        assert is_profile_like("github", "https://github.com/api/v3") is False

    def test_zepeto_correct_structure(self):
        assert is_profile_like("zepeto", "https://web.zepeto.me/share/user/profile/Yogscast") is True

    def test_duolingo_profile(self):
        assert is_profile_like("duolingo", "https://duolingo.com/profile/Yogscast") is True


# ---------------------------------------------------------------------------
# score_account
# ---------------------------------------------------------------------------

class TestScoreAccount:
    def _make_account(self, platform, url, handle, modules=None):
        signals = [{"module": m, "source": "test"} for m in (modules or ["sfp_accounts"])]
        return {"platform": platform, "url": url, "handle": handle, "signals": signals}

    def test_score_in_valid_range(self):
        acc = self._make_account("github", "https://github.com/Yogscast", "Yogscast")
        score, _ = score_account("Yogscast", acc)
        assert 0.0 <= score <= 1.0

    def test_exact_handle_match_boosts_score(self):
        acc_match = self._make_account("github", "https://github.com/Yogscast", "Yogscast")
        acc_mismatch = self._make_account("github", "https://github.com/SomeoneElse", "SomeoneElse")
        score_match, _ = score_account("Yogscast", acc_match)
        score_mismatch, _ = score_account("Yogscast", acc_mismatch)
        assert score_match > score_mismatch

    def test_high_signal_platform_boosts_score(self):
        # Same handle, but high vs low signal platform
        acc_high = self._make_account("github", "https://github.com/Yogscast", "Yogscast")
        acc_low = self._make_account("chatango", "https://chatango.com/Yogscast", "Yogscast")
        score_high, _ = score_account("Yogscast", acc_high)
        score_low, _ = score_account("Yogscast", acc_low)
        assert score_high > score_low

    def test_low_signal_platform_reduces_score(self):
        acc = self._make_account("fansly", "https://fansly.com/Yogscast", "Yogscast")
        score, reasons = score_account("Yogscast", acc)
        assert any("low_signal_platform" in r for r in reasons)

    def test_multiple_modules_boost_score(self):
        acc_one = self._make_account("github", "https://github.com/Yogscast", "Yogscast", modules=["sfp_accounts"])
        acc_many = self._make_account("github", "https://github.com/Yogscast", "Yogscast", modules=["sfp_accounts", "sfp_github", "sfp_social"])
        score_one, _ = score_account("Yogscast", acc_one)
        score_many, _ = score_account("Yogscast", acc_many)
        assert score_many >= score_one

    def test_reasons_list_nonempty(self):
        acc = self._make_account("github", "https://github.com/Yogscast", "Yogscast")
        _, reasons = score_account("Yogscast", acc)
        assert len(reasons) > 0

    def test_score_clamped_to_zero_minimum(self):
        # Worst case: unknown platform, no handle match, non-profile URL
        acc = self._make_account("tinder", "https://tinder.com/search", "", modules=[])
        score, _ = score_account("Yogscast", acc)
        assert score >= 0.0

    def test_case_insensitive_handle_match(self):
        acc = self._make_account("github", "https://github.com/yogscast", "yogscast")
        score_lower, _ = score_account("Yogscast", acc)
        acc2 = self._make_account("github", "https://github.com/Yogscast", "Yogscast")
        score_upper, _ = score_account("Yogscast", acc2)
        assert score_lower == score_upper


# ---------------------------------------------------------------------------
# cluster_accounts — integration
# ---------------------------------------------------------------------------

class TestClusterAccounts:
    def _make_account(self, platform, url, username, module="sfp_accounts"):
        return {
            "platform": platform,
            "url": url,
            "username": username,
            "kind": "url",
            "signals": [{"module": module, "source": "test", "from_event": "ACCOUNT_EXTERNAL_OWNED"}],
        }

    def test_returns_list(self):
        accounts = [self._make_account("github", "https://github.com/Yogscast", "Yogscast")]
        result = cluster_accounts("Yogscast", accounts)
        assert isinstance(result, list)

    def test_single_account_one_cluster(self):
        accounts = [self._make_account("github", "https://github.com/Yogscast", "Yogscast")]
        result = cluster_accounts("Yogscast", accounts)
        assert len(result) == 1

    def test_same_platform_handle_merged(self):
        # Two accounts on same platform with same handle → one cluster
        accounts = [
            self._make_account("github", "https://github.com/Yogscast", "Yogscast"),
            self._make_account("github", "https://github.com/Yogscast", "Yogscast", module="sfp_github"),
        ]
        result = cluster_accounts("Yogscast", accounts)
        assert len(result) == 1
        assert len(result[0]["accounts"]) == 2

    def test_different_platforms_separate_clusters(self):
        accounts = [
            self._make_account("github", "https://github.com/Yogscast", "Yogscast"),
            self._make_account("reddit", "https://reddit.com/user/Yogscast", "Yogscast"),
        ]
        result = cluster_accounts("Yogscast", accounts)
        assert len(result) == 2

    def test_sorted_by_confidence_descending(self):
        accounts = [
            self._make_account("chatango", "https://chatango.com/search", ""),
            self._make_account("github", "https://github.com/Yogscast", "Yogscast"),
        ]
        result = cluster_accounts("Yogscast", accounts)
        confidences = [c["confidence"] for c in result]
        assert confidences == sorted(confidences, reverse=True)

    def test_cluster_has_required_fields(self):
        accounts = [self._make_account("github", "https://github.com/Yogscast", "Yogscast")]
        result = cluster_accounts("Yogscast", accounts)
        cluster = result[0]
        assert "platform" in cluster
        assert "handle" in cluster
        assert "confidence" in cluster
        assert "confidence_reasons" in cluster
        assert "signals" in cluster
        assert "urls" in cluster
        assert "accounts" in cluster

    def test_confidence_is_float_in_range(self):
        accounts = [self._make_account("github", "https://github.com/Yogscast", "Yogscast")]
        result = cluster_accounts("Yogscast", accounts)
        assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_empty_accounts_returns_empty(self):
        assert cluster_accounts("Yogscast", []) == []

    def test_unknown_platform_clusters_by_host(self):
        # Two accounts on same unknown domain should cluster together
        accounts = [
            self._make_account(None, "https://randomsite.xyz/Yogscast", "Yogscast"),
            self._make_account(None, "https://randomsite.xyz/Yogscast", "Yogscast", module="sfp_other"),
        ]
        result = cluster_accounts("Yogscast", accounts)
        # Both should collapse into one cluster for the same host
        assert len(result) == 1

    def test_high_confidence_github_match(self):
        accounts = [self._make_account("github", "https://github.com/Yogscast", "Yogscast")]
        result = cluster_accounts("Yogscast", accounts)
        # A GitHub profile with exact handle match should be fairly confident
        assert result[0]["confidence"] >= 0.5


# ---------------------------------------------------------------------------
# Module-level constant sanity checks
# ---------------------------------------------------------------------------

class TestConstants:
    def test_high_signal_platforms_is_set(self):
        assert isinstance(HIGH_SIGNAL_PLATFORMS, (set, frozenset))
        assert "github" in HIGH_SIGNAL_PLATFORMS
        assert "reddit" in HIGH_SIGNAL_PLATFORMS

    def test_low_signal_platforms_is_set(self):
        assert isinstance(LOW_SIGNAL_PLATFORMS, (set, frozenset))
        assert "fansly" in LOW_SIGNAL_PLATFORMS
        assert "tinder" in LOW_SIGNAL_PLATFORMS

    def test_no_overlap_between_high_and_low(self):
        assert HIGH_SIGNAL_PLATFORMS.isdisjoint(LOW_SIGNAL_PLATFORMS)
