from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Timon"
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    DATABASE_URL: str | None = None

    # Huginn configuration
    HUGINN_URL: str
    HUGINN_ADMIN_EMAIL: str
    HUGINN_ADMIN_PASSWORD: str
    HUGINN_ADMIN_USERNAME: str

    # App configuration
    APP_HOST: str
    EXTERNAL_APP_HOST: str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'forbid'  # Запрещает дополнительные поля

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings() 