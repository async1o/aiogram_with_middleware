from typing import List

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Setings(BaseSettings):

    TOKEN: SecretStr
    DB_NAME: str
    DB_PASS: int
    DB_PORT: int
    DB_HOST: str
    DB_USER: str
    ADMIN_IDS: List[int] = []

    @property
    def get_db_url(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
 

    model_config = SettingsConfigDict(env_file='.env')

settings = Setings()