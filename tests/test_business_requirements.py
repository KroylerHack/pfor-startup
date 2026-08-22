from pfor.api.auth import hash_password, verify_password
from pfor.core.config import Settings
from pfor.schemas.strategy import StrategyRequest


def test_settings_include_postgres_and_ollama_config():
    settings = Settings(
        _env_file=None,
        POSTGRES_SERVER="100.105.40.29",
        POSTGRES_PORT=5432,
        POSTGRES_USER="pfor_user",
        POSTGRES_PASSWORD="pfor_password",
        POSTGRES_DB="pfor_db",
        OLLAMA_BASE_URL="http://100.105.40.29:11434",
        OLLAMA_MODEL="qwen2.5:3b",
    )

    assert settings.postgres_server == "100.105.40.29"
    assert settings.postgres_port == 5432
    assert settings.database_url.startswith("postgresql+psycopg2://")
    assert settings.ollama_base_url == "http://100.105.40.29:11434"
    assert settings.ollama_model == "qwen2.5:3b"


def test_strategy_request_uses_new_api_contract():
    payload = StrategyRequest.model_validate({
        "prompt_text": "Нужно повысить конверсию сайта B2B с 4% до 8% за квартал.",
        "language": "ru",
    })

    assert payload.prompt_text.startswith("Нужно")
    assert payload.language == "ru"


def test_passwords_are_hashed_and_verifiable():
    plain = "StrongPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$")
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False
