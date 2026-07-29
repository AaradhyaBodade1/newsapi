from common.dedupe import compute_content_hash, normalize_url


def test_same_title_and_url_produces_same_hash():
    a = compute_content_hash("Big News Today", "https://example.com/article?utm_source=twitter")
    b = compute_content_hash("  big news today  ", "https://example.com/article?utm_source=facebook")
    assert a == b


def test_different_articles_produce_different_hashes():
    a = compute_content_hash("Story A", "https://example.com/a")
    b = compute_content_hash("Story B", "https://example.com/b")
    assert a != b


def test_normalize_url_strips_tracking_params_and_trailing_slash():
    assert normalize_url("https://Example.com/Path/?utm_source=x&id=5") == normalize_url(
        "https://example.com/Path?id=5"
    )
