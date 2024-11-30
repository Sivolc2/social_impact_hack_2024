import pytest
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Common fixtures can be added here
@pytest.fixture(autouse=True)
def env_setup():
    """Setup test environment variables"""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    yield
    # Cleanup
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"] 