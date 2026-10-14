import logging
import re
from collections.abc import Iterator

from src.scraper.http import DisallowedByRobots, FetchError, PoliteClient
from src.scraper.sitemap import sitemap_locs
from src.scraper.sites.base import Site

logger = logging.getLogger(__name__)

BASE = "https://www.povarenok.ru"
CATEGORY_URL = re.compile(r"/recipes/[^?]+\?searchid=\d+$")
RECIPE_ID = re.compile(r"/recipes/show/(\d+)/")
PAGINATOR = re.compile(
    r'new Paginator\("paginator_1",\s*(\d+),.*?"([^"]+)",\s*"([^"]*)"'
)


def extract_recipe_ids(html: str) -> set[str]:
    return set(RECIPE_ID.findall(html))


def extract_pagination(html: str) -> tuple[int, str, str] | None:
    match = PAGINATOR.search(html)
    if not match:
        return None
    return int(match.group(1)), match.group(2), match.group(3)


def page_url(prefix: str, suffix: str, page: int) -> str:
    return f"{BASE}{prefix}{page}/{suffix}"


def recipe_url(recipe_id: str) -> str:
    return f"{BASE}/recipes/show/{recipe_id}/"


class Povarenok(Site):
    name = "povarenok"

    def __init__(
        self, sitemap: str, max_pages: int = 10, max_categories: int | None = None
    ) -> None:
        self.sitemap = sitemap
        self.max_pages = max_pages
        self.max_categories = max_categories

    def discover(self, client: PoliteClient) -> Iterator[tuple[str, str]]:
        categories = self._categories(client)
        logger.info("Found %d categories", len(categories))
        seen: set[str] = set()
        for i, category in enumerate(categories, 1):
            before = len(seen)
            for html in self._pages(client, category):
                for recipe_id in extract_recipe_ids(html):
                    if recipe_id not in seen:
                        seen.add(recipe_id)
                        yield recipe_id, recipe_url(recipe_id)
            logger.info(
                "Category %d/%d: +%d recipes (total %d) %s",
                i, len(categories), len(seen) - before, len(seen), category,
            )

    def _categories(self, client: PoliteClient) -> list[str]:
        html = self._fetch(client, self.sitemap)
        if html is None:
            return []
        locs = sitemap_locs(html.encode("utf-8"))
        child_sitemaps = [loc for loc in locs if loc.endswith(".xml")]
        for child in child_sitemaps:
            child_xml = self._fetch(client, child)
            if child_xml is not None:
                locs.extend(sitemap_locs(child_xml.encode("utf-8")))
        categories = sorted(
            {
                loc.replace("http://", "https://", 1)
                for loc in locs
                if CATEGORY_URL.search(loc)
            }
        )
        logger.info("Sitemap contains %d categories", len(categories))
        return categories[: self.max_categories]

    def _pages(self, client: PoliteClient, url: str) -> Iterator[str]:
        first = self._fetch(client, url)
        if first is None:
            return
        yield first
        pagination = extract_pagination(first)
        if pagination is None:
            return
        total, prefix, suffix = pagination
        for page in range(2, min(total, self.max_pages) + 1):
            html = self._fetch(client, page_url(prefix, suffix, page))
            if html is None:
                return
            yield html

    @staticmethod
    def _fetch(client: PoliteClient, url: str) -> str | None:
        try:
            response = client.get(url)
        except (DisallowedByRobots, FetchError) as exc:
            logger.warning("Skip %s: %s", url, type(exc).__name__)
            return None
        if response.status_code != 200:
            logger.warning("Skip %s: status %s", url, response.status_code)
            return None
        return response.text