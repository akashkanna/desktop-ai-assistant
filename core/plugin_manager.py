"""
Plugin Manager — discovers and loads external action modules.
"""
import importlib
import pkgutil
from pathlib import Path
from logger_config import setup_logger

logger = setup_logger("plugin_manager")

class PluginManager:
    def __init__(self, package_name: str = "plugins"):
        self.package_name = package_name
        self.plugins = {}
        logger.info("PluginManager initialized.")
        self.discover_plugins()

    def discover_plugins(self):
        try:
            package = importlib.import_module(self.package_name)
        except ImportError as e:
            logger.error(f"Could not import plugin package: {e}")
            return

        package_path = Path(package.__path__[0])
        for finder, name, ispkg in pkgutil.iter_modules([str(package_path)]):
            if ispkg:
                continue
            try:
                module = importlib.import_module(f"{self.package_name}.{name}")
                plugin = getattr(module, "Plugin", None)
                if plugin:
                    self.plugins[name] = plugin()
                    logger.info(f"Loaded plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")

    def list_plugins(self) -> list[str]:
        return list(self.plugins.keys())

    def get_plugin(self, name: str):
        return self.plugins.get(name)

    def execute_action(self, plugin_name: str, action_name: str, **kwargs):
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return f"Plugin '{plugin_name}' was not found."
        action = getattr(plugin, action_name, None)
        if not action:
            return f"Action '{action_name}' was not found for plugin '{plugin_name}'."
        try:
            return action(**kwargs)
        except Exception as e:
            logger.error(f"Plugin action failed: {e}")
            return f"Plugin '{plugin_name}' failed to perform '{action_name}'."
