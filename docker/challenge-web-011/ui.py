import html
from pathlib import Path

from flask import Flask, Response

GLOBAL_CSS_PATH = Path(__file__).resolve().parent / "global.css"


def register_challenge_ui(app: Flask) -> None:
    @app.route("/global.css")
    def global_css() -> Response:
        return Response(
            GLOBAL_CSS_PATH.read_text(encoding="utf-8"),
            mimetype="text/css; charset=utf-8",
        )

    @app.after_request
    def apply_security_headers(response: Response) -> Response:
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


def render_page(
    title: str,
    heading: str,
    body_html: str,
    subtitle: str = "",
    badge: str = "SecureCorp Portal",
    footer_html: str = "",
    wide: bool = False,
) -> str:
    safe_title = html.escape(title)
    safe_heading = html.escape(heading)
    safe_badge = html.escape(badge)
    subtitle_block = f'<p class="ctf-lead">{html.escape(subtitle)}</p>' if subtitle else ""
    footer_content = footer_html if footer_html else "&copy; 2026 SecureCorp Defence Systems."
    card_class = "ctf-card ctf-card--wide" if wide else "ctf-card"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        "<head>\n"
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '    <meta name="robots" content="noindex, nofollow">\n'
        f"    <title>{safe_title} | SecureCorp</title>\n"
        '    <link rel="stylesheet" href="global.css">\n'
        "</head>\n"
        "<body>\n"
        '    <div class="ctf-shell">\n'
        f'        <main id="main-content" class="{card_class}">\n'
        '            <header class="ctf-header">\n'
        f'                <span class="ctf-badge">{safe_badge}</span>\n'
        f"                <h1>{safe_heading}</h1>\n"
        f"                {subtitle_block}\n"
        "            </header>\n"
        '            <section class="ctf-section">\n'
        f"                {body_html}\n"
        "            </section>\n"
        '            <footer class="ctf-footer">\n'
        f"                {footer_content}\n"
        "            </footer>\n"
        "        </main>\n"
        "    </div>\n"
        "</body>\n"
        "</html>\n"
    )
