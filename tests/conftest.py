# tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return '''
def hello_world():
    print("Hello, World!")
    return "Hello, World!"

def add_numbers(a, b):
    return a + b
'''

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "analysis": {
            "security": True,
            "performance": True,
            "style": True,
            "complexity": True
        },
        "rules": {
            "styleGuide": "pep8",
            "maxLineLength": 120,
            "maxComplexity": 10
        }
    }

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    def _create_temp_file(content, filename="test.py"):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return str(file_path)
    return _create_temp_file