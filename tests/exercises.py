"""The exercise modules, loaded by path: their folders (02/, 03/) are not packages."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ex2 = _load("ex2", "02/ex2.py")
ex3 = _load("ex3", "03/ex3.py")
both = pytest.mark.parametrize("module", [ex2, ex3], ids=["ex2", "ex3"])
