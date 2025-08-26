from decimal import DivisionByZero
from typing import Literal

from altron_core.core.tooling import Tool


@Tool
def calculator(
    operation: Literal["add", "subtract", "multiply", "divide"], a: float, b: float
) -> float:
    """
    Four function calculator. Operations are rounded to 4 decimal places.

    Args:
        operation (str): The arithmetic operation to perform. One of "add", "subtract", "multiply", "divide".
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The result of the arithmetic operation.
    """
    # Ensure a and b are numbers
    if isinstance(a, str) or isinstance(b, str):
        a = float(a)
        b = float(b)

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Both 'a' and 'b' must be numbers.")

    result: float

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise DivisionByZero("Cannot divide by zero.")
        result = a / b
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    return round(result, 4)
