import hashlib
import json
from importlib.resources import files
from pathlib import Path

import numpy as np
import pytest
import torch
from safetensors.torch import save_file

from shogi_human_policy import PolicyModel
from shogi_human_policy.network import ModelSpec, PolicyNetwork

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def reference():
    torch.set_num_threads(2)
    with np.load(FIXTURES / "jax-reference.npz", allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


@pytest.fixture(scope="session")
def architecture():
    return json.loads((FIXTURES / "config.json").read_text())


@pytest.fixture(scope="session")
def network(reference, architecture):
    weights = {
        k.removeprefix("param:"): torch.tensor(v) for k, v in reference.items() if k.startswith("param:")
    }
    return PolicyNetwork(ModelSpec.from_dict(architecture), weights)


@pytest.fixture
def model_directory(tmp_path, network, architecture):
    path = tmp_path / "policy.safetensors"
    save_file(network.w, str(path))
    manifest = dict(
        schema="shogi-human-policy-v1",
        architecture=architecture,
        selection="ema",
        model_version="test-model",
        policy_labels=1496,
        history_frames=8,
        history_padding="zero_board_hand31",
        draw_reference_plies=320,
        conditioning=dict(
            rating_order=["self", "opponent"],
            rating_center=1500,
            rating_scale=1500,
            time_encoding="log1p(seconds)/log1p(3600)",
            missing="paired rating and clock masks after normalization",
        ),
        files={path.name: hashlib.sha256(path.read_bytes()).hexdigest()},
        geometry_sha256=hashlib.sha256(
            files("shogi_human_policy").joinpath("geometry.npz").read_bytes()
        ).hexdigest(),
    )
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path


@pytest.fixture
def model(model_directory):
    return PolicyModel.from_directory(model_directory)
