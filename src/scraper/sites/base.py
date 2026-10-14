from abc import ABC, abstractmethod
from collections.abc import Iterator

from src.scraper.http import PoliteClient
from src.scraper.models import Recipe


class Site(ABC):
    name: str

    @abstractmethod
    def discover(self, client: PoliteClient) -> Iterator[tuple[str, str]]:
        """Yield (recipe_id, url) for every recipe found on the site."""

    @abstractmethod
    def parse(self, html: str | bytes, recipe_id: str, url: str) -> Recipe:
        """Turn a recipe page into a Recipe.

        Raw bytes are preferred: BeautifulSoup detects the page encoding
        from <meta charset>, which differs between sites.
        """