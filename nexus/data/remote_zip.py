"""Seekable, strictly bounded HTTP ranges for selecting files from a large ZIP.

No full-download fallback: an origin that ignores Range fails explicitly.
"""
from __future__ import annotations

import io
import urllib.request


class RemoteZipReader(io.RawIOBase):
    def __init__(self, url: str, budget: int = 512 * 1024**2):
        super().__init__()
        self.url = url
        self.budget = budget
        self.transferred = 0
        self.position = 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
            self.size = int(r.headers["Content-Length"])
            self.etag = r.headers.get("ETag")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        position = offset + (self.position if whence == io.SEEK_CUR else self.size if whence == io.SEEK_END else 0)
        if whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END) or position < 0:
            raise ValueError("Invalid seek")
        self.position = position
        return position

    def read(self, size=-1):
        size = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if size <= 0:
            return b""
        if size > 32 * 1024**2 or self.transferred + size > self.budget:
            raise ValueError("HTTP range exceeds request or total transfer budget")
        start, end = self.position, self.position + size - 1
        headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
        if self.etag:
            headers["If-Match"] = self.etag
        request = urllib.request.Request(self.url, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            expected = f"bytes {start}-{end}/{self.size}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise ValueError("Origin ignored or changed HTTP Range; refusing full download")
            data = response.read(size + 1)
        self.transferred += len(data)
        if len(data) != size:
            raise ValueError("Truncated or oversized range")
        self.position += size
        return data
