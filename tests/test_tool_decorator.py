from decimal import DivisionByZero

from altron_core.core.tools import calculator


def test_tool_name():
    assert calculator.name == "calculator"


def test_tool_description():
    assert "Four function calculator." in calculator.description


def test_tool_execution():
    assert calculator("add", 2, 3) == 5
    assert calculator("subtract", 5, 2) == 3
    assert calculator("multiply", 3, 4) == 12
    assert calculator("divide", 10, 2) == 5
    try:
        calculator("divide", 10, 0)
    except DivisionByZero as e:
        assert str(e) == "Cannot divide by zero."


def test_tool_schema():
    schema = calculator.schema
    assert schema["name"] == "calculator"
    assert "Four function calculator." in schema["description"]
    param_names = {param["name"] for param in schema["parameters"]}
    assert param_names == {"operation", "a", "b"}
    operation_param = next(
        param for param in schema["parameters"] if param["name"] == "operation"
    )
    assert operation_param["type"] == "string"
    assert operation_param["required"] is True
    a_param = next(param for param in schema["parameters"] if param["name"] == "a")
    assert a_param["type"] == "number"
    assert a_param["required"] is True
    b_param = next(param for param in schema["parameters"] if param["name"] == "b")
    assert b_param["type"] == "number"
    assert b_param["required"] is True
