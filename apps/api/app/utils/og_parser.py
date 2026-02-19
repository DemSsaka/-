import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.utils.ssrf import validate_external_url


def _parse_price_to_cents(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        value = Decimal(raw.strip().replace(",", "."))
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    return int(value * 100)


def _first_content(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    if not tag:
        return None
    value = tag.get("content")
    return str(value).strip() if value else None


def _jsonld_product(soup: BeautifulSoup) -> tuple[int | None, str | None]:
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        try:
            data = json.loads(script.text)
        except Exception:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            if node_type != "Product" and node_type != ["Product"]:
                continue
            offers = node.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if not isinstance(offers, dict):
                continue
            price_cents = _parse_price_to_cents(str(offers.get("price")))
            currency = offers.get("priceCurrency")
            return price_cents, str(currency) if currency else None
    return None, None


def _extract_price_from_meta(soup: BeautifulSoup) -> int | None:
    candidates = [
        _first_content(soup, "product:price:amount"),
        _first_content(soup, "og:price:amount"),
        _first_content(soup, "twitter:data1"),
    ]
    for raw in candidates:
        cents = _parse_price_to_cents(raw)
        if cents:
            return cents
    return None


def _extract_price_from_text(body: str) -> int | None:
    patterns = [
        r'"price"\s*:\s*"?(?P<price>\d+[.,]?\d*)"?',
        r'"finalPrice"\s*:\s*"?(?P<price>\d+[.,]?\d*)"?',
        r'"priceAmount"\s*:\s*"?(?P<price>\d+[.,]?\d*)"?',
        r'"salePrice"\s*:\s*"?(?P<price>\d+[.,]?\d*)"?',
        r'"amount"\s*:\s*"?(?P<price>\d+[.,]?\d*)"?\s*,\s*"currency"\s*:\s*"?(?:RUB|USD|EUR|GBP)"?',
        r'(?P<price>\d{2,7}[.,]?\d{0,2})\s?(?:₽|руб|RUB|\$|USD|EUR|€|£)',
    ]
    for pat in patterns:
        m = re.search(pat, body, flags=re.IGNORECASE)
        if not m:
            continue
        cents = _parse_price_to_cents(m.group("price"))
        if cents:
            return cents
    return None


async def parse_og(url: str) -> dict[str, Any]:
    validate_external_url(url)
    timeout = httpx.Timeout(connect=5, read=8, write=8, pool=8)
    max_redirects = 3

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=max_redirects) as client:
        resp = await client.get(url, headers=headers)
        final_url = str(resp.url)
        validate_external_url(final_url)

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return {
                "title": None,
                "image_url": None,
                "price_cents": None,
                "currency": None,
                "raw": {"error": "URL does not serve HTML", "final_url": final_url},
                "warning": "This page blocks metadata or is not an HTML product page.",
            }

        body = resp.text[:1_000_000]

    soup = BeautifulSoup(body, "lxml")
    title = _first_content(soup, "og:title") or _first_content(soup, "twitter:title")
    image = _first_content(soup, "og:image") or _first_content(soup, "twitter:image")

    price_cents, currency = _jsonld_product(soup)
    if not price_cents:
        price_cents = _extract_price_from_meta(soup)
    if not price_cents:
        price_cents = _extract_price_from_text(body)

    if title is None and soup.title and soup.title.string:
        title = soup.title.string.strip()

    if image and image.startswith("//"):
        image = f"{urlparse(url).scheme}:{image}"

    return {
        "title": title,
        "image_url": image,
        "price_cents": price_cents,
        "currency": currency,
        "raw": {
            "og_title": _first_content(soup, "og:title"),
            "og_image": _first_content(soup, "og:image"),
            "twitter_title": _first_content(soup, "twitter:title"),
            "twitter_image": _first_content(soup, "twitter:image"),
        },
        "warning": None,
    }
