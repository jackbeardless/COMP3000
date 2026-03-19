"""
Tests for normalize.py

Covers URL extraction, platform/username parsing, and full event normalization.
"""
import pytest
from normalize import (
    _extract_sfurls,
    _platform_from_url,
    _guess_handle_from_url,
    parse_platform_and_username,
    normalize_events,
)


# ---------------------------------------------------------------------------
# _extract_sfurls
# ---------------------------------------------------------------------------

class TestExtractSfurls:
    def test_single_url(self):
        text = "<SFURL>https://github.com/Yogscast</SFURL>"
        assert _extract_sfurls(text) == ["https://github.com/Yogscast"]

    def test_multiple_urls(self):
        text = "<SFURL>https://github.com/Yogscast</SFURL> <SFURL>https://twitter.com/Yogscast</SFURL>"
        result = _extract_sfurls(text)
        assert len(result) == 2
        assert "https://github.com/Yogscast" in result
        assert "https://twitter.com/Yogscast" in result

    def test_no_urls(self):
        assert _extract_sfurls("no urls here") == []

    def test_empty_string(self):
        assert _extract_sfurls("") == []

    def test_none_input(self):
        assert _extract_sfurls(None) == []

    def test_case_insensitive_tag(self):
        text = "<sfurl>https://github.com/test</sfurl>"
        assert _extract_sfurls(text) == ["https://github.com/test"]

    def test_strips_whitespace(self):
        text = "<SFURL>  https://github.com/test  </SFURL>"
        assert _extract_sfurls(text) == ["https://github.com/test"]

    def test_empty_tag_excluded(self):
        text = "<SFURL>   </SFURL>"
        assert _extract_sfurls(text) == []


# ---------------------------------------------------------------------------
# _platform_from_url
# ---------------------------------------------------------------------------

class TestPlatformFromUrl:
    def test_github(self):
        assert _platform_from_url("https://github.com/Yogscast") == "github"

    def test_github_www(self):
        assert _platform_from_url("https://www.github.com/Yogscast") == "github"

    def test_reddit(self):
        assert _platform_from_url("https://www.reddit.com/user/Yogscast") == "reddit"

    def test_lastfm(self):
        assert _platform_from_url("https://www.last.fm/user/Yogscast") == "lastfm"

    def test_unknown_domain(self):
        assert _platform_from_url("https://unknownsite.example.com/user") == "unknown"

    def test_invalid_url(self):
        # Should not raise, returns unknown
        result = _platform_from_url("not_a_url")
        assert isinstance(result, str)

    def test_twitch(self):
        assert _platform_from_url("https://www.twitch.tv/Yogscast") == "twitch"

    def test_steam(self):
        assert _platform_from_url("https://steamcommunity.com/id/Yogscast") == "steam"


# ---------------------------------------------------------------------------
# parse_platform_and_username
# ---------------------------------------------------------------------------

class TestParsePlatformAndUsername:
    def test_github(self):
        platform, user = parse_platform_and_username("https://github.com/Yogscast")
        assert platform == "github"
        assert user == "Yogscast"

    def test_github_with_repo(self):
        # /<user>/<repo> — should return user
        platform, user = parse_platform_and_username("https://github.com/Yogscast/my-repo")
        assert platform == "github"
        assert user == "Yogscast"

    def test_twitch(self):
        platform, user = parse_platform_and_username("https://twitch.tv/Yogscast")
        assert platform == "twitch"
        assert user == "Yogscast"

    def test_instagram(self):
        platform, user = parse_platform_and_username("https://instagram.com/Yogscast")
        assert platform == "instagram"
        assert user == "Yogscast"

    def test_reddit(self):
        platform, user = parse_platform_and_username("https://reddit.com/user/Yogscast")
        assert platform == "reddit"
        assert user == "Yogscast"

    def test_reddit_u_shorthand(self):
        platform, user = parse_platform_and_username("https://reddit.com/u/Yogscast")
        assert platform == "reddit"
        assert user == "Yogscast"

    def test_lastfm_www(self):
        # Regression test for the www.last.fm bug (was returning None before fix)
        platform, user = parse_platform_and_username("https://www.last.fm/user/Yogscast")
        assert platform == "lastfm"
        assert user == "Yogscast"

    def test_lastfm_no_www(self):
        platform, user = parse_platform_and_username("https://last.fm/user/Yogscast")
        assert platform == "lastfm"
        assert user == "Yogscast"

    def test_steam_id(self):
        platform, user = parse_platform_and_username("https://steamcommunity.com/id/Yogscast")
        assert platform == "steam"
        assert user == "Yogscast"

    def test_steam_profiles(self):
        platform, user = parse_platform_and_username("https://steamcommunity.com/profiles/76561198000000000")
        assert platform == "steam"
        assert user == "76561198000000000"

    def test_patreon(self):
        platform, user = parse_platform_and_username("https://patreon.com/Yogscast")
        assert platform == "patreon"
        assert user == "Yogscast"

    def test_pastebin(self):
        platform, user = parse_platform_and_username("https://pastebin.com/u/Yogscast")
        assert platform == "pastebin"
        assert user == "Yogscast"

    def test_mixcloud(self):
        platform, user = parse_platform_and_username("https://mixcloud.com/Yogscast")
        assert platform == "mixcloud"
        assert user == "Yogscast"

    def test_pinterest(self):
        platform, user = parse_platform_and_username("https://pinterest.com/Yogscast")
        assert platform == "pinterest"
        assert user == "Yogscast"

    def test_imageshack(self):
        platform, user = parse_platform_and_username("https://imageshack.com/user/Yogscast")
        assert platform == "imageshack"
        assert user == "Yogscast"

    def test_unknown_domain_returns_none_platform(self):
        platform, user = parse_platform_and_username("https://unknownsite.example.com/user/foo")
        assert platform is None

    def test_archive_returns_no_username(self):
        platform, user = parse_platform_and_username("https://web.archive.org/web/20200101/https://example.com")
        assert platform == "archive"
        assert user is None

    def test_invalid_url_returns_none_none(self):
        platform, user = parse_platform_and_username(":::not_a_url:::")
        assert platform is None
        assert user is None

    def test_www_stripped_before_lookup(self):
        # Both www and non-www variants should resolve the same platform
        p1, _ = parse_platform_and_username("https://www.instagram.com/test")
        p2, _ = parse_platform_and_username("https://instagram.com/test")
        assert p1 == p2 == "instagram"


# ---------------------------------------------------------------------------
# _guess_handle_from_url
# ---------------------------------------------------------------------------

class TestGuessHandleFromUrl:
    def test_at_handle(self):
        handle = _guess_handle_from_url("https://example.com/@Yogscast", "Yogscast")
        assert handle == "Yogscast"

    def test_user_prefix(self):
        handle = _guess_handle_from_url("https://example.com/user/Yogscast", "Yogscast")
        assert handle == "Yogscast"

    def test_target_matches_last_segment(self):
        handle = _guess_handle_from_url("https://example.com/Yogscast", "Yogscast")
        assert handle == "Yogscast"

    def test_junk_last_segment_returns_none(self):
        handle = _guess_handle_from_url("https://example.com/search", "Yogscast")
        assert handle is None

    def test_file_extension_returns_none(self):
        handle = _guess_handle_from_url("https://example.com/image.png", "Yogscast")
        assert handle is None

    def test_empty_path_returns_none(self):
        handle = _guess_handle_from_url("https://example.com/", "Yogscast")
        assert handle is None


# ---------------------------------------------------------------------------
# normalize_events — integration
# ---------------------------------------------------------------------------

class TestNormalizeEvents:
    def _make_event(self, ev_type, data, module="sfp_accounts", source="Yogscast"):
        return {"type": ev_type, "data": data, "module": module, "source": source, "generated": 0}

    def test_basic_structure(self):
        events = [
            self._make_event("ACCOUNT_EXTERNAL_OWNED", "<SFURL>https://github.com/Yogscast</SFURL>"),
        ]
        result = normalize_events(events, target="Yogscast")
        assert result["target"] == "Yogscast"
        assert "counts" in result
        assert "accounts" in result
        assert "urls" in result
        assert "evidence" in result

    def test_url_extracted_and_platform_identified(self):
        events = [
            self._make_event("ACCOUNT_EXTERNAL_OWNED", "<SFURL>https://github.com/Yogscast</SFURL>"),
        ]
        result = normalize_events(events, target="Yogscast")
        assert "https://github.com/Yogscast" in result["urls"]
        account = result["accounts"][0]
        assert account["platform"] == "github"

    def test_username_event_collected(self):
        events = [
            self._make_event("USERNAME", "Yogscast"),
        ]
        result = normalize_events(events, target="Yogscast")
        assert "Yogscast" in result["usernames"]

    def test_multiple_events_deduplicate_urls(self):
        url = "https://github.com/Yogscast"
        events = [
            self._make_event("ACCOUNT_EXTERNAL_OWNED", f"<SFURL>{url}</SFURL>"),
            self._make_event("ACCOUNT_EXTERNAL_OWNED", f"<SFURL>{url}</SFURL>"),
        ]
        result = normalize_events(events, target="Yogscast")
        # urls list is deduplicated
        assert result["urls"].count(url) == 1

    def test_empty_events(self):
        result = normalize_events([], target="Yogscast")
        assert result["counts"]["raw_events"] == 0
        assert result["accounts"] == []

    def test_lastfm_url_parses_username(self):
        events = [
            self._make_event("ACCOUNT_EXTERNAL_OWNED", "<SFURL>https://www.last.fm/user/Yogscast</SFURL>"),
        ]
        result = normalize_events(events, target="Yogscast")
        account = result["accounts"][0]
        assert account["platform"] == "lastfm"

    def test_evidence_contains_all_events(self):
        events = [
            self._make_event("USERNAME", "Yogscast"),
            self._make_event("ACCOUNT_EXTERNAL_OWNED", "<SFURL>https://github.com/Yogscast</SFURL>"),
        ]
        result = normalize_events(events, target="Yogscast")
        assert result["counts"]["evidence"] == 2
