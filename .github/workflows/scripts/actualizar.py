import html
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

OUT_FILE = "index.html"
MX = timezone(timedelta(hours=-6))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MEDIOS = ["Reforma", "El Universal", "Excélsior", "La Jornada", "El Economista",
          "La Razón", "Milenio", "El Heraldo", "La Crónica", "El Financiero"]

# Respaldo: se usa si UnoTV no responde o si todavía no existe la página de hoy.
RESPALDO_FECHA = "23 de octubre de 2026"
RESPALDO_URL = "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"
RESPALDO_PORTADAS = [
    ("Reforma", "Agasaja proveedor a directores del INE"),
    ("El Universal", "Alerta financiera en la Modalidad 40 de pensiones"),
    ("Excélsior", "A debate, los cambios a la Modalidad 40"),
    ("La Jornada", "Sheinbaum: ajustes a la Modalidad 40 del IMSS por uso fraudulento"),
    ("El Economista", "Existen 798 mil pensiones asociadas al plan de jubilación Modalidad 40"),
    ("La Razón", "Sheinbaum niega nexos “perversos” con el narco"),
]


def url_portadas(fecha):
    return (f"https://www.unotv.com/nacional/las-de-hoy-{fecha.day}-de-"
            f"{MESES[fecha.month - 1]}-de-{fecha.year}/")


def obtener_portadas(fecha):
    url = url_portadas(fecha)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    patron = re.compile(
        r"^\s*-\s*\*\*(" + "|".join(re.escape(m) for m in MEDIOS) + r"):?\*\*:?\s*(.+)$",
        re.M,
    )
    portadas = []
    vistos = set()
    for medio, titular in patron.findall(r.text):
        titular = html.unescape(titular).strip().strip("*").strip()
        if titular and medio not in vistos:
            vistos.add(medio)
            portadas.append((medio, titular))
    if len(portadas) < 3:
        raise RuntimeError("no encontré los titulares de hoy")
    return portadas, url


def parse_trends24(texto):
    m = re.search(
        r"Today's top X \(Twitter\) trends and hashtags in Mexico:\s*(.+?)\.\s", texto
    )
    if not m:
        raise RuntimeError("no encontré la lista")
    return [t.strip() for t in html.unescape(m.group(1)).split(",") if t.strip()]


def parse_google_rss(texto):
    titulos = re.findall(r"<item>.*?<title>(.*?)</title>", texto, re.S)
    temas = []
    for t in titulos:
        t = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", t)).strip()
        if t and t not in temas:
            temas.append(t)
    if len(temas) < 3:
        raise RuntimeError("no encontré los títulos")
    return temas


FUENTES_TENDENCIAS = [
    ("Trends24 (X)", "https://trends24.in/mexico/", parse_trends24),
    ("Google Trends México", "https://trends.google.com/trending/rss?geo=MX", parse_google_rss),
]

CSS = """
  :root { --bg:#f6f4ef; --card:#fff; --ink:#1d1d1b; --muted:#6b6b66; --line:#e2dfd7; --accent:#8a1c1c; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:Georgia,serif; line-height:1.5; }
  header { padding:2rem 1rem 1rem; text-align:center; border-bottom:3px double var(--ink); max-width:960px; margin:0 auto; }
  header h1 { margin:0; font-size:clamp(1.6rem,4vw,2.4rem); }
  header p { margin:.4rem 0 0; color:var(--muted); font-family:system-ui,sans-serif; font-size:.95rem; }
  main { max-width:960px; margin:0 auto; padding:1.5rem 1rem 1rem; display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }
  article { background:var(--card); border:1px solid var(--line); border-top:4px solid var(--accent); padding:1rem 1.1rem; border-radius:4px; }
  article h2 { font-family:system-ui,sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin:0 0 .5rem; }
  article h3 { font-size:1.1rem; margin:0 0 .6rem; line-height:1.3; }
  article a { font-family:system-ui,sans-serif; font-size:.85rem; color:var(--accent); text-decoration:none; }
  .trending { max-width:960px; margin:0 auto; padding:1rem 1rem 2rem; border-top:3px double var(--ink); }
  .trending h2 { font-family:system-ui,sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin:1rem 0 .4rem; }
  .trending .note { font-family:system-ui,sans-serif; font-size:.8rem; color:var(--muted); margin:0 0 .8rem; }
  .trending ol { padding-left:1.2rem; }
  .trending li { margin-bottom:.5rem; font-size:.95rem; }
  footer { max-width:960px; margin:0 auto; padding:0 1rem 2rem; color:var(--muted); font-family:system-ui,sans-serif; font-size:.8rem; }
  .actions { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1rem; }
  .actions button, .actions .btn { font-family:system-ui,sans-serif; font-size:.85rem; padding:.45rem .9rem; border-radius:4px; border:1px solid var(--accent); background:var(--accent); color:#fff; cursor:pointer; text-decoration:none; }
  .actions .btn { background:transparent; color:var(--accent); }
"""


def generar_pagina(portadas, fecha_portadas, url_portadas_fuente, es_respaldo,
                   tendencias, fuente_tendencias, ahora):
    tarjetas = "\n".join(
        f"""  <article>
    <h2>{html.escape(medio)}</h2>
    <h3>{html.escape(titular)}</h3>
    <a href="{html.escape(url_portadas_fuente)}">Ver portadas del día</a>
  </article>"""
        for medio, titular in portadas
    )
    if tendencias:
        items = "\n".join(f"    <li><strong>{html.escape(t)}</strong></li>" for t in tendencias)
        bloque_tend = f"<ol>\n{items}\n  </ol>"
    else:
        bloque_tend = "<p class=\"note\">No se pudieron leer las tendencias en esta actualización.</p>"

    aviso = (" Se muestran las portadas de respaldo porque no se encontraron las de hoy."
             if es_respaldo else "")

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Encabezados de periódicos de la CDMX</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Encabezados de los periódicos de la CDMX</h1>
  <p>Actualizado: {ahora.strftime('%d/%m/%Y %H:%M')} (hora de CDMX) · Portadas del {html.escape(fecha_portadas)}</p>
</header>

<main>
{tarjetas}
</main>

<section class="trending">
  <h2>Tendencias en México</h2>
  <p class="note">Fuente: {html.escape(fuente_tendencias or 'no disponible')}</p>
  {bloque_tend}
  <div class="actions">
    <button type="button" onclick="location.reload()">Recargar página</button>
#    <a class="btn" href="https://trends.google.com/trending?geo=MX" target="_blank" rel="noopener">Ver tendencias en vivo</a>
     <a class="btn" href="https://trends.google.com/trending?geo=MX" target="_blank" rel="noopener">Google Trends</a>
     <a class="btn" href="https://trends24.in/mexico/" target="_blank" rel="noopener">Trends24 (X)</a>
  </div>
</section>

<footer>
  Portadas tomadas de UnoTV.{aviso}
</footer>
</body>
</html>
"""


def main():
    ahora = datetime.now(MX)

    try:
        portadas, url_p = obtener_portadas(ahora)
        fecha_p = f"{ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
        es_respaldo = False
        print(f"Portadas de hoy: {len(portadas)} encontradas")
    except Exception as e:
        print(f"No se pudieron leer las portadas de hoy: {e}")
        portadas = RESPALDO_PORTADAS
        url_p = RESPALDO_URL
        fecha_p = RESPALDO_FECHA
        es_respaldo = True

    tendencias, fuente_t = [], None
    for nombre, url, parser in FUENTES_TENDENCIAS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            tendencias = parser(r.text)[:5]
            fuente_t = nombre
            break
        except Exception as e:
            print(f"Falló {nombre}: {e}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(generar_pagina(portadas, fecha_p, url_p, es_respaldo,
                               tendencias, fuente_t, ahora))
    print("index.html generado.")


if __name__ == "__main__":
    main()
