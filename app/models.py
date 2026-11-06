import re
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager, UserMixin

article_tags = db.Table(
    "article_tags",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    role_title = db.Column(db.String(120), nullable=False, default="Telecom Engineer")
    avatar_url = db.Column(db.String(512), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    articles = db.relationship("Article", backref="author", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "role_title": self.role_title,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
        }


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    color_theme = db.Column(db.String(32), default="petroleum")  # carmine | petroleum | cyan

    articles = db.relationship("Article", backref="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "color_theme": self.color_theme,
        }


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
        }


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(500), nullable=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    summary = db.Column(db.Text, nullable=True)
    content_markdown = db.Column(db.Text(length=4294967295), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft", index=True)  # published, draft, review, archived

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    author_key = db.Column(db.String(64), default="duo")  # francisco, wandeson, duo, guest
    author_display = db.Column(db.String(120), default="Francisco & Wandeson")
    author_footer_label = db.Column(db.String(120), default="Francisco & Wandeson")
    author_role_badge = db.Column(db.String(80), default="Goose Founders")

    cover_image_url = db.Column(db.String(600), nullable=True)
    cover_caption = db.Column(db.String(255), nullable=True)
    code_card_preview = db.Column(db.Text, nullable=True)  # Opcional: para cards na home que exibem snippet RouterOS
    meta_description = db.Column(db.String(320), nullable=True)

    reading_time_minutes = db.Column(db.Integer, default=7)
    views_count = db.Column(db.Integer, default=0)

    is_hero = db.Column(db.Boolean, default=False)
    is_featured_double = db.Column(db.Boolean, default=False)
    enable_zen_mode = db.Column(db.Boolean, default=True)
    enable_goocast = db.Column(db.Boolean, default=False)

    goocast_episode_label = db.Column(db.String(64), nullable=True, default="GOOCAST #28")
    goocast_title = db.Column(db.String(255), nullable=True)
    goocast_duration = db.Column(db.String(32), nullable=True, default="24:12")
    goocast_audio_url = db.Column(db.String(512), nullable=True)

    telemetry_box_json = db.Column(db.JSON, nullable=True)
    checklist_json = db.Column(db.JSON, nullable=True)

    published_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tags = db.relationship("Tag", secondary=article_tags, lazy="subquery", backref=db.backref("articles", lazy=True))

    @property
    def word_count(self) -> int:
        text = re.sub(r"[#*`~>\[\]\(\)_-]", " ", self.content_markdown or "")
        words = [w for w in text.split() if w.strip()]
        return max(len(words), 1)

    @property
    def script_blocks_count(self) -> int:
        return len(re.findall(r"```", self.content_markdown or "")) // 2

    @property
    def formatted_views(self) -> str:
        if self.views_count >= 1000:
            return f"{self.views_count / 1000:.1f}k"
        return str(self.views_count)

    def recalculate_reading_time(self) -> int:
        words = self.word_count
        calculated = max(3, round(words / 180))
        if not self.reading_time_minutes:
            self.reading_time_minutes = calculated
        return self.reading_time_minutes

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle or "",
            "slug": self.slug,
            "summary": self.summary or "",
            "content_markdown": self.content_markdown,
            "status": self.status,
            "category": self.category.to_dict() if self.category else None,
            "category_id": self.category_id,
            "author_key": self.author_key,
            "author_display": self.author_display,
            "author_footer_label": self.author_footer_label,
            "author_role_badge": self.author_role_badge,
            "cover_image_url": self.cover_image_url or "",
            "cover_caption": self.cover_caption or "",
            "meta_description": self.meta_description or self.summary or "",
            "reading_time_minutes": self.reading_time_minutes,
            "views_count": self.views_count,
            "formatted_views": self.formatted_views,
            "word_count": self.word_count,
            "script_blocks_count": self.script_blocks_count,
            "is_hero": self.is_hero,
            "is_featured_double": self.is_featured_double,
            "enable_zen_mode": self.enable_zen_mode,
            "enable_goocast": self.enable_goocast,
            "goocast_episode_label": self.goocast_episode_label or "GOOCAST #28",
            "goocast_title": self.goocast_title or self.title,
            "goocast_duration": self.goocast_duration or "24:12",
            "tags": [t.name for t in self.tags],
            "published_at": self.published_at.strftime("%Y-%m-%d") if self.published_at else "",
            "published_at_iso": self.published_at.strftime("%Y-%m-%dT%H:%M") if self.published_at else "",
        }


class Lead(db.Model):
    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    isp_asn = db.Column(db.String(150), nullable=False)
    whatsapp = db.Column(db.String(64), nullable=False)
    source_page = db.Column(db.String(255), default="/")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "isp_asn": self.isp_asn,
            "whatsapp": self.whatsapp,
            "source_page": self.source_page,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
        }


class MediaAsset(db.Model):
    __tablename__ = "media_assets"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(512), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(64), default="image/png")
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_url": self.file_url,
            "alt_text": self.alt_text or self.filename,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at.strftime("%d/%m/%Y %H:%M") if self.uploaded_at else "",
        }


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    author_name = db.Column(db.String(120), nullable=False)
    author_role_isp = db.Column(db.String(120), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_author_badge = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    article = db.relationship(
        "Article",
        backref=db.backref("comments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="select",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.asc()",
    )

    @property
    def initials(self) -> str:
        parts = [p[0].upper() for p in (self.author_name or "L").split() if p]
        return "".join(parts[:2]) or "IS"

    def to_dict(self, include_replies: bool = True) -> dict:
        data = {
            "id": self.id,
            "article_id": self.article_id,
            "parent_id": self.parent_id,
            "author_name": self.author_name,
            "author_role_isp": self.author_role_isp or "",
            "content": self.content,
            "is_author_badge": bool(self.is_author_badge),
            "initials": self.initials,
            "created_at": self.created_at.strftime("%d/%m/%Y às %H:%M") if self.created_at else "",
        }
        if include_replies:
            data["replies"] = [r.to_dict(include_replies=False) for r in self.replies]
        return data


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(120), nullable=False)
    actor_name = db.Column(db.String(120), default="Francisco & Wandeson")
    target_slug = db.Column(db.String(255), nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "actor_name": self.actor_name,
            "target_slug": self.target_slug or "-",
            "details": self.details or "",
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M:%S") if self.created_at else "",
        }
