from generator.app import generate
from hydra import compose, initialize_config_module, initialize

import pytest

def test_basic_generation() -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="config")
        result = generate(cfg)
        assert len(result) > 0
