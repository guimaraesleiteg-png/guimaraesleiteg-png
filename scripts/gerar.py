"""Gera os painéis SVG do README do perfil a partir dos dados públicos do GitHub.

Uso: python scripts/gerar.py            (grava em assets/)
Variáveis opcionais: GITHUB_TOKEN (evita limite da API), GH_USER.
"""
import base64
import datetime as dt
import html
import json
import os
import re
import urllib.request

USUARIO = os.environ.get("GH_USER", "guimaraesleiteg-png")
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Edite à vontade: tecnologias do painel "Stack principal" (nome, peso relativo, cor).
STACK = [
    ("TypeScript", 38, "#4ea1ff"),
    ("Go", 22, "#e6edf3"),
    ("PostgreSQL", 20, "#8b949e"),
    ("Python", 12, "#a371f7"),
    ("Docker", 8, "#3fb950"),
]

# Linhas de "habilidade" do cartão holográfico.
HABILIDADES = [
    ("Conciliação bancária", "OFX, APIs de bancos, boletos e Pix"),
    ("NFS-e nacional", "padrão nacional já com IBS/CBS"),
]

FONTE = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
W = 860


def esc(t):
    return html.escape(str(t), quote=True)


def baixar(url, json_=True):
    req = urllib.request.Request(url, headers={"User-Agent": "perfil-readme"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        dado = r.read()
    return json.loads(dado) if json_ else dado


def contribuicoes():
    """Lê o calendário público de contribuições. Retorna lista [(data, nivel, qtd)] em ordem."""
    pagina = baixar(f"https://github.com/users/{USUARIO}/contributions", json_=False).decode("utf-8")
    dias = {}
    for m in re.finditer(r'data-date="([\d-]+)"\s+id="([^"]+)"\s+data-level="(\d)"', pagina):
        dias[m.group(2)] = [m.group(1), int(m.group(3)), 0]
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)', pagina):
        if m.group(1) in dias:
            q = re.match(r"([\d,]+) contribution", m.group(2))
            dias[m.group(1)][2] = int(q.group(1).replace(",", "")) if q else 0
    return sorted((tuple(v) for v in dias.values()), key=lambda d: d[0])


def sequencias(dias):
    hoje = dias[-1][0] if dias else None
    maior = atual = corrida = 0
    for d, _, q in dias:
        corrida = corrida + 1 if q > 0 else 0
        maior = max(maior, corrida)
    # sequência atual: termina hoje ou ontem
    i = len(dias) - 1
    if i >= 0 and dias[i][2] == 0:
        i -= 1
    while i >= 0 and dias[i][2] > 0:
        atual += 1
        i -= 1
    return atual, maior, hoje


# ---------- moldura compartilhada ----------

def defs_moldura(uid):
    return f"""
  <defs>
    <radialGradient id="{uid}a" cx="0.18" cy="0" r="0.45"><stop offset="0" stop-color="#2f6fb8" stop-opacity=".55"/><stop offset="1" stop-color="#2f6fb8" stop-opacity="0"/></radialGradient>
    <radialGradient id="{uid}b" cx="0.68" cy="0.15" r="0.5"><stop offset="0" stop-color="#1f7a3a" stop-opacity=".45"/><stop offset="1" stop-color="#1f7a3a" stop-opacity="0"/></radialGradient>
    <radialGradient id="{uid}c" cx="0.62" cy="1.05" r="0.4"><stop offset="0" stop-color="#7b4bc4" stop-opacity=".5"/><stop offset="1" stop-color="#7b4bc4" stop-opacity="0"/></radialGradient>
    <radialGradient id="{uid}d" cx="1" cy="0.95" r="0.35"><stop offset="0" stop-color="#1b8a8a" stop-opacity=".45"/><stop offset="1" stop-color="#1b8a8a" stop-opacity="0"/></radialGradient>
  </defs>"""


def moldura(h, uid, corpo, interno=True):
    m = 28
    painel = (f'<rect x="{m}" y="{m}" width="{W-2*m}" height="{h-2*m}" rx="18" fill="#0d1117" fill-opacity=".55" '
              f'stroke="#58a6ff" stroke-opacity=".35"/>' if interno else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{FONTE}">{defs_moldura(uid)}
  <rect x=".5" y=".5" width="{W-1}" height="{h-1}" rx="22" fill="#0d1117" stroke="#2f5f93" stroke-opacity=".8"/>
  <g>
    <rect width="{W}" height="{h}" rx="22" fill="url(#{uid}a)"/>
    <rect width="{W}" height="{h}" rx="22" fill="url(#{uid}b)"/>
    <rect width="{W}" height="{h}" rx="22" fill="url(#{uid}c)"/>
    <rect width="{W}" height="{h}" rx="22" fill="url(#{uid}d)"/>
  </g>
  {painel}
{corpo}
</svg>
"""


# ---------- painéis ----------

def cartao_holo(perfil, total, atual, avatar_b64):
    h = 372
    cx, cy, cw, ch = 52, 55, 210, 262
    nome = perfil.get("name") or USUARIO
    bio = [p.strip() for p in (perfil.get("bio") or "").split("|") if p.strip()]
    desde = perfil.get("created_at", "")[:7]
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    desde_txt = f"{meses[int(desde[5:7]) - 1]}/{desde[:4]}" if desde else ""
    meta = " · ".join(x for x in [perfil.get("company"), perfil.get("location"), f"desde {desde_txt}" if desde_txt else None] if x)

    linhas_bio = "".join(
        f'<text x="300" y="{118 + i*22}" fill="#9fb0c3" font-size="{15 if i == 0 else 13.5}">{esc(t)}</text>'
        for i, t in enumerate(bio[:3]))
    y0 = 118 + len(bio[:3]) * 22 + 14
    habs = "".join(
        f'<g transform="translate(300,{y0 + i*34})"><rect width="500" height="26" rx="8" fill="#ffffff" fill-opacity=".04" stroke="#58a6ff" stroke-opacity=".25"/>'
        f'<rect width="3" height="26" rx="1.5" fill="{["#4ea1ff", "#3fb950", "#a371f7"][i % 3]}"/>'
        f'<text x="14" y="17.5" font-size="12.5" fill="#e6edf3" font-weight="600">{esc(a)}'
        f'<tspan fill="#8b949e" font-weight="400">  —  {esc(b)}</tspan></text></g>'
        for i, (a, b) in enumerate(HABILIDADES))
    chips = [("REPOS", perfil.get("public_repos", 0)), ("CONTRIB.", total), ("SEQUÊNCIA", atual), ("SEGUIDORES", perfil.get("followers", 0))]
    chips_svg = "".join(
        f'<g transform="translate({300 + i*126},{y0 + len(HABILIDADES)*34 + 42})"><text font-size="10" letter-spacing="2" fill="#6e7f94" font-weight="700">{esc(r)}</text>'
        f'<text y="24" font-size="22" font-weight="700" fill="#e6edf3" font-family="{MONO}">{esc(v)}</text></g>'
        for i, (r, v) in enumerate(chips))

    avatar = (f'<image href="data:image/jpeg;base64,{avatar_b64}" x="{cx+14}" y="{cy+36}" width="{cw-28}" height="{cw-28}" '
              f'preserveAspectRatio="xMidYMid slice" clip-path="url(#hfoto)"/>') if avatar_b64 else ""

    corpo = f"""
  <defs>
    <linearGradient id="hfoil" x1="0" y1="0" x2="1" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0" stop-color="#ff6ec7"/><stop offset=".17" stop-color="#ffd36e"/><stop offset=".34" stop-color="#7cff9c"/>
      <stop offset=".5" stop-color="#6ee7ff"/><stop offset=".67" stop-color="#8a7dff"/><stop offset=".84" stop-color="#ff6ec7"/><stop offset="1" stop-color="#ffd36e"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1 -1;0 0;-1 -1" dur="7s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="hbrilho" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="hcarta"><rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16"/></clipPath>
    <clipPath id="hfoto"><rect x="{cx+14}" y="{cy+36}" width="{cw-28}" height="{cw-28}" rx="10"/></clipPath>
  </defs>
  <g>
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="5s" repeatCount="indefinite"/>
    <rect x="{cx-3}" y="{cy-3}" width="{cw+6}" height="{ch+6}" rx="18" fill="url(#hfoil)" opacity=".9"/>
    <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16" fill="#111824"/>
    <g clip-path="url(#hcarta)">
      <text x="{cx+14}" y="{cy+24}" font-size="11" font-weight="700" letter-spacing="1.5" fill="#e6edf3">#001</text>
      <text x="{cx+cw-14}" y="{cy+24}" font-size="10" font-weight="700" letter-spacing="1.5" fill="#ffd36e" text-anchor="end">★ HOLO RARO</text>
      {avatar}
      <rect x="{cx+14}" y="{cy+36}" width="{cw-28}" height="{cw-28}" rx="10" fill="none" stroke="#fff" stroke-opacity=".25"/>
      <text x="{cx + cw/2}" y="{cy+ch-26}" font-size="12" font-weight="700" fill="#e6edf3" text-anchor="middle">@{esc(USUARIO)}</text>
      <text x="{cx + cw/2}" y="{cy+ch-11}" font-size="9.5" letter-spacing="1.5" fill="#8b949e" text-anchor="middle">FULL-STACK · FISCAL</text>
      <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="url(#hfoil)" opacity=".22" style="mix-blend-mode:color-dodge"/>
      <rect x="{cx-160}" y="{cy-40}" width="90" height="{ch+80}" fill="url(#hbrilho)" opacity=".5" transform="rotate(18 {cx} {cy})">
        <animate attributeName="x" values="{cx-200};{cx+cw+120}" dur="4.5s" repeatCount="indefinite"/>
      </rect>
    </g>
  </g>
  <text x="300" y="62" font-size="11" letter-spacing="4" fill="#7d8da1" font-weight="700">CARTA DE COLECIONADOR · EDIÇÃO {dt.date.today().year}</text>
  <text x="300" y="94" font-size="30" font-weight="800" fill="#f0f6fc">{esc(nome)}</text>
  {linhas_bio}
  {habs}
  <text x="300" y="{y0 + len(HABILIDADES)*34 + 12}" font-size="12" fill="#6e7f94">{esc(meta)}</text>
  {chips_svg}"""
    return moldura(h, "h", corpo, interno=False)


def sinais(perfil, estrelas, total, atual, maior):
    h = 190
    itens = [("Estrelas", estrelas, "#4ea1ff"), ("Contribuições", total, "#2bc4c4"),
             ("Repositórios", perfil.get("public_repos", 0), "#a371f7"), ("Seguidores", perfil.get("followers", 0), "#3fb950"),
             ("Sequência atual", atual, "#ffd36e"), ("Maior sequência", maior, "#ff7b72")]
    maxv = max([v for _, v, _ in itens] + [1])
    larg = (W - 2*48 - 5*12) / 6
    blocos = ""
    for i, (rot, v, cor) in enumerate(itens):
        x = 48 + i * (larg + 12)
        frac = max(0.06, v / maxv)
        blocos += (f'<g transform="translate({x:.1f},86)"><rect width="{larg:.1f}" height="72" rx="12" fill="#0d1117" fill-opacity=".6" stroke="#58a6ff" stroke-opacity=".3"/>'
                   f'<text x="12" y="20" font-size="10.5" fill="#8b949e" font-weight="600">{esc(rot)}</text>'
                   f'<text x="12" y="46" font-size="22" font-weight="800" fill="{cor}" font-family="{MONO}">{v}</text>'
                   f'<rect x="12" y="56" width="{larg-24:.1f}" height="4" rx="2" fill="#ffffff" fill-opacity=".08"/>'
                   f'<rect x="12" y="56" width="0" height="4" rx="2" fill="{cor}"><animate attributeName="width" from="0" to="{(larg-24)*frac:.1f}" dur="1.4s" begin="{i*0.12:.2f}s" fill="freeze"/></rect></g>')
    corpo = f"""
  <text x="48" y="62" font-size="20" font-weight="800" fill="#f0f6fc">Sinais do perfil</text>
  <text x="{W-48}" y="62" font-size="12" fill="#58a6ff" text-anchor="end" font-family="{MONO}">&gt; perfil.scan</text>
  {blocos}"""
    return moldura(h, "s", corpo)


def stack():
    h = 70 + 56 + len(STACK) * 30 + 30
    total = sum(p for _, p, _ in STACK) or 1
    linhas = ""
    for i, (nome, p, cor) in enumerate(STACK):
        y = 126 + i * 30
        pct = round(100 * p / total)
        larg = 380 * p / max(q for _, q, _ in STACK)
        linhas += (f'<circle cx="60" cy="{y-4}" r="4.5" fill="{cor}"/>'
                   f'<text x="76" y="{y}" font-size="13.5" font-weight="700" fill="#e6edf3">{esc(nome)}</text>'
                   f'<text x="370" y="{y}" font-size="13" font-weight="700" fill="{cor}" text-anchor="end" font-family="{MONO}">{pct}%</text>'
                   f'<rect x="400" y="{y-9}" width="410" height="7" rx="3.5" fill="#ffffff" fill-opacity=".08"/>'
                   f'<rect x="400" y="{y-9}" width="0" height="7" rx="3.5" fill="{cor}"><animate attributeName="width" from="0" to="{larg:.1f}" dur="1.2s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>')
    corpo = f"""
  <text x="52" y="72" font-size="22" font-weight="800" fill="#f0f6fc">Stack principal</text>
  <text x="52" y="94" font-size="13" fill="#8b949e" font-weight="600">Tecnologias que uso no dia a dia</text>
  <text x="{W-60}" y="72" font-size="12" fill="#58a6ff" text-anchor="end" font-family="{MONO}">&gt; stack.scan</text>
  {linhas}"""
    return moldura(h, "t", corpo)


def destaques(perfil, estrelas, total):
    h = 180
    cards = [("Código aberto", f"{perfil.get('public_repos', 0)} repositório(s) público(s)", "#4ea1ff"),
             ("Ritmo", f"{total} contribuições no último ano", "#3fb950"),
             ("Comunidade", f"{perfil.get('followers', 0)} seguidores · {estrelas} estrelas", "#a371f7")]
    larg = (W - 2*28 - 2*16) / 3
    blocos = ""
    for i, (t, s, cor) in enumerate(cards):
        x = 28 + i * (larg + 16)
        blocos += (f'<g transform="translate({x:.1f},60)"><rect width="{larg:.1f}" height="96" rx="16" fill="#0d1117" fill-opacity=".6" stroke="#58a6ff" stroke-opacity=".35"/>'
                   f'<rect x="0" y="22" width="4" height="52" rx="2" fill="{cor}"/>'
                   f'<text x="24" y="40" font-size="15" font-weight="800" fill="#f0f6fc">{esc(t)}</text>'
                   f'<text x="24" y="64" font-size="12.5" fill="#9fb0c3">{esc(s)}</text></g>')
    corpo = f"""
  <text x="30" y="44" font-size="11" letter-spacing="4" fill="#7d8da1" font-weight="700">DESTAQUES</text>
  {blocos}"""
    return moldura(h, "d", corpo, interno=False)


def atividade(dias, total):
    h = 270
    cel, gap = 11, 3
    x0, y0 = 48, 104
    if not dias:
        dias = []
    # coluna = semana; linha = dia da semana (domingo = 0)
    primeiro = dt.date.fromisoformat(dias[0][0]) if dias else dt.date.today()
    deslocamento = (primeiro.weekday() + 1) % 7
    cores = ["#ffffff", "#1f4f8a", "#2a6fc4", "#3d8bfd", "#79b8ff"]
    celulas, pontos = "", []
    for i, (d, nivel, q) in enumerate(dias):
        idx = i + deslocamento
        col, lin = idx // 7, idx % 7
        x, y = x0 + col * (cel + gap), y0 + lin * (cel + gap)
        op = ' fill-opacity=".06"' if nivel == 0 else ""
        celulas += f'<rect x="{x}" y="{y}" width="{cel}" height="{cel}" rx="2.5" fill="{cores[nivel]}"{op}/>'
        if q > 0:
            pontos.append((x + cel / 2, y + cel / 2))
    if len(pontos) < 2:
        pontos = [(x0 + cel / 2, y0 + cel / 2), (x0 + 52 * (cel + gap) + cel / 2, y0 + 6 * (cel + gap) + cel / 2)] if not pontos else [pontos[0], (pontos[0][0], pontos[0][1] + 0.01)]
    caminho = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    dur = max(3.0, min(18.0, len(pontos) * 0.9))
    rastro = "".join(
        f'<circle r="{3.2 - k*0.45:.2f}" fill="#58a6ff" fill-opacity="{0.75 - k*0.12:.2f}"><animateMotion path="{caminho}" dur="{dur}s" begin="-{(k+1)*dur*0.035:.2f}s" repeatCount="indefinite"/></circle>'
        for k in range(5))
    cabeca = (f'<g><animateMotion path="{caminho}" dur="{dur}s" repeatCount="indefinite"/>'
              f'<rect x="-7" y="-7" width="14" height="14" rx="4" fill="#e6f1ff"/>'
              f'<circle cx="-2.6" cy="-0.5" r="1.4" fill="#0d1117"/><circle cx="2.6" cy="-0.5" r="1.4" fill="#0d1117"/></g>')
    apagado = ' fill-opacity=".06"'
    legenda = "".join(f'<rect x="{W-160 + i*15}" y="62" width="11" height="11" rx="2.5" fill="{c}"{apagado if i == 0 else ""}/>' for i, c in enumerate(cores))
    corpo = f"""
  <text x="48" y="64" font-size="11" letter-spacing="4" fill="#58a6ff" font-weight="700">RASTRO DA COBRINHA</text>
  <text x="48" y="88" font-size="20" font-weight="800" fill="#f0f6fc">{total} contribuições, uma corrida contínua</text>
  <text x="{W-172}" y="72" font-size="10.5" fill="#8b949e" text-anchor="end">menos</text>
  {legenda}
  <text x="{W-84}" y="72" font-size="10.5" fill="#8b949e">mais</text>
  <g>{celulas}</g>
  {rastro}
  {cabeca}"""
    return moldura(h, "a", corpo)


def main():
    os.makedirs(SAIDA, exist_ok=True)
    perfil = baixar(f"https://api.github.com/users/{USUARIO}")
    repos = baixar(f"https://api.github.com/users/{USUARIO}/repos?per_page=100")
    estrelas = sum(r.get("stargazers_count", 0) for r in repos)
    dias = contribuicoes()
    total = sum(q for _, _, q in dias)
    atual, maior, _ = sequencias(dias)
    try:
        avatar = base64.b64encode(baixar(perfil["avatar_url"] + "&s=240", json_=False)).decode()
    except Exception:
        avatar = ""
    arquivos = {
        "holo-card.svg": cartao_holo(perfil, total, atual, avatar),
        "sinais.svg": sinais(perfil, estrelas, total, atual, maior),
        "stack.svg": stack(),
        "destaques.svg": destaques(perfil, estrelas, total),
        "atividade.svg": atividade(dias, total),
    }
    for nome, svg in arquivos.items():
        with open(os.path.join(SAIDA, nome), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
    print(f"ok: {len(arquivos)} painéis · {total} contribuições · sequência {atual}/{maior} · {estrelas} estrelas")


if __name__ == "__main__":
    main()
