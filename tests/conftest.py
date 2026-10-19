"""Pytest configuration for SwissBioPics MCP tests."""
import sys
import os

# Ensure src is on the path so tests can import the package directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
