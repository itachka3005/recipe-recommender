import pytest

from src.scraper.parsing import ParseError
from src.scraper.sites.povarenok import Povarenok

TIME = '<time datetime="PT40M" itemprop="totalTime">40 минут</time>'
YIELD = '<span itemprop="recipeYield">6</span>'

PAGE = f"""
<html><head><meta charset="windows-1251"></head><body>
<div itemscope itemtype="http://schema.org/Recipe">
  <h1 itemprop="name">Батон на кефире</h1>
  <ul>
    <li itemprop="recipeIngredient">
      <a href="#"><span>Кефир</span></a>
          —
          <span>170 мл</span>
    </li>
    <li itemprop="recipeIngredient">
      <a href="#"><span>Соль</span></a>
          —
    </li>
  </ul>
  {TIME}
  {YIELD}
  <div itemprop="nutrition" itemscope
       itemtype="http://schema.org/NutritionInformation">
    <table>
      <tr><td class="nae-title" colspan="4"><strong>Готового блюда</strong></td></tr>
      <tr>
        <td>ккал<br/><strong itemprop="calories">2866.3 ккал</strong></td>
        <td>белки<br/><strong>100 г</strong></td>
      </tr>
      <tr><td class="nae-title" colspan="4"><strong>100 г блюда</strong></td></tr>
      <tr><td>ккал<br/><strong>263 ккал</strong></td></tr>
    </table>
  </div>
</div>
</body></html>
"""


@pytest.fixture
def site() -> Povarenok:
    return Povarenok(sitemap="")


def parse(site: Povarenok, html: str):
    return site.parse(
        html.encode("cp1251"), "1", "https://www.povarenok.ru/recipes/show/1/"
    )


def test_windows_1251_page(site):
    recipe = parse(site, PAGE)
    assert recipe.name == "Батон на кефире"
    assert recipe.ingredients == ["Кефир — 170 мл", "Соль"]
    assert recipe.total_minutes == 40
    assert recipe.servings == 6


def test_kcal_taken_per_100g_not_whole_dish(site):
    assert parse(site, PAGE).kcal_per_100g == 263


def test_old_page_without_time_and_yield(site):
    recipe = parse(site, PAGE.replace(TIME, "").replace(YIELD, ""))
    assert recipe.total_minutes is None
    assert recipe.servings is None


def test_page_without_recipe_raises(site):
    with pytest.raises(ParseError):
        parse(site, "<html><body><h1>Статья</h1></body></html>")

NEW_TEMPLATE = """
<html><head><meta charset="windows-1251"></head><body>
<h1>Шарлотка на кефире</h1>
<div class="ingredients-bl"><ul>
  <li><a href="#"><span itemprop="name">Кефир</span></a>
      — <span itemprop="amount">200 мл</span></li>
  <li><a href="#"><span itemprop="name">Мука</span></a>
      — </li>
</ul></div>
</body></html>
"""

PRINT_VERSION = """
<html><head><meta charset="windows-1251"></head><body>
<h1>Главная>Рецепты>версия для печати</h1>
</body></html>
"""


def test_new_template_without_recipe_scope(site):
    recipe = parse(site, NEW_TEMPLATE)
    assert recipe.name == "Шарлотка на кефире"
    assert recipe.ingredients == ["Кефир — 200 мл", "Мука"]
    assert recipe.total_minutes is None
    assert recipe.kcal_per_100g is None


def test_print_version_is_rejected(site):
    with pytest.raises(ParseError):
        parse(site, PRINT_VERSION)