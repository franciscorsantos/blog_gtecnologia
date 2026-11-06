from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from app.extensions import db
from app.models import Article, Category, Tag, Lead, Comment, AuditLog
from app.utils.markdown_renderer import render_article_markdown

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    published_articles = (
        Article.query.filter_by(status="published")
        .order_by(Article.published_at.desc())
        .all()
    )

    hero_article = (
        Article.query.filter_by(status="published", is_hero=True)
        .order_by(Article.published_at.desc())
        .first()
    )
    if not hero_article and published_articles:
        hero_article = published_articles[0]

    # Artigos exibidos na grade principal (todos os publicados; ou excluindo o hero se desejar,
    # mas na tela Stitch o Hero é o Destaque e a grade traz os 5 ensaios técnicos/GOOCAST)
    grid_articles = [a for a in published_articles if not hero_article or a.id != hero_article.id]
    if not grid_articles and published_articles:
        grid_articles = published_articles

    categories = Category.query.order_by(Category.id.asc()).all()
    tags = Tag.query.limit(8).all()

    avg_reading_time = 7
    if published_articles:
        avg_reading_time = round(
            sum(a.reading_time_minutes or 7 for a in published_articles) / len(published_articles)
        )

    hero_rendered_html = ""
    if hero_article:
        hero_rendered_html, _ = render_article_markdown(hero_article.content_markdown)

    return render_template(
        "public/index.html",
        hero_article=hero_article,
        hero_rendered_html=hero_rendered_html,
        articles=grid_articles,
        all_published=published_articles,
        categories=categories,
        tags=tags,
        avg_reading_time=avg_reading_time,
    )


@public_bp.route("/blog/<slug>")
def article_detail(slug: str):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        abort(404)

    # Incrementa contador de leituras de forma atômica no banco
    Article.query.filter_by(id=article.id).update(
        {"views_count": func.coalesce(Article.views_count, 0) + 1},
        synchronize_session=False,
    )
    db.session.commit()
    article.views_count = (article.views_count or 0) + 1

    rendered_html, toc_items = render_article_markdown(article.content_markdown)

    # Próximos ensaios recomendados
    related_articles = (
        Article.query.filter(Article.status == "published", Article.id != article.id)
        .order_by(Article.views_count.desc())
        .limit(2)
        .all()
    )

    checklist_items = article.checklist_json or []
    telemetry_box = article.telemetry_box_json or None

    try:
        root_comments = (
            Comment.query.filter_by(article_id=article.id, parent_id=None)
            .order_by(Comment.created_at.desc())
            .all()
        )
        total_comments_count = Comment.query.filter_by(article_id=article.id).count()
    except OperationalError:
        db.create_all()
        root_comments = []
        total_comments_count = 0

    return render_template(
        "public/article.html",
        article=article,
        rendered_html=rendered_html,
        toc_items=toc_items,
        related_articles=related_articles,
        checklist_items=checklist_items,
        telemetry_box=telemetry_box,
        comments=root_comments,
        total_comments_count=total_comments_count,
    )


@public_bp.route("/api/articles/<slug>/comments", methods=["GET", "POST"])
def api_article_comments(slug: str):
    article = Article.query.filter_by(slug=slug).first_or_404()

    try:
        Comment.query.limit(1).all()
    except OperationalError:
        db.create_all()

    if request.method == "GET":
        root_comments = (
            Comment.query.filter_by(article_id=article.id, parent_id=None)
            .order_by(Comment.created_at.desc())
            .all()
        )
        total_count = Comment.query.filter_by(article_id=article.id).count()
        return jsonify(
            {
                "ok": True,
                "total": total_count,
                "comments": [c.to_dict() for c in root_comments],
            }
        )

    payload = request.get_json(silent=True) or request.form
    author_name = (payload.get("author_name") or "").strip()
    author_role_isp = (payload.get("author_role_isp") or "").strip()
    content = (payload.get("content") or "").strip()
    parent_id_raw = payload.get("parent_id")

    if not author_name or not content:
        return (
            jsonify({"ok": False, "error": "Por favor, informe seu nome e o seu comentário."}),
            400,
        )

    if len(content) > 3000:
        return (
            jsonify({"ok": False, "error": "O comentário deve ter no máximo 3.000 caracteres."}),
            400,
        )

    parent_id = None
    if parent_id_raw:
        try:
            pid = int(parent_id_raw)
            parent_comment = db.session.get(Comment, pid)
            if parent_comment and parent_comment.article_id == article.id:
                # Mantém aninhamento de 1 nível (respostas sob o comentário raiz)
                parent_id = parent_comment.parent_id or parent_comment.id
        except (ValueError, TypeError):
            parent_id = None

    is_author = bool(current_user and getattr(current_user, "is_authenticated", False))

    comment = Comment(
        article_id=article.id,
        parent_id=parent_id,
        author_name=author_name[:120],
        author_role_isp=author_role_isp[:120] if author_role_isp else None,
        content=content,
        is_author_badge=is_author,
    )
    db.session.add(comment)
    db.session.add(
        AuditLog(
            action="COMMENT_CREATED",
            actor_name=author_name[:120],
            target_slug=article.slug,
            details=f"Comentário publicado no artigo '{article.title[:60]}'",
        )
    )
    db.session.commit()

    total_count = Comment.query.filter_by(article_id=article.id).count()
    return jsonify(
        {
            "ok": True,
            "message": "Comentário publicado com sucesso!",
            "comment": comment.to_dict(),
            "total": total_count,
            "can_moderate": is_author,
        }
    )


@public_bp.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def api_delete_comment(comment_id: int):
    if not (current_user and getattr(current_user, "is_authenticated", False)):
        return jsonify({"ok": False, "error": "Apenas editores autenticados podem excluir comentários."}), 403

    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({"ok": False, "error": "Comentário não encontrado."}), 404

    article_id = comment.article_id
    db.session.delete(comment)
    db.session.commit()

    total_count = Comment.query.filter_by(article_id=article_id).count()
    return jsonify(
        {
            "ok": True,
            "message": "Comentário removido.",
            "deleted_id": comment_id,
            "total": total_count,
        }
    )


@public_bp.route("/api/articles/<slug>")
def api_article_detail(slug: str):
    article = Article.query.filter_by(slug=slug).first_or_404()
    rendered_html, toc_items = render_article_markdown(article.content_markdown)
    data = article.to_dict()
    data["rendered_html"] = rendered_html
    data["toc_items"] = toc_items
    return jsonify(data)


@public_bp.route("/api/leads", methods=["POST"])
def api_create_lead():
    payload = request.get_json(silent=True) or request.form
    name = (payload.get("name") or "").strip()
    isp_asn = (payload.get("isp_asn") or "").strip()
    whatsapp = (payload.get("whatsapp") or "").strip()
    source_page = (payload.get("source_page") or "/").strip()

    if not name or not isp_asn or not whatsapp:
        return (
            jsonify({"ok": False, "error": "Preencha nome, provedor/ASN e WhatsApp."}),
            400,
        )

    lead = Lead(
        name=name,
        isp_asn=isp_asn,
        whatsapp=whatsapp,
        source_page=source_page,
    )
    db.session.add(lead)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "message": "Mensagem recebida! Francisco e Wandeson entrarão em contato.",
            "lead": lead.to_dict(),
        }
    )

