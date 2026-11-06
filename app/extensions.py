from functools import wraps
from flask import session, redirect, url_for, request, flash, g
from werkzeug.local import LocalProxy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

try:
    from flask_login import (
        LoginManager,
        UserMixin,
        login_user,
        logout_user,
        login_required,
        current_user,
    )

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = (
        "Autentique-se com suas credenciais do NOC Goose para acessar o painel editorial."
    )
    login_manager.login_message_category = "warning"
except ImportError:
    # Compatibilidade completa caso flask_login ainda não esteja instalado no ambiente
    class UserMixin:
        @property
        def is_authenticated(self) -> bool:
            return True

        @property
        def is_active(self) -> bool:
            return True

        @property
        def is_anonymous(self) -> bool:
            return False

        def get_id(self) -> str:
            return str(self.id)

    class _AnonymousUser:
        is_authenticated = False
        is_active = False
        is_anonymous = True
        id = None
        display_name = "Visitante"
        role_title = ""

    class _FallbackLoginManager:
        login_view = "auth.login"
        login_message = "Autentique-se com suas credenciais do NOC Goose para acessar o painel editorial."
        login_message_category = "warning"
        _user_callback = None

        def init_app(self, app):
            @app.before_request
            def _load_current_user():
                uid = session.get("_user_id")
                if uid and self._user_callback:
                    g._login_user = self._user_callback(uid) or _AnonymousUser()
                else:
                    g._login_user = _AnonymousUser()

            @app.context_processor
            def _inject_user():
                return {"current_user": current_user}

        def user_loader(self, callback):
            self._user_callback = callback
            return callback

    login_manager = _FallbackLoginManager()

    def _get_user():
        if not hasattr(g, "_login_user"):
            uid = session.get("_user_id")
            if uid and login_manager._user_callback:
                g._login_user = login_manager._user_callback(uid) or _AnonymousUser()
            else:
                g._login_user = _AnonymousUser()
        return g._login_user

    current_user = LocalProxy(_get_user)

    def login_user(user, remember=False):
        session["_user_id"] = user.get_id()
        session.permanent = bool(remember)
        g._login_user = user
        return True

    def logout_user():
        session.pop("_user_id", None)
        g._login_user = _AnonymousUser()
        return True

    def login_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(login_manager.login_message, login_manager.login_message_category)
                return redirect(url_for(login_manager.login_view, next=request.path))
            return func(*args, **kwargs)

        return decorated_view
