from app.config import Config


def test_defaults_when_environment_is_empty():
    config = Config.from_lookup(lambda _: None)

    assert config.port == 8080
    assert config.database_url == "sqlite://data/local_rag.db"
    assert config.qdrant_url == "http://localhost:6333"
    assert config.ollama_url == "http://localhost:11434"
    assert config.admin_secret == "secret_admin_key"
    assert config.env == "local"


def test_supplied_values_override_defaults():
    values = {
        "PORT": "9090",
        "DATABASE_URL": "sqlite://test.db",
        "QDRANT_URL": "http://qdrant.test:6333",
        "OLLAMA_URL": "http://ollama.test:11434",
        "ADMIN_SECRET": "s3cret",
        "ENV": "prod",
    }

    config = Config.from_lookup(values.get)

    assert config.port == 9090
    assert config.database_url == "sqlite://test.db"
    assert config.qdrant_url == "http://qdrant.test:6333"
    assert config.ollama_url == "http://ollama.test:11434"
    assert config.admin_secret == "s3cret"
    assert config.env == "prod"


def test_unparseable_port_falls_back_to_default():
    assert Config.from_lookup({"PORT": "not-a-port"}.get).port == 8080


def test_app_name_defaults_to_localrag():
    config = Config.from_lookup(lambda _: None)

    assert config.app_name == "LocalRAG"
    assert config.app_short_description is None


def test_app_name_and_short_description_override_defaults():
    values = {
        "APP_NAME": "SAVI",
        "APP_SHORT_DESCRIPTION": "SCB AI Virtual Intelligence",
    }

    config = Config.from_lookup(values.get)

    assert config.app_name == "SAVI"
    assert config.app_short_description == "SCB AI Virtual Intelligence"
