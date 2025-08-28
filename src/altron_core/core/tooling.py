import inspect
import json
import re
from typing import Any, Callable, Literal, Union, get_args, get_origin

from docstring_parser import parse as parse_docstring

from altron_core.types.tools import ToolSchema


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
        doc = parse_docstring(self.func.__doc__ or "")

        # map param name -> description from docstring
        doc_params = {p.arg_name: p.description for p in doc.params}

        parameters = []
        for name, param in sig.parameters.items():
            ann = param.annotation
            required = param.default is inspect.Parameter.empty

            # --- handle Optional[T] (Union[T, None]) ---
            if get_origin(ann) is Union and type(None) in get_args(ann):
                # Extract the non-None type
                args = [a for a in get_args(ann) if a is not type(None)]
                if args:
                    ann = args[0]
                required = False  # Optional means not required

            # Determine type
            p_type = "string"  # default
            if ann is int:
                p_type = "integer"
            elif ann is float:
                p_type = "number"
            elif ann is bool:
                p_type = "boolean"
            elif get_origin(ann) is Literal:
                args = get_args(ann)
                if all(isinstance(a, str) for a in args):
                    p_type = "string"
                elif all(isinstance(a, (int, float)) for a in args):
                    p_type = "number"

            parameters.append(
                {
                    "name": name,
                    "description": doc_params.get(name, "No description provided."),
                    "type": p_type,
                    "required": required,
                }
            )

        return {
            "name": self.name,
            "description": doc.short_description or self.description,
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

    def set_tools(self, new_tools: list[Tool]) -> None:
        self._tools = new_tools
        self._lookup = {tool.name: tool for tool in self._tools}

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
