"""WSGI entry point for the canonical ML-backed API in backend/app.py."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

active_api = Path(__file__).with_name("app.py")
spec = spec_from_file_location("saferoute_active_api", active_api)
module = module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app
