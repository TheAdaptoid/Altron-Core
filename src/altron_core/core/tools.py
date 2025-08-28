from datetime import datetime, timedelta
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


@Tool
def time_utils(
    operation: Literal["now", "add"],
    amount: int | None,
    unit: Literal["days", "hours", "minutes"],
) -> str:
    """
    Perform time-related operations and returns the result as an ISO-formatted string.

    Args:
        operation (Literal["now", "add"]): The operation to perform.
            - "now": Returns the current datetime.
            - "add": Adds a specified amount of time to the current datetime.
        amount (int | None): The amount of time to add. Required if operation is "add".
        unit (Literal["days", "hours", "minutes"]): The unit of time to add. Required if operation is "add".

    Returns:
        str: The resulting datetime as an ISO-formatted string, or "Invalid Operation." if the operation is not recognized.

    Raises:
        KeyError: If an invalid unit is provided when operation is "add".
    """
    if operation == "now":
        return datetime.now().isoformat()

    if operation == "add":
        if amount is None:
            raise ValueError("`amount` can not be `None` during an `add` operation.")

        if isinstance(amount, str):
            try:
                amount = int(amount)
            except Exception:
                raise TypeError("`amount` must be an integer")

        unit_map: dict = {"days": 0, "hours": 0, "minutes": 0}
        unit_map[unit] = amount
        future = datetime.now() + timedelta(**unit_map)
        return future.isoformat()

    raise "Invalid Operation."
