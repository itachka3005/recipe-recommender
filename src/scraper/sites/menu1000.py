import logging
import re
from collections.abc import Iterator

from src.scraper.http import PoliteClient
from src.scraper.sitemap import sitemap_locs
from src.scraper.sites.base import Site

logger = logging.getLogger(__name__)

RECIPE_URL = re.compile(r"^https://1000\.menu/cooking/(\d+)-")


class Menu1000(Site):
    name = "menu1000"

    def __init__(self, sitemap_index: str) -> None:
        self.sitemap_index = sitemap_index

    def discover(self, client: PoliteClient) -> Iterator[tuple[str, str]]:
        index = client.get(self.sitemap_index)
        index.raise_for_status()
        for sitemap_url in sitemap_locs(index.content):
            if "sitemap-content-" not in sitemap_url:
                continue
            response = client.get(sitemap_url)
            if response.status_code != 200:
                logger.warning("Skip %s: status %s", sitemap_url, response.status_code)
                continue
            for url in sitemap_locs(response.content):
                match = RECIPE_URL.match(url)
                if match:
                    yield match.group(1), url