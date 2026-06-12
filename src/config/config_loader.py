import csv
import json
import os
import yaml
from pathlib import Path
from dotenv import dotenv_values
from typing import Any, Dict, List, Literal
from pprint import pprint

# Resolve the `config/` folder relative to the project root
# (two levels up from this file: src/ConfigLoader/ -> src/ -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = _PROJECT_ROOT / "config"
ENV_FILE_NAME = ".env"

class ConfigLoader:
    """
    Loads every config file found inside the project's `config/` folder
    and merges them into a single dictionary.

    Supported formats
    -----------------
    .env          — KEY=VALUE  (python-dotenv)
    .yaml / .yml  — YAML mappings
    .json         — JSON objects
    .toml         — TOML tables  (Python 3.11+ stdlib)
    .ini / .cfg   — INI sections
    .conf         — KEY=VALUE or KEY: VALUE
    .txt          — KEY=VALUE pairs or plain list
    """

    def __init__(self, config_path: Path = CONFIG_DIR):
        """
        Initialize the ConfigLoader with the path to the config directory, 
        finds any existing config file and loads their variables as attributes
        to this class.
        
        Args:
            config_path (Path): The path to the config directory. Defaults to CONFIG_DIR.
        """
        self.config_dir = config_path
        self.config_files: Dict[str, Any] = {}
        self.config_files = self.find_config_files()

        self._load_env_vars()
        self._load_variables_from_config_files()

    # ------------------------------------------------------------------
    # Finds and loads config files
    # ------------------------------------------------------------------

    def find_config_files(self) -> Dict[str, Any]:
        dictionary_files = {}
        for path in self.config_dir.iterdir():
            if not path.name == ENV_FILE_NAME:
                path_suffix = Path(path).suffix.lower()
                dictionary_files[path_suffix] = Path(path)
        return dictionary_files
                    
    def _load_variables_from_config_files(self) -> Dict[str, Any]:
        for suffix, path in self.config_files.items():
            if suffix in (".yaml", ".yml"):
                self._load_yaml(path)
            elif suffix == ".json":
                self._load_json(path)
            else:
                print(f"Unsupported file format: {suffix}. Skipping {path.name}.")
                continue
    # ------------------------------------------------------------------
    # Load Variables methods
    # ------------------------------------------------------------------

    def _load_env_vars(self, path = ENV_FILE_NAME) -> Dict[str, Any]:
        if not (self.config_dir / path).exists():
            print(f"No {path} file found in {self.config_dir}. Skipping env vars.")
            return {}
        env_vars = dotenv_values(self.config_dir / path)
        self._set_attributes(env_vars)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        self._set_attributes(yaml_data)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            json_data = json.load(f)
        self._set_attributes(json_data)

    def _set_attributes(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(
        self,
        data: Any,
        filename: str,
        output_format: Literal["csv", "json", "md"],
    ) -> Path:
        """
        Save *data* to the directory configured in ``self.save_paths[output_format]``.

        The output directory is created automatically if it does not exist.

        Args:
            data: Content to write.
                  - ``"csv"``  : list of dicts, list of lists, or a DataFrame.
                  - ``"json"`` : any JSON-serialisable object.
                  - ``"md"``   : a plain string.
            filename: Base filename (extension is added/replaced automatically).
            output_format: One of ``"csv"``, ``"json"``, or ``"md"``.

        Returns:
            Path: Absolute path of the file that was written.

        Raises:
            AttributeError: ``save_paths`` is not set on this config object.
            KeyError: ``save_paths`` has no entry for *output_format*.
            TypeError: *data* has an incompatible type for *output_format*.
        """
        paths_map: Dict[str, str] = self.save_paths
        if output_format not in paths_map:
            raise KeyError(
                f"No entry '{output_format}' in config 'save_paths'. "
                f"Available keys: {list(paths_map.keys())}"
            )

        output_dir = _PROJECT_ROOT / paths_map[output_format]
        output_dir.mkdir(parents=True, exist_ok=True)

        ext = ".md" if output_format == "md" else f".{output_format}"
        target: Path = output_dir / f"{Path(filename).stem}{ext}"

        if output_format == "csv":
            self._save_csv(data, target)
        elif output_format == "json":
            self._save_json(data, target)
        elif output_format == "md":
            self._save_md(data, target)

        return target

    def _save_csv(self, data: Any, path: Path) -> None:
        # DataFrame duck-type — avoids importing pandas in ConfigLoader
        if hasattr(data, "to_csv"):
            data.to_csv(path, index=False, encoding="utf-8")
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            if data and isinstance(data[0], dict):
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f)
                writer.writerows(data or [])

    def _save_json(self, data: Any, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_md(self, data: str, path: Path) -> None:
        if not isinstance(data, str):
            raise TypeError(f"Expected str for markdown output, got {type(data).__name__}")
        path.write_text(data, encoding="utf-8")

# ----------------------------------------------------------------------
# Get functions
# ----------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Return the config value for *key*, or *default* if not found.

        Args:
            key (str): The configuration key to look up.
            default (Any): Value to return when the key is absent. Defaults to None.

        Returns:
            Any: The value associated with *key*, or *default*.
        """
        return getattr(self, key, default)

# ----------------------------------------------------------------------
# Usage
# ----------------------------------------------------------------------

if __name__ == "__main__":
    loader = ConfigLoader()        # defaults to project_root/config/
    

