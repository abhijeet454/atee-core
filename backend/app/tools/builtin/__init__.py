from app.tools.registry import get_tool_registry
from .file_ops import FileOpsTool
from .system import SystemTool
from .web_search import WebSearchTool
from .reminder import ReminderTool

def register_builtin_tools():
    registry = get_tool_registry()
    registry.register("file_ops", FileOpsTool())
    registry.register("system", SystemTool())
    registry.register("web_search", WebSearchTool())
    registry.register("reminder", ReminderTool())
