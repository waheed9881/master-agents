"""Shared pytest fixtures for AI Agent OS."""
import pytest


@pytest.fixture(autouse=True)
def disable_rate_limiting_by_default(settings):
    """Keep existing tests deterministic; phase 16 tests opt in explicitly."""
    settings.RATE_LIMITING_ENABLED = False
