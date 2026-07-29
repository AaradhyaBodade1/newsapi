import httpx

from worker.ingestion.api_fetcher import fetch_api


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_api_parses_nested_articles_list(monkeypatch):
    payload = {
        "articles": [
            {"title": "First Story", "url": "https://example.com/1", "description": "desc 1"},
            {"headline": "Second Story", "link": "https://example.com/2"},
            {"url": "https://example.com/missing-title"},  # skipped: no title
        ]
    }

    def fake_get(url, timeout=None, headers=None):
        return _FakeResponse(payload)

    monkeypatch.setattr(httpx, "get", fake_get)

    source = {
        "id": "11111111-1111-1111-1111-111111111111",
        "category_id": None,
        "url": "https://example.com/api",
    }
    articles = fetch_api(source)

    assert len(articles) == 2
    assert articles[0].title == "First Story"
    assert articles[0].summary == "desc 1"
    assert articles[1].title == "Second Story"
    assert articles[1].url == "https://example.com/2"
