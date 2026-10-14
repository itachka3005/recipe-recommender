from abc import ABC, abstractmethod
from collections.abc import Iterator

from src.scraper.http import PoliteClient
from src.scraper.models import Recipe


class Site(ABC):
    name: str

    @abstractmethod
    def discover(self, client: PoliteClient) -> Iterator[tuple[str, str]]:
        """Yield (recipe_id, url) for every recipe found on the site."""

    def parse(self, html: str, recipe_id: str, url: str) -> Recipe:
        """Turn a recipe page into a Recipe."""
        raise NotImplementedError