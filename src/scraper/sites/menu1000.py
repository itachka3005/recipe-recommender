import logging
import re
from collections.abc import Iterator

from bs4 import BeautifulSoup

from src.scraper.http import PoliteClient
from src.scraper.models import Recipe
from src.scraper.parsing import (
    ParseError,
    first_number,
    own_props,
    parse_duration,
    prop_value,
)
from src.scraper.sitemap import sitemap_locs
from src.scraper.sites.base import Site

logger = logging.getLogger(__name__)

RECIPE_URL = re.compile(r"^https://1000\.menu/cooking/(\d+)-")
RECIPE_TYPE = re.compile(r"schema\.org/Recipe\b")
WEBPAGE_TYPE = re.compile(r"schema\.org/WebPage\b")


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

    def parse(self, html: str | bytes, recipe_id: str, url: str) -> Recipe:
        soup = BeautifulSoup(html, "lxml")
        root = soup.find(attrs={"itemtype": RECIPE_TYPE})
        if root is None:
            # Older pages lack the Recipe scope: recipe properties sit
            # directly in the WebPage scope.
            root = soup.find(attrs={"itemtype": WEBPAGE_TYPE})
        if root is None or not own_props(root, "recipeIngredient"):
            raise ParseError("no recipe microdata")

        names = own_props(root, "name")
        times = own_props(root, "totalTime")
        yields = own_props(root, "recipeYield")
        # 1000.menu shows nutrition per 100 g of the dish.
        calories = root.find(attrs={"itemprop": "calories"})
        servings = first_number(prop_value(yields[0])) if yields else None

        return Recipe(
            site=self.name,
            recipe_id=recipe_id,
            url=url,
            name=prop_value(names[0]) if names else "",
            ingredients=[
                prop_value(el) for el in own_props(root, "recipeIngredient")
            ],
            total_minutes=parse_duration(prop_value(times[0])) if times else None,
            kcal_per_100g=first_number(prop_value(calories)) if calories else None,
            servings=int(servings) if servings else None,
        )