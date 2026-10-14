import pytest

from src.scraper.parsing import ParseError
from src.scraper.sites.menu1000 import Menu1000

BREADCRUMBS = """
<div itemscope itemtype="https://schema.org/BreadcrumbList">
  <span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
    <span itemprop="name">Главная</span>
  </span>
</div>
"""

MODERN_PAGE = f"""
<html><body itemscope itemtype="http://schema.org/WebPage">
{BREADCRUMBS}
<section itemprop="mainEntity" itemscope itemtype="http://schema.org/Recipe">
  <meta itemprop="name" content="Тестовый суп" />
  <meta itemprop="recipeIngredient" content="Картофель - 3 шт." />
  <meta itemprop="recipeIngredient" content="Морковь - 1 шт." />
  <meta itemprop="totalTime" content="PT1H30M" />
  <meta itemprop="recipeYield" content="4" />
  <div itemprop="nutrition" itemscope
       itemtype="http://schema.org/NutritionInformation">
    <span itemprop="calories">120</span> ккал
  </div>
</section>
</body></html>
"""

LEGACY_PAGE = f"""
<html><body itemscope itemtype="http://schema.org/WebPage">
{BREADCRUMBS}
<section id="pt_info">
  <meta itemprop="name" content="Старый пирог" />
  <meta itemprop="recipeIngredient" content="Яйца - 3 шт." />
  <meta itemprop="totalTime" content="PT1H20M" />
</section>
</body></html>
"""

ARTICLE_PAGE = f"""
<html><body itemscope itemtype="http://schema.org/WebPage">
{BREADCRUMBS}
<h1 itemprop="name">Как выбрать арбуз</h1>
</body></html>
"""


@pytest.fixture
def site() -> Menu1000:
    return Menu1000(sitemap_index="")


def parse(site: Menu1000, html: str):
    return site.parse(html, "1", "https://1000.menu/cooking/1-test")


def test_modern_page(site):
    recipe = parse(site, MODERN_PAGE)
    assert recipe.name == "Тестовый суп"
    assert recipe.ingredients == ["Картофель - 3 шт.", "Морковь - 1 шт."]
    assert recipe.total_minutes == 90
    assert recipe.calories == 120
    assert recipe.servings == 4


def test_breadcrumb_name_is_not_used(site):
    assert parse(site, MODERN_PAGE).name != "Главная"


def test_legacy_page_without_recipe_scope(site):
    recipe = parse(site, LEGACY_PAGE)
    assert recipe.name == "Старый пирог"
    assert recipe.ingredients == ["Яйца - 3 шт."]
    assert recipe.total_minutes == 80
    assert recipe.calories is None


def test_page_without_recipe_raises(site):
    with pytest.raises(ParseError):
        parse(site, ARTICLE_PAGE)