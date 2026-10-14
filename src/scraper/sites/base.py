from abc import ABC, abstractmethod
from collections.abc import Iterator

from src.scraper.http import PoliteClient


class Site(ABC):
    name: str

    @abstractmethod
    def discover(self, client: PoliteClient) -> Iterator[tuple[str, str]]:
        """Yield (recipe_id, url) for every recipe found on the site."""