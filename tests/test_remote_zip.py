from email.message import Message

import pytest

from nexus.data.remote_zip import RemoteZipReader


class Response:
    def __init__(self, status, headers, body=b""):
        self.status = status
        self.headers = Message()
        for key, value in headers.items():
            self.headers[key] = value
        self.body = body
        self.read_called = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, size):
        self.read_called = True
        return self.body[:size]


def test_origin_ignoring_range_is_rejected_before_body_read(monkeypatch):
    head = Response(200, {"Content-Length": "10000000000"})
    full = Response(200, {"Content-Length": "10000000000"})
    replies = iter([head, full])
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: next(replies))
    reader = RemoteZipReader("https://example.com/data.zip")
    with pytest.raises(ValueError, match="refusing full download"):
        reader.read(10)
    assert not full.read_called


def test_transfer_cap_applies_before_request(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(200, {"Content-Length": "1000"}))
    reader = RemoteZipReader("https://example.com/data.zip", budget=4)
    with pytest.raises(ValueError, match="budget"):
        reader.read(5)
