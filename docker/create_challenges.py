from pathlib import Path
from typing import NotRequired, TypedDict

BASE_DIR = Path(__file__).resolve().parent


class ChallengeSpec(TypedDict):
    id: str
    port_web: int
    default_flag: str
    extra_apt: NotRequired[str]
    extra_env: NotRequired[str]
    build_steps: str


DOCKERFILE_001 = """FROM nginx:1.27-alpine

ARG CHALLENGE_FLAG='EclipSec{h1dd3n_1n_pl41n_s1ght}'

ENV PORT=8080

COPY docker/challenge-web-001/nginx.conf /etc/nginx/nginx.conf
COPY docker/challenge-web-001/index.html /usr/share/nginx/html/index.html
COPY docker/shared/global.css /usr/share/nginx/html/global.css

RUN awk 'BEGIN { flag = ENVIRON["CHALLENGE_FLAG"] } { idx = index($0, "__CHALLENGE_FLAG__"); if (idx > 0) { $0 = substr($0, 1, idx - 1) flag substr($0, idx + 18) } print }' /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp && \\
    mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html && \\
    chown -R root:nginx /usr/share/nginx/html && \\
    chmod 550 /usr/share/nginx/html && \\
    chmod 440 /usr/share/nginx/html/index.html /usr/share/nginx/html/global.css

USER nginx

EXPOSE 8080

ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
"""

DOCKERFILE_FLASK_TEMPLATE = """FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    HOST=0.0.0.0 \\
    PORT=8000

__EXTRA_APT____EXTRA_ENV__RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='__DEFAULT_FLAG__'

WORKDIR /app
COPY docker/challenge-web-__CHALLENGE_ID__/app.py docker/shared/ui.py docker/shared/global.css /app/

__BUILD_STEPS__

USER ctf

EXPOSE 8000

CMD ["python3", "app.py"]
"""

_STANDARD_DOT_FLAG_STEPS = (
    "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
    "    chown -R root:ctf /app && \\\n"
    "    chmod 550 /app && \\\n"
    "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
)

_STANDARD_TXT_FLAG_STEPS = (
    "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/flag.txt && \\\n"
    "    chown -R root:ctf /app && \\\n"
    "    chmod 550 /app && \\\n"
    "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/flag.txt"
)

CHALLENGE_SPECS: list[ChallengeSpec] = [
    {
        "id": "002",
        "port_web": 8002,
        "default_flag": "EclipSec{r0b0ts_4r3_y0ur_fr13nd5}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "003",
        "port_web": 8003,
        "default_flag": "EclipSec{c00k13_m0nst3r_m4n1pul4t10n}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "004",
        "port_web": 8004,
        "default_flag": "EclipSec{p1ng_0f_d34th_cmdi}",
        "extra_apt": (
            "RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
            "    iputils-ping \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n\n"
        ),
        "build_steps": _STANDARD_TXT_FLAG_STEPS,
    },
    {
        "id": "005",
        "port_web": 8005,
        "default_flag": "EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}",
        "build_steps": (
            "RUN printf '%s\\n' 'Welcome to the home page.' > /app/home.txt && \\\n"
            "    printf '%s\\n' \"$CHALLENGE_FLAG\" > /flag.txt && \\\n"
            "    chown -R root:ctf /app /flag.txt && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/home.txt /flag.txt"
        ),
    },
    {
        "id": "006",
        "port_web": 8006,
        "default_flag": "EclipSec{sql1_byp4ss_l0g1n}",
        "extra_env": "ENV CTF_DB_PATH=/tmp/users.db\n\n",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "007",
        "port_web": 8007,
        "default_flag": "EclipSec{1d0r_c4n_b3_d4ng3r0us}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "008",
        "port_web": 8008,
        "default_flag": "EclipSec{sst1_t3mpl4t3_1nj3ct10n}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "009",
        "port_web": 8009,
        "default_flag": "EclipSec{b4ckup_f1l3s_4r3_l34ks}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "010",
        "port_web": 8010,
        "default_flag": "EclipSec{h34d3rs_c4n_b3_sp00f3d}",
        "build_steps": _STANDARD_DOT_FLAG_STEPS,
    },
    {
        "id": "011",
        "port_web": 8011,
        "default_flag": "EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}",
        "build_steps": _STANDARD_TXT_FLAG_STEPS,
    },
]


def render_dockerfile(spec: ChallengeSpec) -> str:
    """Render an isolated, non-root, read-only compatible Dockerfile referencing docker/shared/."""
    return (
        DOCKERFILE_FLASK_TEMPLATE
        .replace("__CHALLENGE_ID__", spec["id"])
        .replace("__EXTRA_APT__", spec.get("extra_apt", ""))
        .replace("__EXTRA_ENV__", spec.get("extra_env", ""))
        .replace("__DEFAULT_FLAG__", spec["default_flag"])
        .replace("__BUILD_STEPS__", spec["build_steps"])
    )


def render_service_entry(
    challenge_id: str,
    port_host: int,
    port_container: int,
    default_flag: str,
    mem_limit: str = "128m",
    cpus: str = "0.50",
    pids_limit: int = 64,
    cap_add_net_raw: bool = False,
) -> str:
    """Render a resource-bounded, hardened docker-compose service block."""
    env_var = f"FLAG_WEB_{challenge_id}"
    lines = [
        f"  web-{challenge_id}:",
        "    build:",
        "      context: ..",
        f"      dockerfile: docker/challenge-web-{challenge_id}/Dockerfile",
        "      args:",
        f"        CHALLENGE_FLAG: ${{{env_var}:-{default_flag}}}",
        f"    container_name: ctf-web-{challenge_id}",
        "    restart: unless-stopped",
        "    read_only: true",
        "    tmpfs:",
        '      - "/tmp:rw,noexec,nosuid,size=16m"',
        "    security_opt:",
        '      - "no-new-privileges:true"',
        "    cap_drop:",
        "      - ALL",
    ]
    if cap_add_net_raw:
        lines.extend(["    cap_add:", "      - NET_RAW"])
    lines.extend(
        [
            f"    mem_limit: {mem_limit}",
            f"    memswap_limit: {mem_limit}",
            f"    cpus: {cpus}",
            f"    pids_limit: {pids_limit}",
            "    ports:",
            f'      - "{port_host}:{port_container}"',
            "    networks:",
            "      - ctf-net",
        ]
    )
    return "\n".join(lines) + "\n"


def _prune_legacy_copies(ch_dir: Path) -> None:
    for legacy_name in ("global.css", "ui.py"):
        legacy_path = ch_dir / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()


def generate_challenges(base_dir: Path) -> None:
    """Sync standalone Dockerfiles (using shared UI assets) and docker-compose.yml."""
    ch001_dir = base_dir / "challenge-web-001"
    ch001_dir.mkdir(parents=True, exist_ok=True)
    _prune_legacy_copies(ch001_dir)
    (ch001_dir / "Dockerfile").write_text(DOCKERFILE_001, encoding="utf-8", newline="\n")

    service_blocks = [
        render_service_entry(
            "001",
            8001,
            8080,
            "EclipSec{h1dd3n_1n_pl41n_s1ght}",
            mem_limit="64m",
            cpus="0.25",
            pids_limit=32,
        )
    ]

    for spec in CHALLENGE_SPECS:
        ch_dir = base_dir / f"challenge-web-{spec['id']}"
        ch_dir.mkdir(parents=True, exist_ok=True)
        _prune_legacy_copies(ch_dir)
        (ch_dir / "Dockerfile").write_text(
            render_dockerfile(spec), encoding="utf-8", newline="\n"
        )
        service_blocks.append(
            render_service_entry(
                spec["id"],
                spec["port_web"],
                8000,
                spec["default_flag"],
                cap_add_net_raw=(spec["id"] == "004"),
            )
        )

    compose_content = (
        "services:\n"
        + "\n".join(service_blocks)
        + "\nnetworks:\n  ctf-net:\n    driver: bridge\n"
    )
    (base_dir / "docker-compose.yml").write_text(
        compose_content, encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate_challenges(BASE_DIR)
    print("Standalone Dockerfiles and docker-compose.yml synced.")
