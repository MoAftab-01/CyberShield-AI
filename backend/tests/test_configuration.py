"""Settings-only regressions: synthetic dotenv files, no app or DB startup."""

import ast
import importlib.util
import os
from pathlib import Path
import socket
import sqlite3
import sys

import pytest
from pydantic import ValidationError
import sqlalchemy


pytestmark = pytest.mark.configuration_only

BACKEND_DIR = Path(__file__).resolve().parents[1]
CONFIG_SOURCE = BACKEND_DIR / "app" / "core" / "config.py"
ISOLATED_ROOT = Path.cwd()
FIXTURE_DATABASE_URL = "postgresql://configuration.invalid/configuration_test"
FIXTURE_SIGNING_VALUE = "configuration-fixture-" * 3


def _load_module(path, monkeypatch):
    name = "_phase1a_configuration_fixture"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def configuration(tmp_path, monkeypatch):
    def forbidden_io(*args, **kwargs):
        pytest.fail("Configuration tests must not connect to networks or databases.")

    monkeypatch.setattr(socket.socket, "connect", forbidden_io)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden_io)
    monkeypatch.setattr(socket, "create_connection", forbidden_io)
    monkeypatch.setattr(sqlite3, "connect", forbidden_io)
    monkeypatch.setattr(sqlalchemy, "create_engine", forbidden_io)
    monkeypatch.setattr(sqlalchemy.engine, "create_engine", forbidden_io)

    source = CONFIG_SOURCE.read_text(encoding="utf-8")
    settings_class = next(
        node for node in ast.parse(source).body
        if isinstance(node, ast.ClassDef) and node.name == "Settings"
    )
    for node in settings_class.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            monkeypatch.delenv(node.target.id, raising=False)

    project = tmp_path / "project"
    copied_config = project / "backend" / "app" / "core" / "config.py"
    copied_config.parent.mkdir(parents=True)
    copied_config.write_text(source, encoding="utf-8")
    dotenv = project / "backend" / ".env"
    dotenv.write_text(
        "APP_NAME=Configuration fixture \u00fc\n"
        "ENVIRONMENT=production\n"
        f"DATABASE_URL={FIXTURE_DATABASE_URL}\n"
        f"JWT_SECRET={FIXTURE_SIGNING_VALUE}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    before = set(sys.modules)
    module = _load_module(copied_config, monkeypatch)
    module._fixture_imports = set(sys.modules) - before
    return module, project, dotenv


def _runtime_settings(module, **overrides):
    values = {
        "_env_file": None,
        "ENVIRONMENT": "production",
        "DATABASE_URL": FIXTURE_DATABASE_URL,
        "JWT_SECRET": FIXTURE_SIGNING_VALUE,
    }
    values.update(overrides)
    return module.Settings(**values)


@pytest.mark.parametrize("directory", ["root", "backend", "unrelated"])
def test_dotenv_resolution_is_independent_of_working_directory(
    configuration, monkeypatch, directory
):
    module, project, dotenv = configuration
    cwd = {
        "root": project,
        "backend": project / "backend",
        "unrelated": project / "other",
    }[directory]
    cwd.mkdir(exist_ok=True)
    # A conflicting cwd-local .env must never replace backend/.env.
    if cwd != dotenv.parent:
        (cwd / ".env").write_text("APP_NAME=Wrong cwd configuration\n", encoding="utf-8")
    monkeypatch.chdir(cwd)

    settings = module.Settings()
    assert module.Settings.model_config["env_file"] == dotenv
    assert settings.APP_NAME == "Configuration fixture \u00fc"
    assert settings.DATABASE_URL == FIXTURE_DATABASE_URL
    assert settings.JWT_SECRET == FIXTURE_SIGNING_VALUE

    # Exercise the import-time singleton as well as a fresh Settings instance.
    imported = _load_module(project / "backend/app/core/config.py", monkeypatch)
    assert imported.settings.APP_NAME == settings.APP_NAME
    assert imported.settings.DATABASE_URL == settings.DATABASE_URL


def test_process_environment_overrides_dotenv(configuration, monkeypatch):
    module, _, _ = configuration
    database_url = "postgresql+psycopg2://override.invalid/configuration_test?sslmode=require"
    signing_value = "process-fixture-" * 4
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET", signing_value)
    settings = module.Settings()
    assert settings.DATABASE_URL == database_url
    assert settings.JWT_SECRET == signing_value


def test_explicit_settings_override_process_environment(configuration, monkeypatch):
    module, _, _ = configuration
    monkeypatch.setenv("DATABASE_URL", "not-a-database-url")
    monkeypatch.setenv("JWT_SECRET", "invalid-fixture")
    settings = _runtime_settings(module)
    assert settings.DATABASE_URL == FIXTURE_DATABASE_URL
    assert settings.JWT_SECRET == FIXTURE_SIGNING_VALUE


@pytest.mark.parametrize("field", ["DATABASE_URL", "JWT_SECRET"])
def test_missing_runtime_settings_are_required(configuration, field):
    module, _, _ = configuration
    values = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": FIXTURE_DATABASE_URL,
        "JWT_SECRET": FIXTURE_SIGNING_VALUE,
    }
    del values[field]
    with pytest.raises(ValidationError) as caught:
        module.Settings(_env_file=None, **values)
    errors = caught.value.errors(include_input=False)
    assert any(error["loc"] == (field,) and error["type"] == "missing" for error in errors)


def test_missing_dotenv_fails_during_import(configuration, monkeypatch):
    _, project, dotenv = configuration
    dotenv.unlink()  # Synthetic fixture only; never touches backend/.env.
    with pytest.raises(ValidationError):
        _load_module(project / "backend/app/core/config.py", monkeypatch)


@pytest.mark.parametrize("environment", ["development", "staging", "production", "custom"])
@pytest.mark.parametrize("field", ["DATABASE_URL", "JWT_SECRET"])
def test_test_only_values_are_rejected_outside_tests(configuration, environment, field):
    module, _, _ = configuration
    invalid = "sqlite:///:memory:" if field == "DATABASE_URL" else "short-fixture"
    with pytest.raises(ValidationError, match=field):
        _runtime_settings(module, ENVIRONMENT=environment, **{field: invalid})


@pytest.mark.parametrize("value", ["", " " * 40, "x" * 31, " " + "x" * 30 + " "],
                         ids=["empty", "whitespace", "too-short", "padded-short"])
def test_invalid_runtime_signing_values_are_rejected(configuration, value):
    module, _, _ = configuration
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _runtime_settings(module, JWT_SECRET=value)


def test_runtime_accepts_signing_value_at_minimum_length(configuration):
    module, _, _ = configuration
    value = "x" * module.MIN_JWT_SECRET_LENGTH
    settings = _runtime_settings(module, JWT_SECRET=value)
    assert settings.JWT_SECRET == value


@pytest.mark.parametrize("field,value", [
    ("DATABASE_URL", "sqlite:///:memory:"),
    ("JWT_SECRET", "short-fixture"),
])
def test_invalid_process_values_do_not_fall_back_to_dotenv(configuration, monkeypatch, field, value):
    module, _, _ = configuration
    monkeypatch.setenv(field, value)
    with pytest.raises(ValidationError, match=field):
        module.Settings()


@pytest.mark.parametrize("database_url", [
    "", "not-a-url", "mysql://configuration.invalid/configuration_test",
    "postgresql://configuration.invalid", "postgresql:///configuration_test",
    "postgresql://configuration.invalid:invalid/configuration_test",
])
def test_invalid_runtime_database_urls_are_rejected(configuration, database_url):
    module, _, _ = configuration
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        _runtime_settings(module, DATABASE_URL=database_url)


def test_explicit_test_settings_allow_isolated_sqlite(configuration, tmp_path, capsys):
    module, _, _ = configuration
    database = tmp_path / "isolated.db"
    settings = _runtime_settings(
        module, ENVIRONMENT=" TEST ", DATABASE_URL=f"sqlite:///{database}",
        JWT_SECRET="short-fixture",
    )
    assert settings.ENVIRONMENT == "test"
    assert not database.exists()
    assert "JWT_SECRET is shorter than" in capsys.readouterr().out


def test_empty_signing_value_is_rejected_even_in_tests(configuration):
    module, _, _ = configuration
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _runtime_settings(module, ENVIRONMENT="test", DATABASE_URL="sqlite://", JWT_SECRET="")


def test_validation_messages_hide_settings_inputs(configuration):
    module, _, _ = configuration
    sensitive_marker = "private-fixture-marker"
    with pytest.raises(ValidationError) as caught:
        _runtime_settings(module, DATABASE_URL=sensitive_marker, JWT_SECRET=sensitive_marker)
    assert sensitive_marker not in str(caught.value)
    assert FIXTURE_SIGNING_VALUE not in str(caught.value)


@pytest.mark.parametrize("filename", ["faiss_store.py", "bm25_store.py", "index_meta.py"])
def test_rag_storage_resolves_only_inside_isolated_test_root(monkeypatch, filename):
    monkeypatch.chdir(ISOLATED_ROOT)
    configured = Path(os.environ["VECTOR_DB_DIR"]).resolve()
    assert configured == ISOLATED_ROOT / "vector_db"
    assert not configured.is_relative_to(BACKEND_DIR)

    # Evaluate only path declarations; never import RAG, providers, or the app.
    path = BACKEND_DIR / "app/rag" / filename
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id in
                           {"_BASE_DIR", "_VECTOR_DB_DIR"} for target in node.targets)]
    namespace = {"Path": Path, "os": os, "__file__": str(path)}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), str(path), "exec"), namespace)
    assert namespace["_VECTOR_DB_DIR"].resolve() == configured
    assert all((ISOLATED_ROOT / name).is_dir()
               for name in ("vector_db", "knowledge_base", "uploads"))


def test_configuration_checks_never_import_application_or_database(configuration):
    module, _, _ = configuration
    forbidden = ("app.main", "app.database", "app.db", "app.rag", "app.services")
    assert not any(name == prefix or name.startswith(prefix + ".")
                   for name in module._fixture_imports for prefix in forbidden)
