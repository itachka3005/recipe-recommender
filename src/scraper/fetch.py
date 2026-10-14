import argparse
import gzip
import logging
from pathlib import Path

from src.config import load_config
from src.scraper.http import DisallowedByRobots, FetchError, PoliteClient
from src.scraper.storage import Storage

logger = logging.getLogger(__name__)


def html_path(root: Path, site: str, recipe_id: str) -> Path:
    return root / site / f"{recipe_id}.html.gz"


def save_gzip(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(content))
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download recipe pages")
    parser.add_argument("site", choices=["menu1000", "povarenok"])
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    cfg = load_config()
    scraper_cfg = cfg["scraper"]
    root = Path(cfg["storage"]["html_dir"])

    with (
        PoliteClient(
            user_agent=scraper_cfg["user_agent"],
            delay=scraper_cfg["delay_seconds"],
            timeout=scraper_cfg["timeout_seconds"],
            max_retries=scraper_cfg["max_retries"],
        ) as client,
        Storage(cfg["storage"]["db_path"]) as storage,
    ):
        todo = storage.pending(args.site, args.limit)
        logger.info("Downloading %d pages for %s", len(todo), args.site)
        for i, (recipe_id, url) in enumerate(todo, 1):
            path = html_path(root, args.site, recipe_id)
            if path.exists():
                storage.mark(args.site, recipe_id, "downloaded", 200)
                continue
            try:
                response = client.get(url)
            except DisallowedByRobots:
                storage.mark(args.site, recipe_id, "blocked")
                continue
            except FetchError:
                storage.mark(args.site, recipe_id, "failed")
                continue

            if response.status_code == 200:
                save_gzip(path, response.content)
                storage.mark(args.site, recipe_id, "downloaded", 200)
            elif response.status_code in (404, 410):
                storage.mark(args.site, recipe_id, "missing", response.status_code)
            else:
                storage.mark(args.site, recipe_id, "failed", response.status_code)

            if i % 50 == 0:
                logger.info("%d/%d done", i, len(todo))


if __name__ == "__main__":
    main()