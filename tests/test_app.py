import unittest
import json
from config import TestConfig
from app import create_app
from app.extensions import db
from app.models import User, Article, Category, Tag, Lead


class GooseBlogTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def login_francisco(self):
        return self.client.post(
            "/cms/login",
            data={"identifier": "francisco@goose.tec.br", "password": "goose2026"},
            follow_redirects=True,
        )

    def test_01_seed_and_models(self):
        """Verifica se o seed populou usuários, categorias, tags e artigos do design Stitch."""
        self.assertGreaterEqual(User.query.count(), 2)
        self.assertGreaterEqual(Category.query.count(), 4)
        self.assertGreaterEqual(Tag.query.count(), 10)
        self.assertEqual(Article.query.count(), 7)

        hero = Article.query.filter_by(is_hero=True).first()
        self.assertIsNotNone(hero)
        self.assertIn("Fim do Robô Burro", hero.title)

    def test_02_public_home_and_article_view(self):
        """Valida a renderização da Home Minimalista (/) e da página de Artigo (/blog/<slug>)."""
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        html_home = res_home.data.decode("utf-8")
        self.assertIn("O Fim do Robô Burro no Provedor", html_home)
        self.assertIn("Artigos &amp; Pesquisas Aplicadas", html_home)

        res_art = self.client.get("/blog/arquitetura-bgp-multihomed-transito-ip")
        self.assertEqual(res_art.status_code, 200)
        html_art = res_art.data.decode("utf-8")
        self.assertIn("Arquitetura BGP Multihomed com Comunidades", html_art)
        self.assertIn("Protocolo de Segurança NOC Goose", html_art)
        self.assertIn("DIAGRAMA TOPOLÓGICO: POP BORDER MULTIHOMED", html_art)
        self.assertIn("Checklist Operacional de Validação", html_art)

    def test_03_api_article_and_lead_submission(self):
        """Valida o endpoint JSON do modal de artigo e o salvamento de leads no banco."""
        res_api = self.client.get("/api/articles/arquitetura-bgp-multihomed-transito-ip")
        self.assertEqual(res_api.status_code, 200)
        data = json.loads(res_api.data)
        self.assertEqual(data["slug"], "arquitetura-bgp-multihomed-transito-ip")
        self.assertIn("rendered_html", data)

        res_lead = self.client.post(
            "/api/leads",
            json={
                "name": "Carlos Eduardo",
                "isp_asn": "UltraFibra ISP (AS269999)",
                "whatsapp": "(11) 97777-8888",
                "source_page": "/",
            },
        )
        self.assertEqual(res_lead.status_code, 200)
        lead_data = json.loads(res_lead.data)
        self.assertTrue(lead_data["ok"])
        self.assertIsNotNone(Lead.query.filter_by(name="Carlos Eduardo").first())

    def test_04_cms_authentication_and_protection(self):
        """Verifica se /cms exige login e se Francisco autentica com sucesso."""
        res_unauth = self.client.get("/cms")
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn("/cms/login", res_unauth.headers["Location"])

        res_login = self.login_francisco()
        self.assertEqual(res_login.status_code, 200)
        html_cms = res_login.data.decode("utf-8")
        self.assertIn("Gestão Editorial de Ensaios &amp; Artigos", html_cms)
        self.assertIn("Inspetor de Metadados", html_cms)

    def test_05_cms_editor_and_crud_operations(self):
        """Testa criação, edição de metadados, duplicação, alteração de status e exportação JSON."""
        self.login_francisco()

        # Renderiza o Editor Markdown
        res_ed = self.client.get("/cms/editor")
        self.assertEqual(res_ed.status_code, 200)
        self.assertIn("raw_post_buffer.md", res_ed.data.decode("utf-8"))

        # Cria um novo ensaio via API do Editor
        res_create = self.client.post(
            "/api/cms/articles",
            json={
                "title": "Engenharia MPLS e Segment Routing em Backbones Ópticos",
                "slug": "engenharia-mpls-segment-routing",
                "content_markdown": "## 1. Introdução ao SR-MPLS\n\nConfiguração de loopback e OSPF.\n\n```mikrotik\n/routing ospf instance add name=v2\n```",
                "status": "published",
                "author_key": "francisco",
                "meta_description": "Guia de MPLS e Segment Routing para ISPs.",
                "is_hero": False,
                "enable_zen_mode": True,
                "enable_goocast": True,
                "tags": ["MPLS", "BGP", "MikroTik"],
            },
        )
        self.assertEqual(res_create.status_code, 200)
        created = json.loads(res_create.data)["article"]
        art_id = created["id"]

        # Atualiza metadados via Inspetor
        res_meta = self.client.post(
            f"/api/cms/articles/{art_id}/metadata",
            json={"is_hero": True, "enable_zen_mode": True, "enable_goocast": False},
        )
        self.assertEqual(res_meta.status_code, 200)
        self.assertTrue(json.loads(res_meta.data)["article"]["is_hero"])

        # Duplica o artigo
        res_dup = self.client.post(f"/api/cms/articles/{art_id}/duplicate")
        self.assertEqual(res_dup.status_code, 200)
        dup_id = json.loads(res_dup.data)["article"]["id"]

        # Deleta a cópia
        res_del = self.client.delete(f"/api/cms/articles/{dup_id}")
        self.assertEqual(res_del.status_code, 200)

        # Exporta dump JSON
        res_exp = self.client.get("/api/cms/export")
        self.assertEqual(res_exp.status_code, 200)
        dump = json.loads(res_exp.data)
        self.assertGreaterEqual(dump["articles_count"], 8)


if __name__ == "__main__":
    unittest.main()
