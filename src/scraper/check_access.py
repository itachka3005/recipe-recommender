import logging

from src.config import load_config
from src.scraper.http import DisallowedByRobots, FetchError, PoliteClient

URLS = [
    "https://1000.menu/cooking/14-kurinji-pirog-s-sjrnjm-sousom",
    "https://www.povarenok.ru/recipes/dishes/first/?searchid=12",
]


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()["scraper"]
    with PoliteClient(
        user_agent=cfg["user_agent"],
        delay=cfg["delay_seconds"],
        timeout=cfg["timeout_seconds"],
        max_retries=cfg["max_retries"],
    ) as client:
        for url in URLS:
            try:
                response = client.get(url)
            except DisallowedByRobots:
                print(f"BLOCKED BY ROBOTS  {url}")
            except FetchError:
                print(f"FAILED             {url}")
            else:
                has_recipe = "recipeIngredient" in response.text
                print(f"{response.status_code}  recipe markup: {has_recipe}  {url}")


if __name__ == "__main__":
    main()