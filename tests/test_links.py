from univid.links import extract_links, is_supported


def test_supported_domains_and_subdomains():
    assert is_supported("https://x.com/user/status/1")
    assert is_supported("https://www.instagram.com/reel/abc/")
    assert is_supported("https://m.facebook.com/watch?v=1")
    assert is_supported("https://vm.tiktok.com/ZM123/")
    assert is_supported("https://v.redd.it/abc")


def test_unsupported_and_lookalike_domains():
    assert not is_supported("https://example.com/video.mp4")
    assert not is_supported("https://www.youtube.com/watch?v=abc")
    assert not is_supported("https://notx.com/status/1")
    assert not is_supported("https://x.com.evil.example/status/1")


def test_extracts_in_order_and_dedupes():
    msg = "look https://x.com/a/status/1 and https://tiktok.com/@u/video/2 and https://x.com/a/status/1"
    assert extract_links(msg) == ["https://x.com/a/status/1", "https://tiktok.com/@u/video/2"]


def test_skips_angle_bracket_links():
    assert extract_links("no embed please <https://x.com/a/status/1>") == []


def test_strips_trailing_punctuation_and_markdown():
    assert extract_links("(see https://x.com/a/status/1).") == ["https://x.com/a/status/1"]
    assert extract_links("[vid](https://x.com/a/status/1)") == ["https://x.com/a/status/1"]
    assert extract_links("||https://x.com/a/status/1||") == ["https://x.com/a/status/1"]


def test_limit():
    msg = " ".join(f"https://x.com/a/status/{i}" for i in range(10))
    assert len(extract_links(msg)) == 3
