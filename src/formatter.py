from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_article_html(article: dict) -> str:
    template_dir = Path("templates")

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("article.html")

    css_path = template_dir / "journal.css"
    css = css_path.read_text(encoding="utf-8")

    return template.render(
        article=article,
        css=css,
    )
