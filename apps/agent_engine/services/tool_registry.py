"""Registry of tools available to agents."""
from typing import Callable


class ToolRegistry:
    """Simple tool registry for agent orchestration."""

    _tools: dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str, func: Callable) -> None:
        cls._tools[name] = func

    @classmethod
    def get(cls, name: str) -> Callable | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def execute(cls, name: str, **kwargs) -> dict:
        tool = cls.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        try:
            result = tool(**kwargs)
            return {"result": result, "status": "success"}
        except Exception as exc:
            return {"error": str(exc), "status": "failed"}
