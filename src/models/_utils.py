from pydantic import BaseModel


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ModelBase(BaseModel):
    class Config:
        alias_generator = to_camel_case
        allow_population_by_field_name = True
