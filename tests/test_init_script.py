"""Regression checks for setup-script failure propagation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_init_uses_pipefail_and_safe_optional_environment_values():
    script = (ROOT / "init.sh").read_text(encoding="utf-8")

    assert "set -euo pipefail" in script
    assert '"${1:-}"' in script
    assert '"${TUSHARE_TOKEN:-}"' in script


def test_default_pytest_configuration_excludes_live_integration_tests():
    config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "not integration" in config
    assert "requires live APIs" in config
