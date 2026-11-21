import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parent.parent
if str(DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(DOCKER_DIR))

from build_monolithic import build_monolithic_bundle
from create_challenges import generate_challenges

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def assert_html_standards(html_text: str, forbidden_substring: str = "") -> None:
    assert "<!DOCTYPE html>" in html_text
    assert '<html lang="es">' in html_text
    assert '<meta name="robots" content="noindex, nofollow">' in html_text
    assert '<link rel="stylesheet" href="global.css">' in html_text
    assert "<main" in html_text
    assert "<header" in html_text
    assert "<section" in html_text
    assert "<footer" in html_text
    assert html_text.count("<h1") == 1
    assert "style=" not in html_text.lower()
    assert not _EMOJI_RE.search(html_text)
    if forbidden_substring:
        assert forbidden_substring not in html_text
        assert "EclipSec{" not in html_text


def assert_security_headers(resp) -> None:
    assert resp.headers.get("X-Robots-Tag") == "noindex, nofollow"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "no-referrer"


def assert_css_endpoint(client) -> None:
    css_resp = client.get("/global.css")
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.mimetype
    css_text = css_resp.get_data(as_text=True)
    assert "--color-bg-primary: #0b0f17" in css_text
    assert "--color-surface-card: #161e2e" in css_text
    assert "--color-accent-primary: #e11d48" in css_text
    assert "prefers-reduced-motion" in css_text


def load_isolated_challenge(
    challenge_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    flag_value: str,
):
    workdir = tmp_path / f"web-{challenge_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    src_dir = DOCKER_DIR / f"challenge-web-{challenge_id}"
    for fname in ("app.py", "ui.py", "global.css"):
        shutil.copyfile(src_dir / fname, workdir / fname)

    if challenge_id in {"002", "003", "006", "007", "008", "009", "010"}:
        (workdir / ".flag").write_text(f"{flag_value}\n", encoding="utf-8", newline="\n")
    elif challenge_id in {"004", "011"}:
        (workdir / "flag.txt").write_text(f"{flag_value}\n", encoding="utf-8", newline="\n")
    elif challenge_id == "005":
        (workdir / "home.txt").write_text("Welcome to the home page.\n", encoding="utf-8", newline="\n")

    if challenge_id == "006":
        monkeypatch.setenv("CTF_DB_PATH", str(workdir / "users.db"))

    monkeypatch.chdir(workdir)
    monkeypatch.syspath_prepend(str(workdir))
    sys.modules.pop("ui", None)

    ui_spec = importlib.util.spec_from_file_location("ui", workdir / "ui.py")
    assert ui_spec is not None and ui_spec.loader is not None
    ui_mod = importlib.util.module_from_spec(ui_spec)
    sys.modules["ui"] = ui_mod
    ui_spec.loader.exec_module(ui_mod)

    mod_name = f"ctf_e2e_web_{challenge_id}"
    sys.modules.pop(mod_name, None)
    app_spec = importlib.util.spec_from_file_location(mod_name, workdir / "app.py")
    assert app_spec is not None and app_spec.loader is not None
    app_mod = importlib.util.module_from_spec(app_spec)
    sys.modules[mod_name] = app_mod
    app_spec.loader.exec_module(app_mod)
    return app_mod.app, workdir


def test_generators_parity_with_checked_in_tree(tmp_path: Path):
    gen_dir = tmp_path / "docker_gen"
    shutil.copytree(DOCKER_DIR / "shared", gen_dir / "shared")
    generate_challenges(gen_dir)
    build_monolithic_bundle(gen_dir, gen_dir / "monolithic")

    assert (gen_dir / "docker-compose.yml").read_text(encoding="utf-8") == (
        DOCKER_DIR / "docker-compose.yml"
    ).read_text(encoding="utf-8")

    for i in range(1, 12):
        cid = f"{i:03d}"
        gen_ch = gen_dir / f"challenge-web-{cid}"
        real_ch = DOCKER_DIR / f"challenge-web-{cid}"
        gen_files = sorted(p.name for p in gen_ch.iterdir() if p.is_file())
        real_files = sorted(p.name for p in real_ch.iterdir() if p.is_file())
        assert gen_files == real_files
        for fname in gen_files:
            assert (gen_ch / fname).read_text(encoding="utf-8") == (real_ch / fname).read_text(
                encoding="utf-8"
            )

    gen_mono = gen_dir / "monolithic"
    real_mono = DOCKER_DIR / "monolithic"
    gen_mono_files = sorted(
        p.relative_to(gen_mono).as_posix()
        for p in gen_mono.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    real_mono_files = sorted(
        p.relative_to(real_mono).as_posix()
        for p in real_mono.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    assert gen_mono_files == real_mono_files
    for rel in gen_mono_files:
        assert (gen_mono / rel).read_text(encoding="utf-8") == (real_mono / rel).read_text(
            encoding="utf-8"
        )


def test_dockerfiles_and_compose_hardening():
    for i in range(1, 12):
        cid = f"{i:03d}"
        df_bytes = (DOCKER_DIR / f"challenge-web-{cid}" / "Dockerfile").read_bytes()
        assert b"\r\n" not in df_bytes
        df_text = df_bytes.decode("utf-8")
        assert "ARG CHALLENGE_FLAG=" in df_text
        assert "\nUSER " in df_text
        assert "ttyd" not in df_text
        assert "ENV FLAG=" not in df_text

    mono_df_bytes = (DOCKER_DIR / "monolithic" / "Dockerfile").read_bytes()
    assert b"\r\n" not in mono_df_bytes
    mono_df = mono_df_bytes.decode("utf-8")
    assert "ttyd" not in mono_df
    assert "ENV FLAG=" not in mono_df
    assert "python:3.12-slim" in mono_df

    compose_text = (DOCKER_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    service_blocks = compose_text.split("  web-")[1:]
    assert len(service_blocks) == 11
    for block in service_blocks:
        for required_key in (
            "read_only: true",
            "tmpfs:",
            "no-new-privileges:true",
            "cap_drop:",
            "- ALL",
            "mem_limit:",
            "memswap_limit:",
            "cpus:",
            "pids_limit:",
            "- ctf-net",
        ):
            assert required_key in block


def test_web_001_and_monolithic_index_standards():
    html_001 = (DOCKER_DIR / "challenge-web-001" / "index.html").read_text(encoding="utf-8")
    assert_html_standards(html_001)
    assert "__CHALLENGE_FLAG__" in html_001

    nginx_001 = (DOCKER_DIR / "challenge-web-001" / "nginx.conf").read_text(encoding="utf-8")
    assert "listen 8080" in nginx_001
    assert "pid /tmp/nginx.pid;" in nginx_001
    assert 'add_header X-Robots-Tag "noindex, nofollow"' in nginx_001

    rendered_001 = html_001.replace("__CHALLENGE_FLAG__", "EclipSec{e2e_flag_001}")
    visible_only = re.sub(r"<!--.*?-->", "", rendered_001, flags=re.S)
    assert "EclipSec{e2e_flag_001}" not in visible_only
    assert "EclipSec{e2e_flag_001}" in rendered_001

    index_html = (DOCKER_DIR / "monolithic" / "web-index" / "index.html").read_text(encoding="utf-8")
    assert_html_standards(index_html, forbidden_substring="EclipSec{")
    for i in range(1, 12):
        assert f'href="/web-{i:03d}/"' in index_html


def test_web_002_robots_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_002}"
    app, _ = load_isolated_challenge("002", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    home = client.get("/")
    assert home.status_code == 200
    assert_security_headers(home)
    assert_html_standards(home.get_data(as_text=True), forbidden_substring=flag)

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "/secret_flag_dir_991" in robots.get_data(as_text=True)

    secret = client.get("/secret_flag_dir_991")
    assert secret.status_code == 200
    assert secret.get_data(as_text=True).strip() == flag


def test_web_003_cookie_tampering_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_003}"
    app, _ = load_isolated_challenge("003", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    guest_resp = client.get("/")
    assert guest_resp.status_code == 200
    assert_security_headers(guest_resp)
    assert_html_standards(guest_resp.get_data(as_text=True), forbidden_substring=flag)

    client.set_cookie("role", "admin")
    admin_resp = client.get("/")
    assert admin_resp.status_code == 200
    body = admin_resp.get_data(as_text=True)
    assert_html_standards(body)
    assert flag in body


def test_web_004_cmdi_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_004}"
    app, _ = load_isolated_challenge("004", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    get_resp = client.get("/")
    assert get_resp.status_code == 200
    assert_security_headers(get_resp)
    assert_html_standards(get_resp.get_data(as_text=True), forbidden_substring=flag)

    sep = "&" if os.name == "nt" else ";"
    payload = f'127.0.0.1 {sep} "{sys.executable}" -c "print(open(\'flag.txt\').read().strip())"'
    post_resp = client.post("/", data={"ip": payload})
    assert post_resp.status_code == 200
    body = post_resp.get_data(as_text=True)
    assert_html_standards(body)
    assert flag in body


def test_web_005_lfi_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_005}"
    app, _ = load_isolated_challenge("005", tmp_path, monkeypatch, flag)
    outside_flag = tmp_path / "flag_outside.txt"
    outside_flag.write_text(f"{flag}\n", encoding="utf-8", newline="\n")

    client = app.test_client()
    assert_css_endpoint(client)

    default_resp = client.get("/")
    assert default_resp.status_code == 200
    assert_security_headers(default_resp)
    default_body = default_resp.get_data(as_text=True)
    assert_html_standards(default_body, forbidden_substring=flag)
    assert "Welcome to the home page." in default_body

    # Confirm no flag.txt exists in challenge working directory (anti-bypass)
    assert not (tmp_path / "web-005" / "flag.txt").exists()

    lfi_resp = client.get("/?file=../flag_outside.txt")
    assert lfi_resp.status_code == 200
    lfi_body = lfi_resp.get_data(as_text=True)
    assert_html_standards(lfi_body)
    assert flag in lfi_body


def test_web_006_sqli_login_bypass_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_006}"
    app, _ = load_isolated_challenge("006", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    get_resp = client.get("/")
    assert get_resp.status_code == 200
    assert_security_headers(get_resp)
    assert_html_standards(get_resp.get_data(as_text=True), forbidden_substring=flag)

    bad_resp = client.post("/", data={"user": "admin", "pass": "wrong"})
    assert bad_resp.status_code == 200
    assert_html_standards(bad_resp.get_data(as_text=True), forbidden_substring=flag)

    sqli_resp = client.post("/", data={"user": "' OR 1=1 --", "pass": "anything"})
    assert sqli_resp.status_code == 200
    sqli_body = sqli_resp.get_data(as_text=True)
    assert_html_standards(sqli_body)
    assert flag in sqli_body


def test_web_007_idor_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_007}"
    app, _ = load_isolated_challenge("007", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    normal_resp = client.get("/?id=1")
    assert normal_resp.status_code == 200
    assert_security_headers(normal_resp)
    assert_html_standards(normal_resp.get_data(as_text=True), forbidden_substring=flag)

    idor_resp = client.get("/?id=0")
    assert idor_resp.status_code == 200
    idor_body = idor_resp.get_data(as_text=True)
    assert_html_standards(idor_body)
    assert flag in idor_body


def test_web_008_ssti_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_008}"
    had_flag = "FLAG" in os.environ
    previous_flag = os.environ.pop("FLAG", None)
    try:
        app, _ = load_isolated_challenge("008", tmp_path, monkeypatch, flag)
        client = app.test_client()

        assert_css_endpoint(client)
        normal_resp = client.get("/?name=Alice")
        assert normal_resp.status_code == 200
        assert_security_headers(normal_resp)
        normal_body = normal_resp.get_data(as_text=True)
        assert_html_standards(normal_body, forbidden_substring=flag)
        assert "Alice" in normal_body

        math_resp = client.get("/?name={{7*7}}")
        assert math_resp.status_code == 200
        assert "49" in math_resp.get_data(as_text=True)

        exploit_resp = client.get("/?name={{cycler.__init__.__globals__.os.environ['FLAG']}}")
        assert exploit_resp.status_code == 200
        exploit_body = exploit_resp.get_data(as_text=True)
        assert_html_standards(exploit_body)
        assert flag in exploit_body
    finally:
        os.environ.pop("FLAG", None)
        if had_flag and previous_flag is not None:
            os.environ["FLAG"] = previous_flag


def test_web_009_backup_leak_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_009}"
    app, _ = load_isolated_challenge("009", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    home = client.get("/")
    assert home.status_code == 200
    assert_security_headers(home)
    assert_html_standards(home.get_data(as_text=True), forbidden_substring=flag)

    bak = client.get("/index.bak")
    assert bak.status_code == 200
    assert flag in bak.get_data(as_text=True)


def test_web_010_headers_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_010}"
    app, _ = load_isolated_challenge("010", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    denied = client.get("/")
    assert denied.status_code == 200
    assert_security_headers(denied)
    assert_html_standards(denied.get_data(as_text=True), forbidden_substring=flag)

    denied_ip = client.get(
        "/",
        headers={"User-Agent": "SecureBrowser1.0", "X-Forwarded-For": "10.0.0.5"},
    )
    assert denied_ip.status_code == 200
    assert_html_standards(denied_ip.get_data(as_text=True), forbidden_substring=flag)

    granted = client.get(
        "/",
        headers={
            "User-Agent": "SecureBrowser1.0",
            "X-Forwarded-For": "127.0.0.1, 198.51.100.5",
        },
    )
    assert granted.status_code == 200
    granted_body = granted.get_data(as_text=True)
    assert_html_standards(granted_body)
    assert flag in granted_body


def test_web_011_rce_get_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    flag = "EclipSec{e2e_flag_011}"
    app, _ = load_isolated_challenge("011", tmp_path, monkeypatch, flag)
    client = app.test_client()

    assert_css_endpoint(client)
    idle = client.get("/")
    assert idle.status_code == 200
    assert_security_headers(idle)
    assert_html_standards(idle.get_data(as_text=True), forbidden_substring=flag)

    cmd = f'"{sys.executable}" -c "print(open(\'flag.txt\').read().strip())"'
    rce_resp = client.get("/", query_string={"cmd": cmd})
    assert rce_resp.status_code == 200
    rce_body = rce_resp.get_data(as_text=True)
    assert_html_standards(rce_body)
    assert flag in rce_body
