import inspect
import json
import re
from typing import Any, Callable, Literal, get_type_hints

from altron_core.types.tools import ToolParameter, ToolRequest, ToolResponse, ToolSchema


class Tool:
    """A function designated as a tool available for the agent to use."""

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        self.name = func.__name__
        self.description = (
            func.__doc__.strip() if func.__doc__ else "No description provided."
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    @property
    def schema(self) -> ToolSchema:
        """Generate a tool schema for this tool."""
        sig = inspect.signature(self.func)
        type_hints = get_type_hints(self.func)
        doc = self.func.__doc__ or ""
        param_docs = self._parse_param_docs(doc)

        parameters: list[ToolParameter] = []
        for param_name, param in sig.parameters.items():
            if param_name not in type_hints:
                continue  # Skip if no type hint

            py_type = type_hints[param_name]
            schema_type: str = self._map_type(py_type)

            parameters.append(
                {
                    "name": param_name,
                    "description": param_docs.get(
                        param_name, "No description provided."
                    ),
                    "type": schema_type,
                    "required": param.default is inspect.Parameter.empty,
                }
            )

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }

    def _map_type(
        self, py_type: Any
    ) -> Literal["string", "integer", "number", "boolean"]:
        """Map Python types to schema types."""
        origin = getattr(py_type, "__origin__", py_type)
        if origin is Literal:
            return "string"
        elif py_type is str:
            return "string"
        elif py_type is int:
            return "integer"
        elif py_type is float:
            return "number"
        elif py_type is bool:
            return "boolean"
        else:
            return "string"  # Default fallback

    def _parse_param_docs(self, doc: str) -> dict[str, str]:
        """Extract parameter descriptions from docstring."""
        param_docs: dict[str, str] = {}
        args_section = re.search(r"Args:\s*(.*?)\n\s*\n", doc, re.DOTALL)
        if args_section:
            lines = args_section.group(1).splitlines()
            for line in lines:
                match = re.match(r"\s*(\w+)\s*\(([^)]+)\):\s*(.*)", line)
                if match:
                    name, _, desc = match.groups()
                    param_docs[name] = desc.strip()
        return param_docs


class ToolExecutor:
    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: list[Tool] = tools if tools is not None else []
        self._lookup: dict[str, Tool] = {tool.name: tool for tool in self._tools}

    def add_tools(self, new_tools: list[Tool]) -> None:
        """Add new tools to the executor."""
        self._tools.extend(new_tools)
        for tool in new_tools:
            self._lookup[tool.name] = tool

    def remove_tools(self, tool_names: list[str]) -> None:
        """Remove multiple tools identified by their names."""
        self._tools = [tool for tool in self._tools if tool.name not in tool_names]
        for name in tool_names:
            self._lookup.pop(name, None)

    def convert_to_common_schema(self, tool: ToolSchema) -> dict[str, Any]:
        """Convert a tool to a common schema for execution."""
        required: list[str] = []
        properties: dict[str, dict[str, Any]] = {}

        for param in tool["parameters"]:
            # Get the details of the parameter
            properties[param["name"]] = {
                "type": param["type"],
                "description": param["description"],
            }

            # Check if the parameter is required
            if param.get("required", False):
                required.append(param["name"])

        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def get_tools(self) -> list[Tool]:
        """Retrieve a list of available tools."""
        return self._tools

    def get_schemas(self) -> list[dict[str, Any]]:
        """Retrieve the schemas of the available tools."""
        return [self.convert_to_common_schema(tool.schema) for tool in self._tools]

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool with the given name and arguments."""
        tool: Tool | None = self._lookup.get(tool_name)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")

        try:
            result: Any = tool(**arguments)
            return json.dumps(result) if not isinstance(result, str) else result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"


class EventCallbacks:
    def on_tool_request(self, tool_requests: list[ToolRequest]) -> None:
        """Called when a tool is requested."""
        for request in tool_requests:
            tool_name = request["name"]
            arguments = request["arguments"]
            print(f"Tool requested: {tool_name} with arguments {arguments}")

    def on_tool_response(self, tool_responses: list[ToolResponse]) -> None:
        """Called when a tool response is received."""
        for response in tool_responses:
            tool_name = response["name"]
            content = response["content"]
            print(f"Tool response from {tool_name}: {content}")
