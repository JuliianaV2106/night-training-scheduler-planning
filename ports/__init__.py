"""Inbound Ports Package & Dynamic Loader for `ports/in/` (allowing clean imports without `in` keyword clash)."""

import importlib.util
from pathlib import Path
from typing import Any

_IN_DIR = Path(__file__).parent / "in"


def load_inbound_port_module(module_basename: str) -> Any:
    """Loads `ports/in/<module_basename>.py` cleanly without hitting Python's `in` keyword."""
    file_path = _IN_DIR / f"{module_basename}.py"
    spec = importlib.util.spec_from_file_location(f"ports_in_{module_basename}", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load inbound port module from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
