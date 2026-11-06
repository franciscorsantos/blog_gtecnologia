from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import login_user, logout_user, current_user
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/cms/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("cms.dashboard"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("cms.dashboard"))

        flash("Credenciais inválidas. Verifique seu usuário/e-mail e senha NOC.", "error")

    return render_template("cms/login.html")


@auth_bp.route("/cms/logout")
def logout():
    logout_user()
    flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("auth.login"))

