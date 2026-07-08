"""Connection settings for the local training stack (same pattern as demo/config.py)."""

from pydantic_settings import BaseSettings


class StackSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "eu-west-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"


settings = StackSettings()
