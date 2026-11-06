import os
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def resolve_database_uri() -> str:
    """
    Resolve a URI do banco de dados MySQL via SQLAlchemy + PyMySQL.
    Tenta garantir que o schema exista no servidor MySQL configurado.
    Se o MySQL não estiver acessível localmente e ALLOW_SQLITE_FALLBACK=true,
    faz fallback seguro para SQLite local sem interromper a execução.
    """
    db_url = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/blog_gtecnologia?charset=utf8mb4",
    )
    allow_fallback = os.environ.get("ALLOW_SQLITE_FALLBACK", "true").lower() == "true"

    if db_url.startswith("mysql"):
        try:
            import pymysql

            parsed = urlparse(db_url.replace("mysql+pymysql://", "mysql://"))
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            user = parsed.username or "root"
            password = parsed.password or ""
            db_name = (parsed.path or "/blog_gtecnologia").lstrip("/").split("?")[0]

            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset="utf8mb4",
                connect_timeout=2,
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.commit()
            conn.close()
            return db_url
        except Exception as exc:
            if allow_fallback:
                sqlite_path = os.path.join(BASE_DIR, "blog_gtecnologia.db")
                return f"sqlite:///{sqlite_path}"
            raise
    return db_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "goose-tecnologia-noc-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        **(
            {"connect_args": {"timeout": 15}}
            if SQLALCHEMY_DATABASE_URI.startswith("sqlite")
            else {}
        ),
    }
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
