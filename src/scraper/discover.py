import argparse
import logging

from src.config import load_config
from src.scraper.http import PoliteClient
from src.scraper.sites.base import Site
from src.scraper.sites.menu1000 import Menu1000
from src.scraper.sites.povarenok import Povarenok
from src.scraper.storage import Storage

logger = logging.getLogger(__name__)


def build_site(name: str, cfg: dict, max_categories: int | None = None) -> Site:
    if name == "menu1000":
        return Menu1000(cfg["sitemap_index"])
    if name == "povarenok":
        return Povarenok(
            cfg["sitemap"],
            max_pages=cfg["max_pages_per_category"],
            max_categories=max_categories,
        )
    raise ValueError(f"Unknown site: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect recipe URLs from a site")
    parser.add_argument("site", choices=["menu1000", "povarenok"])
    parser.add_argument(
        "--max-categories",
        type=int,
        default=None,
        help="Limit categories for a trial run (povarenok only)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    cfg = load_config()
    scraper_cfg = cfg["scraper"]
    site = build_site(args.site, cfg["sites"][args.site], args.max_categories)

    with (
        PoliteClient(
            user_agent=scraper_cfg["user_agent"],
            delay=scraper_cfg["delay_seconds"],
            timeout=scraper_cfg["timeout_seconds"],
            max_retries=scraper_cfg["max_retries"],
        ) as client,
        Storage(cfg["storage"]["db_path"]) as storage,
    ):
        added = storage.add_urls(site.name, site.discover(client))
        logger.info("Added %d new URLs for %s", added, site.name)
        for row in storage.count_by_status():
            print(row)


if __name__ == "__main__":
    main()