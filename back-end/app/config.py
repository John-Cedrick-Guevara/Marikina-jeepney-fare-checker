from pydantic import BaseSettings, SettingsConfigDict


class FairSettings(BaseSettings):
    supabase_url: str
    supabase_connection_string: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
