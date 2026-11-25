import ast
import subprocess
import sys
import types
import urllib.request
from pathlib import Path

import nbformat
import pytest
from IPython import display as ipython_display


@pytest.mark.parametrize("source", ["文字列", "棋譜ファイル"])
@pytest.mark.parametrize("setup", ["リリース", "手元ファイル"])
@pytest.mark.parametrize(
    "use_ratings,use_clocks", [(True, False), (False, False), (True, True), (False, True)]
)
def test_demo_cells_locally(model_directory, tmp_path, monkeypatch, source, setup, use_ratings, use_clocks):
    root = Path(__file__).parents[1]
    notebook = nbformat.read(root / "notebooks/demo.ipynb", as_version=4)
    nbformat.validate(notebook)
    upload_batches = [
        {
            "shogi_human_policy-0.1.0.dev0-py3-none-any.whl": b"wheel-upload-test",
            **{
                name: (model_directory / name).read_bytes()
                for name in ("manifest.json", "policy.safetensors")
            },
        },
        {"opening.kif": (root / "examples/records/opening.kif").read_bytes()},
    ]
    uploads = iter(upload_batches if setup == "手元ファイル" else upload_batches[1:])
    colab = types.ModuleType("google.colab")
    colab.files = types.SimpleNamespace(upload=lambda: next(uploads))
    monkeypatch.setitem(sys.modules, "google.colab", colab)
    calls = []
    monkeypatch.setattr(subprocess, "check_call", lambda args: calls.append(args))
    downloads = []

    def retrieve(url, target):
        downloads.append(url)
        Path(target).write_bytes((model_directory / Path(target).name).read_bytes())

    monkeypatch.setattr(urllib.request, "urlretrieve", retrieve)
    shown = []
    monkeypatch.setattr(ipython_display, "display", lambda item: shown.append(item))
    monkeypatch.chdir(tmp_path)
    namespace = {}
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        assert not cell.outputs and cell.execution_count is None
        code = cell.source.replace('input_mode = "文字列"', f'input_mode = "{source}"')
        code = code.replace('setup_mode = "リリース"', f'setup_mode = "{setup}"')
        code = code.replace('moves_played = ""', 'moves_played = "1"')
        code = code.replace("use_ratings = True", f"use_ratings = {use_ratings}")
        code = code.replace("use_clocks = False", f"use_clocks = {use_clocks}")
        code = code.replace("white_seconds = 60", "white_seconds = 90")
        ast.parse(code)
        exec(compile(code, "demo.ipynb", "exec"), namespace)
    assert len(calls) == 1 and calls[0][1:4] == ["-m", "pip", "install"]
    if setup == "リリース":
        assert calls[0][-1] == "git+https://github.com/nyoki-mtl/shogi-human-policy.git@v0.1.1"
        assert downloads == [
            f"https://github.com/nyoki-mtl/shogi-human-policy/releases/download/v0.1.1/{name}"
            for name in ("manifest.json", "policy.safetensors")
        ]
    else:
        assert not downloads
    assert namespace["position"].moves == ("7g7f",)
    assert namespace["conditions"].ratings == ((1800, 1500) if use_ratings else None)
    assert namespace["conditions"].clocks == ((90, 60) if use_clocks else None)
    assert len(namespace["rows"]) == 5
    assert all(row["notation"].startswith("△") for row in namespace["rows"])
    assert any(isinstance(item, ipython_display.SVG) for item in shown)
