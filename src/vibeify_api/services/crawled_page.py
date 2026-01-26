"""Crawled page service for business logic."""

from __future__ import annotations

import asyncio
import gzip
import io
import json
from datetime import datetime
import urllib.parse
import urllib.error
import urllib.request
import ssl
from dataclasses import dataclass
from typing import Optional, Literal
from urllib.parse import urlparse

from sqlalchemy import select

from vibeify_api.core.database import AsyncSessionLocal
from vibeify_api.models.crawled_page import CrawledPage
from vibeify_api.repository.s3 import S3Repository
from vibeify_api.schemas.crawled_page import CrawledPageResponse
from vibeify_api.services.base import BaseService


@dataclass(frozen=True)
class _CommonCrawlHit:
    warc_filename: str
    warc_offset: int
    warc_length: int
    digest: Optional[str] = None


class CrawledPageService(BaseService[CrawledPage]):
    """Service for storing crawled HTML and its metadata."""

    def __init__(self):
        super().__init__(CrawledPage)
        self.s3_repo = S3Repository()

    @staticmethod
    def _build_ssl_context() -> ssl.SSLContext:
        # Prefer system defaults; optionally use certifi if present.
        try:
            import certifi  # type: ignore

            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            return ssl.create_default_context()

    @staticmethod
    def _urlopen_bytes(
        req: urllib.request.Request,
        *,
        timeout_seconds: int,
        ssl_context: ssl.SSLContext,
    ) -> bytes:
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_context) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            # HTTPError is also a URLError; capture body for better debugging.
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            detail = f"HTTP Error {getattr(e, 'code', 'unknown')}: {getattr(e, 'reason', '')}".strip()
            if body and body.strip():
                detail = f"{detail} - {body.strip()}"
            raise RuntimeError(f"Failed to fetch {req.full_url}: {detail}") from e
        except urllib.error.URLError as e:
            # URLError subclasses OSError; wrap so Celery logs a useful message.
            raise RuntimeError(f"Failed to fetch {req.full_url}: {e}") from e
        except OSError as e:
            raise RuntimeError(f"Network error fetching {req.full_url}: {e}") from e

    async def _fetch_bytes(
        self,
        req: urllib.request.Request,
        *,
        timeout_seconds: int,
        ssl_context: ssl.SSLContext,
    ) -> bytes:
        return await asyncio.to_thread(
            self._urlopen_bytes,
            req,
            timeout_seconds=timeout_seconds,
            ssl_context=ssl_context,
        )

    @staticmethod
    def _validate_exact_url(url: str) -> None:
        # This service fetches a single *exact* URL from the CDX index.
        # Wildcards/patterns like "https://example.com/*" are not supported here.
        if "*" in url:
            raise ValueError(
                f"Wildcard URLs are not supported for single-page crawl: {url}. "
                "Provide concrete page URLs (e.g. https://www.nike.com/w/...)"
            )
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid URL (must be absolute http/https): {url}")

    @staticmethod
    def _cdx_endpoint(crawl: str) -> str:
        return f"https://index.commoncrawl.org/{crawl}-index"

    async def _lookup_common_crawl_hit(
        self,
        *,
        url: str,
        crawl: str,
        timeout_seconds: int,
        ssl_context: ssl.SSLContext,
    ) -> _CommonCrawlHit:
        params = {
            "url": url,
            "matchType": "exact",
            "output": "json",
            "fl": "filename,offset,length,digest",
            "filter": ["status:200", "mime:text/html"],
            "limit": "1",
        }
        req_url = f"{self._cdx_endpoint(crawl)}?{urllib.parse.urlencode(params, doseq=True)}"
        req = urllib.request.Request(req_url, headers={"User-Agent": "vibeify-commoncrawl/1.0"})
        body = (await self._fetch_bytes(req, timeout_seconds=timeout_seconds, ssl_context=ssl_context)).decode(
            "utf-8",
            errors="replace",
        )
        lines = [ln for ln in body.splitlines() if ln.strip()]
        if not lines:
            raise ValueError(f"No Common Crawl CDX results for url={url} crawl={crawl}")

        obj = json.loads(lines[0])
        filename = obj.get("filename")
        offset = obj.get("offset")
        length = obj.get("length")
        if not (filename and offset is not None and length is not None):
            raise ValueError(f"Invalid CDX response for url={url}: {obj}")

        return _CommonCrawlHit(
            warc_filename=str(filename),
            warc_offset=int(offset),
            warc_length=int(length),
            digest=obj.get("digest"),
        )

    async def discover_common_crawl_hits(
        self,
        *,
        seed_url: str,
        crawl: str,
        match_type: Literal["exact", "prefix", "host", "domain"] = "prefix",
        max_urls: int = 500,
        page_size: int = 1000,
        timeout_seconds: int = 30,
    ) -> list[dict]:
        """
        Discover many URLs + WARC pointers from the Common Crawl index.

        Returns a list of dicts with:
          url, warc_filename, warc_offset, warc_length, digest

        This enables "central URL" discovery (eg ``https://www.nike.com/*``)
        without doing a second per-URL CDX lookup.
        """
        if max_urls <= 0:
            return []

        seed = (seed_url or "").strip()
        if not seed:
            return []

        # Normalize wildcard shorthands (pywb-style).
        effective_match_type: str = match_type
        if seed.startswith("*."):
            effective_match_type = "domain"
            seed = seed[2:]

        if "*" in seed:
            # Wildcards imply a prefix query *unless* the caller explicitly asked for host/domain.
            # For host/domain queries, we ignore any path/wildcard and query by hostname only.
            if effective_match_type not in {"host", "domain"}:
                effective_match_type = "prefix"
            seed = seed.replace("*", "")

        url_pattern = seed
        if effective_match_type in {"host", "domain"}:
            # CDX host/domain matching is done by hostname; any path segment is ignored/unsupported.
            # If we accidentally include "/..." (or "/*"), Common Crawl may treat it like a prefix
            # wildcard query, which often yields no results for bare domains (eg "lego.com/*").
            if "://" in url_pattern:
                parsed = urlparse(url_pattern)
                url_pattern = parsed.netloc or url_pattern
            # Strip any path/query/fragment if present without scheme (eg "example.com/foo").
            url_pattern = url_pattern.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip()
        elif effective_match_type == "prefix":
            # Ensure a trailing wildcard for prefix queries.
            if not url_pattern.endswith("/"):
                url_pattern += "/"
            url_pattern += "*"

        ssl_context = self._build_ssl_context()
        base = self._cdx_endpoint(crawl)

        seen: set[str] = set()
        out: list[dict] = []

        # Common Crawl's `page`/`pageSize` follow PyWB ZipNum paging semantics:
        # `pageSize` is the number of compressed index blocks, not "rows per page".
        # To avoid HTTP 400 ("Page N invalid"), first ask for the page count.
        num_pages = 1
        try:
            page_count_params = {
                "url": url_pattern,
                "matchType": effective_match_type,
                "output": "json",
                "collapse": "urlkey",
                "filter": ["status:200", "mime:text/html"],
                "pageSize": str(page_size),
                "showNumPages": "true",
            }
            page_count_url = f"{base}?{urllib.parse.urlencode(page_count_params, doseq=True)}"
            page_count_req = urllib.request.Request(page_count_url, headers={"User-Agent": "vibeify-commoncrawl/1.0"})
            page_count_body = (
                await self._fetch_bytes(page_count_req, timeout_seconds=timeout_seconds, ssl_context=ssl_context)
            ).decode("utf-8", errors="replace")
            try:
                page_obj = json.loads(page_count_body.strip())
                if isinstance(page_obj, dict) and "pages" in page_obj:
                    num_pages = max(1, int(page_obj.get("pages") or 1))
            except Exception:
                # If parsing fails, fall back to a single page attempt.
                num_pages = 1
        except RuntimeError as e:
            # Common Crawl index returns HTTP 404 when no matches exist.
            if "HTTP Error 404" in str(e):
                return []
            # If the page-count query fails for any reason, fall back to a single page attempt.
            num_pages = 1

        for page in range(num_pages):
            if len(out) >= max_urls:
                break
            params = {
                "url": url_pattern,
                "matchType": effective_match_type,
                "output": "json",
                "fl": "url,filename,offset,length,digest",
                "collapse": "urlkey",
                "filter": ["status:200", "mime:text/html"],
                "pageSize": str(page_size),
                "page": str(page),
            }
            req_url = f"{base}?{urllib.parse.urlencode(params, doseq=True)}"
            req = urllib.request.Request(req_url, headers={"User-Agent": "vibeify-commoncrawl/1.0"})
            try:
                body = (await self._fetch_bytes(req, timeout_seconds=timeout_seconds, ssl_context=ssl_context)).decode(
                    "utf-8",
                    errors="replace",
                )
            except RuntimeError as e:
                # Common Crawl index returns HTTP 404 when no matches exist.
                if "HTTP Error 404" in str(e):
                    break
                # Page out of range or invalid paging params: treat as end of paging.
                if "Page" in str(e) and "invalid" in str(e):
                    break
                raise

            lines = [ln for ln in body.splitlines() if ln.strip()]
            if not lines:
                break

            for ln in lines:
                if len(out) >= max_urls:
                    break
                try:
                    obj = json.loads(ln)
                except json.JSONDecodeError:
                    continue

                url = obj.get("url")
                filename = obj.get("filename")
                offset = obj.get("offset")
                length = obj.get("length")
                if not (url and filename and offset is not None and length is not None):
                    continue

                url_str = str(url)
                if url_str in seen:
                    continue
                seen.add(url_str)
                out.append(
                    {
                        "url": url_str,
                        "warc_filename": str(filename),
                        "warc_offset": int(offset),
                        "warc_length": int(length),
                        "digest": obj.get("digest"),
                    }
                )

        return out

    async def discover_common_crawl_index_records(
        self,
        *,
        seed_url: str,
        crawl: str,
        max_urls: int = 500,
        timeout_seconds: int = 30,
    ) -> list[dict]:
        """
        Fetch raw Common Crawl index (CDX) records for a URL/pattern.

        This is intended to align 1:1 with calling:
          https://index.commoncrawl.org/{crawl}-index?url={seed_url}&output=json

        The returned dicts preserve Common Crawl's native keys (e.g. urlkey,
        timestamp, url, status, digest, length, offset, filename, redirect, ...).
        """
        if max_urls <= 0:
            return []

        url_pattern = (seed_url or "").strip()
        if not url_pattern:
            return []

        ssl_context = self._build_ssl_context()
        base = self._cdx_endpoint(crawl)

        params = {
            "url": url_pattern,
            "output": "json",
        }
        req_url = f"{base}?{urllib.parse.urlencode(params, doseq=True)}"
        req = urllib.request.Request(req_url, headers={"User-Agent": "vibeify-commoncrawl/1.0"})

        try:
            body = (await self._fetch_bytes(req, timeout_seconds=timeout_seconds, ssl_context=ssl_context)).decode(
                "utf-8",
                errors="replace",
            )
        except RuntimeError as e:
            # Common Crawl index returns HTTP 404 when no matches exist.
            if "HTTP Error 404" in str(e):
                return []
            raise

        out: list[dict] = []
        for ln in body.splitlines():
            if len(out) >= max_urls:
                break
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
        return out

    async def fetch_from_common_crawl_hit_and_persist(
        self,
        *,
        url: str,
        data_origin: str,
        target_application: Optional[str],
        user_id: Optional[int],
        crawl: str,
        warc_filename: str,
        warc_offset: int,
        warc_length: int,
        digest: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> dict:
        """Fetch HTML via a pre-resolved WARC record pointer (CDX hit) and persist it."""
        self._validate_exact_url(url)
        ssl_context = self._build_ssl_context()

        existing = await self.get_by_url(
            url=url,
            data_origin=data_origin,
            target_application=target_application,
        )
        if existing and digest and existing.content_digest == digest:
            return CrawledPageResponse.model_validate(existing).model_dump(mode="json", by_alias=True)

        hit = _CommonCrawlHit(
            warc_filename=warc_filename,
            warc_offset=warc_offset,
            warc_length=warc_length,
            digest=digest,
        )
        record = await self._fetch_warc_record(hit=hit, timeout_seconds=timeout_seconds, ssl_context=ssl_context)
        html_bytes, content_type = self._extract_html_from_warc(record)
        return await self.upload_and_persist_html(
            url=url,
            data_origin=data_origin,
            target_application=target_application,
            user_id=user_id,
            html_bytes=html_bytes,
            content_type=content_type,
            content_digest=digest,
            existing_id=existing.id if existing else None,
        )

    async def _fetch_warc_record(
        self,
        *,
        hit: _CommonCrawlHit,
        timeout_seconds: int,
        ssl_context: ssl.SSLContext,
    ) -> bytes:
        warc_url = f"https://data.commoncrawl.org/{hit.warc_filename}"
        end = hit.warc_offset + hit.warc_length - 1
        req = urllib.request.Request(
            warc_url,
            headers={
                "Range": f"bytes={hit.warc_offset}-{end}",
                "User-Agent": "vibeify-commoncrawl/1.0",
            },
        )
        raw = await self._fetch_bytes(req, timeout_seconds=timeout_seconds, ssl_context=ssl_context)
        try:
            return gzip.decompress(raw)
        except Exception:
            return raw

    @staticmethod
    def _unchunk(data: bytes) -> bytes:
        i = 0
        out = bytearray()
        while True:
            j = data.find(b"\r\n", i)
            if j == -1:
                break
            size_line = data[i:j].split(b";", 1)[0].strip()
            try:
                size = int(size_line, 16)
            except ValueError:
                break
            i = j + 2
            if size == 0:
                break
            out += data[i : i + size]
            i += size + 2  # chunk + CRLF
        return bytes(out)

    @classmethod
    def _extract_html_from_warc(cls, record_bytes: bytes) -> tuple[bytes, str]:
        # Split WARC headers
        warc_sep = record_bytes.find(b"\r\n\r\n")
        payload = record_bytes[warc_sep + 4 :] if warc_sep != -1 else record_bytes

        # Split HTTP headers
        http_sep = payload.find(b"\r\n\r\n")
        if http_sep == -1:
            raise ValueError("Unable to parse HTTP response from WARC record")

        http_header_bytes = payload[:http_sep]
        body = payload[http_sep + 4 :]

        header_text = http_header_bytes.decode("iso-8859-1", errors="replace")
        lines = header_text.split("\r\n")

        headers: dict[str, str] = {}
        for line in lines[1:]:
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

        if headers.get("transfer-encoding", "").lower() == "chunked":
            body = cls._unchunk(body)

        if headers.get("content-encoding", "").lower() == "gzip":
            try:
                body = gzip.decompress(body)
            except Exception:
                pass

        content_type = headers.get("content-type", "text/html")
        if "text/html" not in content_type.lower():
            raise ValueError(f"Non-HTML content-type in WARC response: {content_type}")

        return body, content_type

    async def fetch_from_common_crawl_and_persist(
        self,
        *,
        url: str,
        data_origin: str,
        target_application: Optional[str],
        user_id: Optional[int],
        crawl: str = "CC-MAIN-2025-51",
        timeout_seconds: int = 30,
    ) -> dict:
        """
        Fetch HTML for a URL from Common Crawl (CDX -> WARC) and persist it (S3 + DB).
        """
        self._validate_exact_url(url)
        ssl_context = self._build_ssl_context()
        existing = await self.get_by_url(
            url=url,
            data_origin=data_origin,
            target_application=target_application,
        )
        hit = await self._lookup_common_crawl_hit(
            url=url,
            crawl=crawl,
            timeout_seconds=timeout_seconds,
            ssl_context=ssl_context,
        )
        # If we already have this URL indexed with the same digest, skip the WARC download + S3 upload.
        if existing and hit.digest and existing.content_digest == hit.digest:
            return CrawledPageResponse.model_validate(existing).model_dump(mode="json", by_alias=True)

        record = await self._fetch_warc_record(hit=hit, timeout_seconds=timeout_seconds, ssl_context=ssl_context)
        html_bytes, content_type = self._extract_html_from_warc(record)
        return await self.upload_and_persist_html(
            url=url,
            data_origin=data_origin,
            target_application=target_application,
            user_id=user_id,
            html_bytes=html_bytes,
            content_type=content_type,
            content_digest=hit.digest,
            existing_id=existing.id if existing else None,
        )

    async def get_by_url(
        self,
        *,
        url: str,
        data_origin: str,
        target_application: Optional[str],
    ) -> Optional[CrawledPage]:
        async with AsyncSessionLocal() as session:
            stmt = select(CrawledPage).where(
                CrawledPage.url == url,
                CrawledPage.data_origin == data_origin,
            )
            if target_application is None:
                stmt = stmt.where(CrawledPage.target_application.is_(None))
            else:
                stmt = stmt.where(CrawledPage.target_application == target_application)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def existing_urls(
        self,
        *,
        urls: list[str],
        data_origin: str,
        target_application: Optional[str],
    ) -> set[str]:
        if not urls:
            return set()
        async with AsyncSessionLocal() as session:
            stmt = select(CrawledPage.url).where(
                CrawledPage.url.in_(urls),
                CrawledPage.data_origin == data_origin,
            )
            if target_application is None:
                stmt = stmt.where(CrawledPage.target_application.is_(None))
            else:
                stmt = stmt.where(CrawledPage.target_application == target_application)
            result = await session.execute(stmt)
            return {row[0] for row in result.all()}

    async def upload_and_persist_html(
        self,
        *,
        url: str,
        data_origin: str,
        target_application: Optional[str],
        user_id: Optional[int],
        html_bytes: bytes,
        content_type: str,
        content_digest: Optional[str] = None,
        existing_id: Optional[int] = None,
    ) -> dict:
        parsed = urlparse(url)
        filename = f"crawl-{parsed.netloc or 'site'}.html"
        s3_key = self.s3_repo.generate_key(filename=filename, user_id=user_id)

        await self.s3_repo.upload_file(
            s3_key=s3_key,
            file_data=io.BytesIO(html_bytes),
            content_type=content_type,
        )

        if existing_id is not None:
            crawled = await self.repository.update(
                existing_id,
                {
                    "s3_key": s3_key,
                    "s3_bucket": self.s3_repo.bucket_name,
                    "content_digest": content_digest,
                    "crawled_at": datetime.utcnow(),
                },
            )
        else:
            crawled = await self.repository.create(
                CrawledPage(
                    url=url,
                    data_origin=data_origin,
                    target_application=target_application,
                    content_digest=content_digest,
                    s3_key=s3_key,
                    s3_bucket=self.s3_repo.bucket_name,
                    user_id=user_id,
                )
            )

        return CrawledPageResponse.model_validate(crawled).model_dump(
            mode="json",
            by_alias=True,
        )
