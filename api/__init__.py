"""
PoliSim REST API Package
HTTP endpoints for fiscal policy analysis.
"""

from api.rest_server import create_api_app, run_api_server
from api.client import PoliSimAPIClient

__all__ = [
    'create_api_app',
    'run_api_server',
    'PoliSimAPIClient',
]
