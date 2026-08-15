from app.core.config import Settings


def test_mongodb_config_defaults():
    settings = Settings()
    assert settings.MONGO_URI is not None
    assert settings.MONGO_DB_NAME == "threat_atlas"
    assert "mongodb://" in settings.MONGO_URI


def test_mongodb_config_custom_values(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://test_host:27017")
    monkeypatch.setenv("MONGO_DB_NAME", "test_db")

    custom_settings = Settings()
    assert custom_settings.MONGO_URI == "mongodb://test_host:27017"
    assert custom_settings.MONGO_DB_NAME == "test_db"
