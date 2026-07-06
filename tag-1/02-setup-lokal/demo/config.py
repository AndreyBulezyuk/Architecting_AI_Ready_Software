"""Connection settings for the local training stack.

Every value can be overridden via environment variables (e.g. NEO4J_URI).
The defaults match the root docker-compose.yml.
"""

from pydantic_settings import BaseSettings


class StackSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    postgres_dsn: str = "postgresql://postgres:trainingpass@localhost:5432/aiready"

    aws_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "eu-west-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"


settings = StackSettings()
