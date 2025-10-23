def get_temperature(location: str, unit: str = "Celsius") -> dict:
    """
    Fetch the current temperature for a given location.

    Args:
        location (str): The location to fetch the temperature for.
        unit (str): The unit of temperature. Either "Celsius" or "Fahrenheit". Default is "Celsius".

    Returns:
        dict: A dictionary containing the location and the current temperature.
    """
    # Placeholder implementation
    temperature_data: dict = {
        "location": location,
        "temperature": "22" if unit == "Celsius" else "72",
        "unit": unit,
    }
    return temperature_data


class ToolManager:
    def __init__(self):
        self._tools: list[dict] = []

    def list_tools(self) -> list[dict]:
        return self._tools

    def execute_tool(self, tool_id: str, parameters: dict) -> dict:
        for tool in self._tools:
            if tool["id"] == tool_id:
                # Simulate tool execution
                return {"status": "success", "data": tool["data"]}
        return {"status": "error", "message": "Tool not found"}
