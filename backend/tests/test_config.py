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


def test_production_mongodb_and_cors_env(monkeypatch):
    monkeypatch.setenv("MONGODB_URL", "mongodb+srv://user:pass@cluster.mongodb.net/test?retryWrites=true")
    monkeypatch.setenv("DATABASE_NAME", "prod_threat_atlas")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://threatatlas.vercel.app, https://custom-domain.com")

    settings = Settings()
    assert settings.MONGO_URI == "mongodb+srv://user:pass@cluster.mongodb.net/test?retryWrites=true"
    assert settings.MONGODB_URL == "mongodb+srv://user:pass@cluster.mongodb.net/test?retryWrites=true"
    assert settings.MONGO_DB_NAME == "prod_threat_atlas"
    assert settings.DATABASE_NAME == "prod_threat_atlas"
    assert "https://threatatlas.vercel.app" in settings.ALLOWED_ORIGINS
    assert "https://custom-domain.com" in settings.ALLOWED_ORIGINS

