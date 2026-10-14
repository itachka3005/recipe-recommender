import argparse
import gzip
import logging
from pathlib import Path

from src.config import load_config
from src.scraper.discover import build_site
from src.scraper.fetch import html_path
from src.scraper.parsing import ParseError
from src.scraper.storage import Storage

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse downloaded recipe pages")
    parser.add_argument("site", choices=["menu1000", "povarenok"])
    parser.add_argument(
        "--reparse", action="store_true", help="Parse already parsed pages again"
    )
    parser.add_argument(
        "--retry-failed", action="store_true", help="Parse previously failed pages"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    site = build_site(args.site, cfg["sites"][args.site])
    root = Path(cfg["storage"]["html_dir"])

    if args.reparse:
        statuses = ("downloaded", "parsed", "parse_failed")
    elif args.retry_failed:
        statuses = ("downloaded", "parse_failed")
    else:
        statuses = ("downloaded",)

    with Storage(cfg["storage"]["db_path"]) as storage:
        todo = storage.downloaded(site.name, statuses)
        logger.info("Parsing %d pages for %s", len(todo), site.name)
        parsed = failed = 0
        for recipe_id, url in todo:
            path = html_path(root, site.name, recipe_id)
            try:
                html = gzip.decompress(path.read_bytes())
                recipe = site.parse(html, recipe_id, url)
            except (OSError, ValueError, ParseError) as exc:
                logger.warning("Failed %s: %s", recipe_id, exc)
                storage.set_status(site.name, recipe_id, "parse_failed")
                failed += 1
                continue
            storage.save_recipe(recipe)
            parsed += 1
        logger.info("Parsed %d, failed %d", parsed, failed)


if __name__ == "__main__":
    main()