import os
import sqlite3
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine
from config import Config
from app.extensions import db, login_manager


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Ativa modo WAL e busy_timeout no SQLite para alta concorrência de leituras e escritas."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.Error:
            # Fallback seguro caso o filesystem (ex: NFS no PythonAnywhere) não suporte mmap do WAL
            cursor.execute("PRAGMA journal_mode=DELETE;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.cms import cms_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cms_bp)

    with app.app_context():
        from app import models  # noqa: F401
        from app.seed import seed_database

        db.create_all()
        seed_database()

    return app

