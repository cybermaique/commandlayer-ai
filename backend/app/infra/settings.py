import os


def database_url() -> str:
    user = os.getenv("DB_USER", "commandlayer")
    password = os.getenv("DB_PASSWORD", "commandlayer")
    host = os.getenv("DB_HOST", "postgres")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "commandlayer")

    # psycopg v3 driver
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
