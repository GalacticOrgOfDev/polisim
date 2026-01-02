import types
import builtins
import importlib
import main
import sys


def test_parse_ver_and_version_ok():
    assert main.parse_ver("1.2.3") == (1, 2, 3)
    assert main.is_version_ok("1.2.3", "1.2.0") is True
    assert main.is_version_ok("1.2.0", "1.2.3") is False


def test_ensure_dependencies_no_missing(monkeypatch):
    # Fake a couple of modules with acceptable versions
    fake_mods = {
        "foo": types.SimpleNamespace(__version__="2.0.0"),
        "bar": types.SimpleNamespace(__version__="1.5.0"),
    }

    def fake_import_module(name):
        if name in fake_mods:
            return fake_mods[name]
        raise ImportError()

    def fake_metadata_version(pkg_name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    monkeypatch.setattr(importlib.metadata, "version", fake_metadata_version)

    deps = [
        ("foo", "foo", "Foo", "1.0.0", False),
        ("bar", "bar", "Bar", "1.5.0", False),
    ]

    assert main.ensure_dependencies(auto_install=False, headless=True, deps=deps) is True


def test_ensure_dependencies_prompts_on_missing(monkeypatch):
    # Simulate missing dependency and decline install
    def fake_import_module(name):
        raise ImportError()

    def fake_metadata_version(pkg_name):
        raise importlib.metadata.PackageNotFoundError

    inputs = iter(["n"])

    def fake_input(prompt):
        return next(inputs)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    monkeypatch.setattr(importlib.metadata, "version", fake_metadata_version)
    monkeypatch.setattr(builtins, "input", fake_input)

    deps = [("missing", "missing", "Missing", "1.0.0", False)]
    assert main.ensure_dependencies(auto_install=False, headless=True, deps=deps) is False


def test_check_data_ingestion_ok(monkeypatch):
    class FakeScraper:
        def __init__(self, use_cache=True):
            pass

        def get_current_us_budget_data(self):
            return {
                'cache_used': False,
                'freshness_hours': 1.0,
                'data_source': 'test-live',
                'checksum': 'abc123',
            }

    fake_module = types.SimpleNamespace(CBODataScraper=FakeScraper)
    monkeypatch.setitem(sys.modules, 'core.cbo_scraper', fake_module)

    assert main.check_data_ingestion(headless=True) is True


def test_check_data_ingestion_fails_on_stale_cache(monkeypatch):
    class FakeScraper:
        def __init__(self, use_cache=True):
            pass

        def get_current_us_budget_data(self):
            return {
                'cache_used': True,
                'freshness_hours': 100.0,
                'data_source': 'test-cache',
                'checksum': 'abc123',
            }

    fake_module = types.SimpleNamespace(CBODataScraper=FakeScraper)
    monkeypatch.setitem(sys.modules, 'core.cbo_scraper', fake_module)

    assert main.check_data_ingestion(headless=True) is False


def test_check_data_ingestion_fails_on_missing_checksum(monkeypatch):
    class FakeScraper:
        def __init__(self, use_cache=True):
            pass

        def get_current_us_budget_data(self):
            return {
                'cache_used': False,
                'freshness_hours': 1.0,
                'data_source': 'test-live',
                'checksum': None,
            }

    fake_module = types.SimpleNamespace(CBODataScraper=FakeScraper)
    monkeypatch.setitem(sys.modules, 'core.cbo_scraper', fake_module)

    assert main.check_data_ingestion(headless=True) is False


def test_check_data_ingestion_fails_on_schema(monkeypatch):
    class FakeScraper:
        def __init__(self, use_cache=True):
            pass

        def get_current_us_budget_data(self):
            return {
                'cache_used': False,
                'freshness_hours': 1.0,
                'data_source': 'test-live',
                'checksum': 'abc123',
                'schema_valid': False,
                'validation_errors': ['missing field: gdp'],
            }

    fake_module = types.SimpleNamespace(CBODataScraper=FakeScraper)
    monkeypatch.setitem(sys.modules, 'core.cbo_scraper', fake_module)

    assert main.check_data_ingestion(headless=True) is False
