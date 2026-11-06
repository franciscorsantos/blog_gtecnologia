import os
import re
import unicodedata
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
    Response,
    json,
)
from app.extensions import db, login_required, current_user
from app.models import Article, Category, Tag, User, Lead, MediaAsset, AuditLog
from app.utils.markdown_renderer import render_article_markdown

cms_bp = Blueprint("cms", __name__)


def make_slug(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or f"ensaio-{int(datetime.now(timezone.utc).timestamp())}"


def log_cms_action(action: str, target_slug: str = "", details: str = "") -> None:
    actor = getattr(current_user, "display_name", None) or "Francisco & Wandeson"
    entry = AuditLog(
        action=action,
        actor_name=actor,
        target_slug=target_slug,
        details=details,
    )
    db.session.add(entry)


@cms_bp.route("/cms")
@login_required
def dashboard():
    all_articles = Article.query.order_by(
        Article.is_hero.desc(), Article.published_at.desc()
    ).all()

    published_count = sum(1 for a in all_articles if a.status == "published")
    draft_count = sum(1 for a in all_articles if a.status == "draft")
    review_count = sum(1 for a in all_articles if a.status == "review")
    archived_count = sum(1 for a in all_articles if a.status == "archived")

    total_views = sum(a.views_count or 0 for a in all_articles)
    formatted_total_views = (
        f"{total_views / 1000:.1f}k" if total_views >= 1000 else str(total_views)
    )

    avg_reading = (
        round(
            sum(a.reading_time_minutes or 7 for a in all_articles) / len(all_articles),
            1,
        )
        if all_articles
        else 7.4
    )

    categories = Category.query.order_by(Category.id.asc()).all()
    tags = Tag.query.order_by(Tag.name.asc()).all()
    users = User.query.order_by(User.id.asc()).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(25).all()
    media_assets = MediaAsset.query.order_by(MediaAsset.uploaded_at.desc()).all()
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(30).all()

    active_article = next((a for a in all_articles if a.is_hero), None) or (
        all_articles[0] if all_articles else None
    )

    return render_template(
        "cms/dashboard.html",
        articles=all_articles,
        active_article=active_article,
        published_count=published_count,
        draft_count=draft_count,
        review_count=review_count,
        archived_count=archived_count,
        total_count=len(all_articles),
        formatted_total_views=formatted_total_views,
        avg_reading=avg_reading,
        categories=categories,
        tags=tags,
        users=users,
        leads=leads,
        media_assets=media_assets,
        audit_logs=audit_logs,
    )


@cms_bp.route("/cms/editor")
@cms_bp.route("/cms/editor/<int:article_id>")
@login_required
def editor(article_id: int = None):
    article = None
    if article_id:
        article = db.session.get(Article, article_id)
    else:
        # Se nenhum ID foi passado e ?new=1 não está presente, pode carregar um template inicial em branco ou o artigo BGP de referência se solicitado
        if request.args.get("new") != "1":
            article = Article.query.filter_by(
                slug="arquitetura-bgp-multihomed-transito-ip"
            ).first()

    categories = Category.query.order_by(Category.id.asc()).all()
    all_tags = Tag.query.order_by(Tag.name.asc()).all()
    users = User.query.order_by(User.id.asc()).all()

    initial_markdown = article.content_markdown if article else (
        "# Novo Ensaio Técnico de Engenharia Telecom\n\n"
        ":::noc-warning\n"
        "title: Aviso Crítico de Operação em Produção (NOC)\n"
        "Valide os filtros de roteamento em laboratório antes da janela de manutenção.\n"
        ":::\n\n"
        "## 1. Topologia & Contexto Operacional\n\n"
        "Descreva aqui a arquitetura física e lógica do cenário de rede.\n\n"
        "```mikrotik|MikroTik RouterOS v7 Script\n"
        "/routing bgp template\n"
        "add name=\"GOOSE-CORE\" as=263481 router-id=10.254.0.1 use-bfd=yes\n"
        "```\n"
    )
    rendered_preview, toc_items = render_article_markdown(initial_markdown)

    return render_template(
        "cms/editor.html",
        article=article,
        categories=categories,
        all_tags=all_tags,
        users=users,
        initial_markdown=initial_markdown,
        rendered_preview=rendered_preview,
        toc_items=toc_items,
    )


@cms_bp.route("/api/cms/preview", methods=["POST"])
@login_required
def api_preview_markdown():
    payload = request.get_json(silent=True) or {}
    md_text = payload.get("content_markdown") or ""
    rendered_html, toc_items = render_article_markdown(md_text)

    words = [w for w in re.sub(r"[#*`~>\[\]\(\)_-]", " ", md_text).split() if w.strip()]
    word_count = len(words)
    reading_time = max(1, round(word_count / 180))
    script_blocks = len(re.findall(r"```", md_text)) // 2

    return jsonify(
        {
            "ok": True,
            "rendered_html": rendered_html,
            "toc_items": toc_items,
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "script_blocks_count": script_blocks,
        }
    )


@cms_bp.route("/api/cms/articles", methods=["POST"])
@login_required
def api_save_article():
    payload = request.get_json(silent=True) or {}
    article_id = payload.get("id")

    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "O título do ensaio é obrigatório."}), 400

    raw_slug = (payload.get("slug") or "").strip()
    slug = make_slug(raw_slug if raw_slug else title)

    if article_id:
        article = db.session.get(Article, int(article_id))
        if not article:
            return jsonify({"ok": False, "error": "Artigo não encontrado."}), 404
        # Evita colisão de slug com outro artigo
        existing = Article.query.filter(Article.slug == slug, Article.id != article.id).first()
        if existing:
            slug = f"{slug}-{article.id}"
    else:
        existing = Article.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp()) % 10000}"
        article = Article(slug=slug)
        db.session.add(article)

    article.title = title
    article.slug = slug
    article.subtitle = (payload.get("subtitle") or "").strip()
    article.summary = (payload.get("summary") or payload.get("meta_description") or "").strip()
    article.content_markdown = payload.get("content_markdown") or ""
    article.status = payload.get("status") or article.status or "draft"

    # Categoria
    cat_id = payload.get("category_id")
    cat_name = payload.get("category_name")
    if cat_id:
        article.category_id = int(cat_id)
    elif cat_name:
        cat = Category.query.filter_by(name=cat_name).first()
        if cat:
            article.category_id = cat.id

    # Autor
    author_key = payload.get("author_key") or "duo"
    article.author_key = author_key
    matched_user = User.query.filter_by(username=author_key).first()
    if matched_user:
        article.author_id = matched_user.id
        article.author_display = payload.get("author_display") or matched_user.display_name
        article.author_footer_label = f"{matched_user.display_name} • {matched_user.role_title}"
        article.author_role_badge = matched_user.role_title
    else:
        article.author_id = None
        author_labels = {
            "duo": ("Francisco & Wandeson", "Francisco & Wandeson", "Goose Founders"),
            "francisco": ("Francisco (CTO)", "Francisco • CTO", "Goose Founders"),
            "wandeson": ("Wandeson (CX)", "Wandeson • CX", "CX & Telecom Lead"),
            "guest": ("Tony Sanderson (Convidado)", "Participação Especial", "GOOCAST Guest"),
        }
        disp, footer_lbl, badge = author_labels.get(
            author_key, ("Francisco & Wandeson", "Francisco & Wandeson", "Goose Founders")
        )
        article.author_display = payload.get("author_display") or disp
        article.author_footer_label = footer_lbl
        article.author_role_badge = badge

    # Capa & SEO
    if "cover_image_url" in payload:
        article.cover_image_url = (payload.get("cover_image_url") or "").strip()
    if "cover_caption" in payload:
        article.cover_caption = (payload.get("cover_caption") or "").strip()
    if "meta_description" in payload:
        article.meta_description = (payload.get("meta_description") or "").strip()[:320]

    # Switches
    if "is_hero" in payload:
        is_hero_val = bool(payload.get("is_hero"))
        if is_hero_val:
            Article.query.filter(Article.id != article.id).update({"is_hero": False})
        article.is_hero = is_hero_val

    if "enable_zen_mode" in payload:
        article.enable_zen_mode = bool(payload.get("enable_zen_mode"))
    if "enable_goocast" in payload:
        article.enable_goocast = bool(payload.get("enable_goocast"))
    if "goocast_episode_label" in payload:
        article.goocast_episode_label = (payload.get("goocast_episode_label") or "GOOCAST #28").strip()
    if "goocast_title" in payload:
        article.goocast_title = (payload.get("goocast_title") or article.title).strip()
    if "goocast_duration" in payload:
        article.goocast_duration = (payload.get("goocast_duration") or "24:12").strip()

    # Data de publicação
    pub_date_str = payload.get("published_at")
    if pub_date_str:
        try:
            article.published_at = datetime.fromisoformat(pub_date_str)
        except ValueError:
            pass

    # Tempo de leitura
    article.reading_time_minutes = max(1, round(article.word_count / 180))

    # Tags
    tag_names = payload.get("tags")
    if isinstance(tag_names, list):
        resolved_tags = []
        for raw_t in tag_names:
            clean_t = raw_t.strip().lstrip("#")
            if not clean_t:
                continue
            t_slug = make_slug(clean_t)
            tag_obj = Tag.query.filter(
                (Tag.name == clean_t) | (Tag.slug == t_slug)
            ).first()
            if not tag_obj:
                tag_obj = Tag(name=clean_t, slug=t_slug)
                db.session.add(tag_obj)
            resolved_tags.append(tag_obj)
        article.tags = resolved_tags

    log_cms_action(
        action="SAVE_ARTICLE" if article.status == "draft" else "PUBLISH_ARTICLE",
        target_slug=article.slug,
        details=f"Artigo '{article.title[:60]}' salvo com status '{article.status}'.",
    )

    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "message": "Ensaio sincronizado com sucesso no banco de dados!",
            "article": article.to_dict(),
        }
    )


@cms_bp.route("/api/cms/articles/<int:article_id>/metadata", methods=["POST"])
@login_required
def api_update_article_metadata(article_id: int):
    article = db.session.get(Article, article_id)
    if not article:
        return jsonify({"ok": False, "error": "Artigo não encontrado."}), 404

    payload = request.get_json(silent=True) or {}

    if "title" in payload and payload["title"].strip():
        article.title = payload["title"].strip()
    if "meta_description" in payload:
        article.meta_description = payload["meta_description"].strip()[:320]
    if "slug" in payload and payload["slug"].strip():
        article.slug = make_slug(payload["slug"].strip())

    if "is_hero" in payload:
        is_hero_val = bool(payload["is_hero"])
        if is_hero_val:
            Article.query.filter(Article.id != article.id).update({"is_hero": False})
        article.is_hero = is_hero_val

    if "enable_zen_mode" in payload:
        article.enable_zen_mode = bool(payload["enable_zen_mode"])
    if "enable_goocast" in payload:
        article.enable_goocast = bool(payload["enable_goocast"])

    log_cms_action(
        action="UPDATE_SEO_METADATA",
        target_slug=article.slug,
        details=f"Metadados de SEO e switches atualizados (Hero={article.is_hero}, Zen={article.enable_zen_mode}).",
    )
    db.session.commit()

    return jsonify({"ok": True, "article": article.to_dict()})


@cms_bp.route("/api/cms/articles/<int:article_id>/status", methods=["POST"])
@login_required
def api_change_article_status(article_id: int):
    article = db.session.get(Article, article_id)
    if not article:
        return jsonify({"ok": False, "error": "Artigo não encontrado."}), 404

    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status", "published")
    if new_status not in ("published", "draft", "review", "archived"):
        return jsonify({"ok": False, "error": "Status inválido."}), 400

    article.status = new_status
    log_cms_action(
        action=f"STATUS_{new_status.upper()}",
        target_slug=article.slug,
        details=f"Status alterado para '{new_status}'.",
    )
    db.session.commit()

    return jsonify({"ok": True, "article": article.to_dict()})


@cms_bp.route("/api/cms/articles/<int:article_id>/duplicate", methods=["POST"])
@login_required
def api_duplicate_article(article_id: int):
    original = db.session.get(Article, article_id)
    if not original:
        return jsonify({"ok": False, "error": "Artigo não encontrado."}), 404

    new_slug = f"{original.slug}-copia-{int(datetime.now(timezone.utc).timestamp()) % 1000}"
    copy_art = Article(
        title=f"{original.title} (Cópia)",
        subtitle=original.subtitle,
        slug=new_slug,
        summary=original.summary,
        content_markdown=original.content_markdown,
        status="draft",
        category_id=original.category_id,
        author_id=original.author_id,
        author_key=original.author_key,
        author_display=original.author_display,
        author_footer_label=original.author_footer_label,
        author_role_badge=original.author_role_badge,
        cover_image_url=original.cover_image_url,
        cover_caption=original.cover_caption,
        meta_description=original.meta_description,
        reading_time_minutes=original.reading_time_minutes,
        views_count=0,
        is_hero=False,
        enable_zen_mode=original.enable_zen_mode,
        enable_goocast=original.enable_goocast,
        goocast_episode_label=original.goocast_episode_label,
        goocast_title=original.goocast_title,
        goocast_duration=original.goocast_duration,
        telemetry_box_json=original.telemetry_box_json,
        checklist_json=original.checklist_json,
        tags=list(original.tags),
    )
    db.session.add(copy_art)
    log_cms_action(
        action="DUPLICATE_ARTICLE",
        target_slug=new_slug,
        details=f"Duplicado a partir de '{original.slug}'.",
    )
    db.session.commit()

    return jsonify({"ok": True, "article": copy_art.to_dict()})


@cms_bp.route("/api/cms/articles/<int:article_id>", methods=["DELETE"])
@login_required
def api_delete_article(article_id: int):
    article = db.session.get(Article, article_id)
    if not article:
        return jsonify({"ok": False, "error": "Artigo não encontrado."}), 404

    slug = article.slug
    db.session.delete(article)
    log_cms_action(
        action="DELETE_ARTICLE",
        target_slug=slug,
        details=f"Artigo '{slug}' removido do repositório.",
    )
    db.session.commit()

    return jsonify({"ok": True, "deleted_id": article_id})


@cms_bp.route("/api/cms/upload", methods=["POST"])
@login_required
def api_upload_media():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nome de arquivo inválido."}), 400

    filename = secure_filename(file.filename)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    saved_name = f"{timestamp}_{filename}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    file.save(upload_path)

    file_url = f"/static/uploads/{saved_name}"
    asset = MediaAsset(
        filename=filename,
        file_url=file_url,
        alt_text=request.form.get("alt_text") or filename,
        mime_type=file.mimetype or "image/png",
    )
    db.session.add(asset)
    log_cms_action(
        action="UPLOAD_MEDIA",
        target_slug=filename,
        details=f"Upload de mídia salvo em {file_url}.",
    )
    db.session.commit()

    return jsonify({"ok": True, "asset": asset.to_dict()})


@cms_bp.route("/api/cms/export")
@login_required
def api_export_json():
    articles = Article.query.order_by(Article.published_at.desc()).all()
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "platform": "Goose Tecnologia CMS v2.4",
        "articles_count": len(articles),
        "articles": [a.to_dict() for a in articles],
    }
    log_cms_action(
        action="EXPORT_DUMP_JSON",
        target_slug="goose-blog-dump.json",
        details=f"Exportação completa de {len(articles)} artigos.",
    )
    db.session.commit()

    response = Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = "attachment; filename=goose-blog-dump.json"
    return response


@cms_bp.route("/api/cms/authors", methods=["GET"])
@login_required
def api_list_authors():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({"ok": True, "authors": [u.to_dict() for u in users]})


@cms_bp.route("/api/cms/authors", methods=["POST"])
@login_required
def api_save_author():
    payload = request.get_json(silent=True) or {}
    author_id = payload.get("id")
    display_name = (payload.get("display_name") or "").strip()
    role_title = (payload.get("role_title") or "Redator Técnico Telecom").strip()
    email = (payload.get("email") or "").strip().lower()
    raw_username = (payload.get("username") or "").strip()
    bio = (payload.get("bio") or "").strip()
    avatar_url = (payload.get("avatar_url") or "").strip()
    password = (payload.get("password") or "").strip()

    if not display_name:
        return jsonify({"ok": False, "error": "O nome do autor/redator é obrigatório."}), 400

    username = make_slug(raw_username if raw_username else display_name)
    if not email:
        email = f"{username}@goose.tec.br"

    DEFAULT_AVATAR = (
        "https://lh3.googleusercontent.com/aida-public/"
        "AB6AXuCv2wN6Zl7YGCG44IolCNUScJ9kzQwH4ou8YYmvT8DbT5KBbGi4LOXzsVjFMcQlDhliLO5SJiH9HqmzRmaYWeO1N6vZIdkqSfDkOCKJ5e20cYUraU22Ysk-jfB2adM45hzWGs6bKago7yoNPH5QLO2knCSq0J932Ak_DeOpKkt6eEzSX62lbP83ezejW3QorHKjLQJhiksTfZ6OgmY4h4aixpFvsx3RUyFSJFR4hkk"
    )

    if author_id:
        user = db.session.get(User, int(author_id))
        if not user:
            return jsonify({"ok": False, "error": "Autor não encontrado."}), 404
        old_username = user.username
        # Evita conflito de username/email com outro usuário
        conflict_user = User.query.filter(
            ((User.username == username) | (User.email == email)),
            User.id != user.id,
        ).first()
        if conflict_user:
            return (
                jsonify({"ok": False, "error": "Já existe outro autor com este usuário ou e-mail."}),
                400,
            )
        user.username = username
        user.email = email
        user.display_name = display_name
        user.role_title = role_title
        user.bio = bio
        if avatar_url:
            user.avatar_url = avatar_url
        if password:
            user.set_password(password)

        # Atualiza artigos vinculados a esse autor para refletir novo nome/cargo
        linked_articles = Article.query.filter(
            (Article.author_id == user.id) | (Article.author_key == old_username)
        ).all()
        for art in linked_articles:
            art.author_id = user.id
            art.author_key = user.username
            art.author_display = user.display_name
            art.author_footer_label = f"{user.display_name} • {user.role_title}"
            art.author_role_badge = user.role_title

        log_cms_action(
            action="UPDATE_AUTHOR",
            target_slug=user.username,
            details=f"Autor/Redator '{user.display_name}' ({user.role_title}) atualizado.",
        )
    else:
        conflict_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if conflict_user:
            username = f"{username}-{int(datetime.now(timezone.utc).timestamp()) % 1000}"
            if User.query.filter_by(email=email).first():
                email = f"{username}@goose.tec.br"

        user = User(
            username=username,
            email=email,
            display_name=display_name,
            role_title=role_title,
            bio=bio or "Especialista técnico e redator do portal Goose Tecnologia.",
            avatar_url=avatar_url or DEFAULT_AVATAR,
        )
        user.set_password(password if password else "goose2026")
        db.session.add(user)
        log_cms_action(
            action="CREATE_AUTHOR",
            target_slug=user.username,
            details=f"Novo Autor/Redator '{user.display_name}' ({user.role_title}) cadastrado.",
        )

    db.session.commit()
    return jsonify({"ok": True, "author": user.to_dict()})


@cms_bp.route("/api/cms/authors/<int:user_id>", methods=["DELETE"])
@login_required
def api_delete_author(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"ok": False, "error": "Autor não encontrado."}), 404

    if User.query.count() <= 1:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "Não é possível excluir o único autor ativo do sistema.",
                }
            ),
            400,
        )

    # Desvincula artigos que pertenciam a este autor para não quebrar FK
    linked_articles = Article.query.filter(
        (Article.author_id == user.id) | (Article.author_key == user.username)
    ).all()
    for art in linked_articles:
        art.author_id = None

    deleted_name = user.display_name
    deleted_slug = user.username
    db.session.delete(user)
    log_cms_action(
        action="DELETE_AUTHOR",
        target_slug=deleted_slug,
        details=f"Autor/Redator '{deleted_name}' removido.",
    )
    db.session.commit()
    return jsonify({"ok": True, "deleted_id": user_id})

