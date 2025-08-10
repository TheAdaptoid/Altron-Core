from pydantic import BaseModel


def to_camel_case(snake_str: str) -> str:
    """
    Convert a snake_case string to camelCase.

    Args:
        snake_str (str): The input string in snake_case format.

    Returns:
        str: The converted string in camelCase format.

    Example:
        >>> to_camel_case("example_string")
        'exampleString'
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ModelBase(BaseModel):
    class Config:
        alias_generator = to_camel_case
        validate_by_name = True
