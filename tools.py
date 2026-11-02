from __future__ import annotations

import ipaddress
import logging
import socket
import time
import urllib.robotparser
import uuid
from typing import Any, TypeVar
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tavily import TavilyClient

from backend.config import settings
from backend.schemas import SourceEvidence, utc_now

logger = logging.getLogger(__name__)
OutputModel = TypeVar("OutputModel", bound=BaseModel)
USER_AGENT = "MarketMindResearchBot/1.0 (+https://example.invalid/research)"


class ResearchTools:
    """Real OpenAI/LangChain, Tavily, and robots-aware page extraction integrations."""

    def __init__(self) -> None:
        missing = settings.missing_live_credentials
        if missing:
            raise RuntimeError(f"Missing backend API credentials: {', '.join(missing)}")
        self._llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            timeout=settings.request_timeout_seconds,
            max_retries=0,
        )
        self._tavily = TavilyClient(api_key=settings.tavily_api_key)
        self._http = httpx.Client(
            timeout=settings.request_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        )

    def complete(self, output_model: type[OutputModel], system_prompt: str, user_prompt: str) -> OutputModel:
        structured_llm = self._llm.with_structured_output(output_model, method="json_schema")
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                result = structured_llm.invoke(
                    [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
                )
                if isinstance(result, output_model):
                    return result
                return output_model.model_validate(result)
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    logger.warning("Structured LLM attempt %d/3 failed: %s", attempt + 1, exc)
                    time.sleep(2**attempt)
        raise RuntimeError(f"OpenAI structured response failed after 3 attempts: {last_error}") from last_error

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._tavily.search(
                    query=query,
                    max_results=max_results,
                    search_depth="advanced",
                    include_answer=False,
                    include_raw_content=False,
                )
                return [
                    result for result in response.get("results", [])
                    if result.get("url") and result.get("content")
                ]
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    logger.warning("Tavily attempt %d/3 failed: %s", attempt + 1, exc)
                    time.sleep(2**attempt)
        raise RuntimeError(f"Tavily search failed after 3 attempts: {last_error}") from last_error

    def source_from_result(
        self,
        result: dict[str, Any],
        query: str,
        extract_page: bool = True,
    ) -> SourceEvidence:
        url = str(result["url"])
        extracted = self.extract_page(url) if extract_page else ""
        snippet = str(result.get("content") or "")[:4000]
        title = str(result.get("title") or url)[:500]
        return SourceEvidence(
            source_id=uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:16],
            title=title,
            url=url,
            publisher=str(result.get("source") or urlsplit(url).hostname or "Unknown"),
            snippet=snippet,
            extracted_text=extracted[:12000],
            published_date=result.get("published_date"),
            retrieved_at=utc_now(),
            search_query=query,
        )

    def extract_page(self, url: str) -> str:
        parts = urlsplit(url)
        if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
            return ""
        if not self._public_host(parts.hostname):
            logger.warning("Skipping extraction for non-public or unresolvable host: %s", parts.hostname)
            return ""

        base = f"{parts.scheme}://{parts.netloc}"
        robots_url = urljoin(base, "/robots.txt")
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            robots_response = self._http.get(robots_url)
            if robots_response.status_code < 400:
                parser.parse(robots_response.text.splitlines())
            else:
                parser.parse([])
            if not parser.can_fetch(USER_AGENT, url):
                return ""
            response = self._http.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return ""
            if not self._public_host(urlsplit(str(response.url)).hostname or ""):
                raise ValueError("Page redirected to a non-public host.")
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
                element.decompose()
            return " ".join(soup.stripped_strings)
        except (httpx.HTTPError, ValueError, OSError) as exc:
            logger.info("Page extraction unavailable for %s: %s", url, exc)
            return ""

    @staticmethod
    def _public_host(hostname: str) -> bool:
        if not hostname:
            return False
        try:
            addresses = {entry[4][0] for entry in socket.getaddrinfo(hostname, None)}
        except (socket.gaierror, OSError):
            return False
        for address in addresses:
            parsed = ipaddress.ip_address(address)
            if not parsed.is_global:
                return False
        return bool(addresses)

    def close(self) -> None:
        self._http.close()


class DemoTools:
    """Offline-only workflow exercise; deliberately returns no invented market facts."""

    @staticmethod
    def complete(output_model: type[OutputModel], system_prompt: str, user_prompt: str) -> OutputModel:
        del system_prompt, user_prompt
        return output_model()

    @staticmethod
    def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
        del query, max_results
        return []

    @staticmethod
    def source_from_result(
        result: dict[str, Any],
        query: str,
        extract_page: bool = True,
    ) -> SourceEvidence:
        del result, query, extract_page
        raise RuntimeError("The offline demo workflow does not construct synthetic sources.")

    @staticmethod
    def extract_page(url: str) -> str:
        del url
        return ""

    @staticmethod
    def close() -> None:
        return None
