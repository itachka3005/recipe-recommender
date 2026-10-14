import sqlite3

from src.config import load_config

QUERY = """
SELECT
    site,
    COUNT(*),
    AVG(total_minutes IS NULL),
    AVG(kcal_per_100g IS NULL),
    AVG(servings IS NULL),
    AVG(json_array_length(ingredients)),
    MAX(json_array_length(ingredients))
FROM recipes
GROUP BY site
"""


def main() -> None:
    cfg = load_config()
    conn = sqlite3.connect(cfg["storage"]["db_path"])
    print(
        f"{'site':<10} {'recipes':>8} {'no time':>8} {'no kcal':>8} "
        f"{'no yield':>8} {'avg ingr':>9} {'max ingr':>9}"
    )
    for site, n, no_time, no_kcal, no_yield, avg_ingr, max_ingr in conn.execute(QUERY):
        print(
            f"{site:<10} {n:>8} {no_time:>8.1%} {no_kcal:>8.1%} "
            f"{no_yield:>8.1%} {avg_ingr:>9.1f} {max_ingr:>9}"
        )
    conn.close()


if __name__ == "__main__":
    main()