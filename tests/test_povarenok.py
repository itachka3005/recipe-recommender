from src.scraper.sites.povarenok import (
    extract_pagination,
    extract_recipe_ids,
    page_url,
    recipe_url,
)

LISTING = """
<a href="https://www.povarenok.ru/recipes/show/126075/">Борщ</a>
<a href="https://www.povarenok.ru/recipes/show/126075/#comments">12</a>
<a href="https://www.povarenok.ru/recipes/show/135830/">Щи</a>
<script type="text/javascript">
  pag_1 = new Paginator("paginator_1", 6, (screen.width > 640 ? 10 : 6), 1,
  "/recipes/dishes/first/~", "?searchid=12", 0);
</script>
"""


def test_recipe_ids_are_deduplicated():
    assert extract_recipe_ids(LISTING) == {"126075", "135830"}


def test_pagination_is_parsed_despite_nested_parentheses():
    assert extract_pagination(LISTING) == (6, "/recipes/dishes/first/~", "?searchid=12")


def test_pagination_missing_on_showcase_page():
    assert extract_pagination("<html>no pager here</html>") is None


def test_page_url():
    assert (
        page_url("/recipes/dishes/first/~", "?searchid=12", 2)
        == "https://www.povarenok.ru/recipes/dishes/first/~2/?searchid=12"
    )


def test_recipe_url_is_normalized():
    assert recipe_url("126075") == "https://www.povarenok.ru/recipes/show/126075/"