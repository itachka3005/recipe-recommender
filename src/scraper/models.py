from pydantic import BaseModel, Field


class Recipe(BaseModel):
    site: str
    recipe_id: str
    url: str
    name: str = Field(min_length=1)
    ingredients: list[str] = Field(min_length=1)
    total_minutes: int | None = Field(default=None, ge=0)
    kcal_per_100g: float | None = Field(default=None, ge=0)
    servings: int | None = Field(default=None, ge=1)