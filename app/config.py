from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str ="postgresql+psycopg2://clausewatch:clausewatch@localhost:5432/clausewatch"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "clausewatch"
    minio_secret_key: str = "clausewatch123"
    minio_bucket_name: str = "clausewatch-contracts"
    minio_region: str = "us-east-1"
    openai_api_key: str = ""
    resend_api_key: str =""
    document_encryption_key: str = ""
    download_link_secret: str = ""
    cron_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# This reads .env at startup and gives a typed, validated config
# instead of scattering os.environ.get() calls throughout the codebase.