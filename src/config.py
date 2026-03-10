from pathlib import Path
import logging
import os

import yaml
from dotenv import load_dotenv

load_dotenv()

TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


def get_project_root() -> Path:
    """Walk up from this file's directory to find the project root
    (identified by the presence of pyproject.toml).
    Returns the absolute Path to the project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml found)")


def _get_env_override(key: str) -> str | None:
    value = os.environ.get(key)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in TRUTHY_VALUES:
        return True
    if lowered in FALSY_VALUES:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _set_nested_value(config: dict, path: tuple[str, ...], value):
    current = config
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value


def _apply_env_overrides(config: dict):
    overrides = (
        (("arxiv", "categories"), "ARXIV_CATEGORIES", _parse_csv),
        (("arxiv", "max_results_per_category"), "ARXIV_MAX_RESULTS_PER_CATEGORY", int),
        (("arxiv", "cutoff_days"), "ARXIV_CUTOFF_DAYS", int),
        (("llm", "provider"), "LLM_PROVIDER", str),
        (("email", "enabled"), "EMAIL_ENABLED", _parse_bool),
        (("email", "from"), "EMAIL_FROM", str),
        (("email", "to"), "EMAIL_TO", _parse_csv),
        (("email", "subject_prefix"), "EMAIL_SUBJECT_PREFIX", str),
        (("scheduler", "cron"), "SCHEDULE_CRON", str),
        (("report", "chinese"), "REPORT_CHINESE", _parse_bool),
        (("database", "path"), "DATABASE_PATH", str),
    )

    for path, env_key, parser in overrides:
        raw_value = _get_env_override(env_key)
        if raw_value is None:
            continue
        parsed_value = parser(raw_value)
        print(f"DEBUG: Applying env override: {env_key}={raw_value} -> {path}={parsed_value}")
        _set_nested_value(config, path, parsed_value)

    print(f"DEBUG: After overrides, llm.provider = {config.get('llm', {}).get('provider')}")


def load_config(path: str = None) -> dict:
    """Load and return the YAML config dict.
    If path is None, defaults to config/config.yaml relative to project root.
    Resolves the database path to an absolute path relative to project root."""
    root = get_project_root()
    if path is None:
        config_path = root / "config" / "config.yaml"
    else:
        config_path = Path(path)
        if not config_path.is_absolute():
            config_path = root / config_path
    with open(config_path) as f:
        config = yaml.safe_load(f)
    _apply_env_overrides(config)
    # Resolve database path relative to project root
    db_path = config.get("database", {}).get("path", "data/papers.db")
    if not Path(db_path).is_absolute():
        config["database"]["path"] = str(root / db_path)
    return config


def get_env(key: str) -> str:
    """Read from os.environ. Raises ValueError if the key is missing."""
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


def setup_logging(level: str = "INFO"):
    """Configure project-wide logging. Call once at startup."""
    log_level = getattr(logging, level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger().setLevel(log_level)
