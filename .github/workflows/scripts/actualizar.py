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
    "Accept": "application/rss+xml,application/xml,text/xml,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}

# Feeds RSS verificados. Para agregar otro medio, añade su feed aquí.
FEEDS = [
    ("Reforma", "https://www.reforma.com/rss/portada.xml"),
    ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml"),
    ("Excélsior", "https://www.excelsior.com.mx/rss"),
    ("El Heraldo", "https://heraldodemexico.com.mx/rss/feed.html?r=4"),
    ("El Financiero", "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml"),
]

# Respaldo para los medios sin feed verificado o si el feed falla.
RESPALDO = [
    ("El Universal", "Alerta financiera en la Modalidad 40 de pensiones",
     "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"),
]
RESPALDO_FECHA = "23 de octubre de 2026"


def limpiar(texto):
    texto = html.unescape(texto)
    texto = re.sub(r"<!\[CDATA\[|\]\]>", "", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    return " ".join(texto.split()).strip()


def ultimas_noticias(nombre, url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    items = re.findall(r"<item>(.*?)</item>", r.text, re.S)
    if not items:
        raise RuntimeError("el feed no tiene noticias")
    primero = re.search(r"<title>(.*?)</title>", items[0], re.S)
    link = re.search(r"<link>(.*?)</link>", items[0], re.S)
    if not primero:
        raise RuntimeError("no encontré el título")
    titular = limpiar(primero.group(1))
    enlace = limpiar(link.group(1)) if link else url
    return titular, enlace


def obtener_tendencias():
    fuentes = [
        ("Trends24 (X)", "https://trends24.in/mexico/", "trends24"),
        ("Google Trends México", "https://trends.google.com/trending/rss?geo=MX", "google"),
    ]
    for nombre, url, tipo in fuentes:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            if tipo == "trends24":
                m = re.search(
                    r"Today's top X \(Twitter\) trends and hashtags in Mexico:\s*(.+?)\.\s",
                    r.text,
                )
                if not m:
                    raise RuntimeError("no encontré la lista")
                temas = [t.strip() for t in html.unescape(m.group(1)).split(",") if t.strip()]
            else:
                titulos = re.findall(r"<item>.*?<title>(.*?)</title>", r.text, re.S)
                temas = []
                for t in titulos:
                    t = limpiar(t)
                    if t and t not in temas:
                        temas.append(t)
            if len(temas) < 3:
                raise RuntimeError("lista incompleta")
            return nombre, temas[:5]
        except Exception as e:
            print(f"Falló {nombre}: {e}")
    return None, []


def generar_pagina(tarjetas, tendencias, fuente_t, ahora):
    tarjetas_html = "\n".join(
        f"""  <article>
    <h2>{html.escape(medio)}</h2>
    <h3>{html.escape(titular)}</h3>
    <a href="{html.escape(enlace)}">{html.escape(etiqueta)}</a>
  </article>"""
        for medio, titular, enlace, etiqueta in tarjetas
    )
    if tendencias:
        items = "\n".join(f"    <li><strong>{html.escape(t)}</strong></li>" for t in tendencias)
        bloque = f"<ol>\n{items}\n  </ol>"
    else:
        bloque = "<p class=\"note\">No se pudieron leer las tendencias en esta actualización.</p>"

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Encabezados de periódicos de la CDMX</title>
<style>
  :root {{ --bg:#f6f4ef; --card:#fff; --ink:#1d1d1b; --muted:#6b6b66; --line:#e2dfd7; --accent:#8a1c1c; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Georgia,serif; line-height:1.5; }}
  header {{ padding:2rem 1rem 1rem; text-align:center; border-bottom:3px double var(--ink); max-width:960px; margin:0 auto; }}
  header h1 {{ margin:0; font-size:clamp(1.6rem,4vw,2.4rem); }}
  header p {{ margin:.4rem 0 0; color:var(--muted); font-family:system-ui,sans-serif; font-size:.95rem; }}
  main {{ max-width:960px; margin:0 auto; padding:1.5rem 1rem 1rem; display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }}
  article {{ background:var(--card); border:1px solid var(--line); border-top:4px solid var(--accent); padding:1rem 1.1rem; border-radius:4px; }}
  article h2 {{ font-family:system-ui,sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin:0 0 .5rem; }}
  article h3 {{ font-size:1.1rem; margin:0 0 .6rem; line-height:1.3; }}
  article a {{ font-family:system-ui,sans-serif; font-size:.85rem; color:var(--accent); text-decoration:none; }}
  .trending {{ max-width:960px; margin:0 auto; padding:1rem 1rem 2rem; border-top:3px double var(--ink); }}
  .trending h2 {{ font-family:system-ui,sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin:1rem 0 .4rem; }}
  .trending .note {{ font-family:system-ui,sans-serif; font-size:.8rem; color:var(--muted); margin:0 0 .8rem; }}
  .trending ol {{ padding-left:1.2rem; }}
  .trending li {{ margin-bottom:.5rem; font-size:.95rem; }}
  .actions {{ display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1rem; }}
  .actions button, .actions .btn {{ font-family:system-ui,sans-serif; font-size:.85rem; padding:.45rem .9rem; border-radius:4px; border:1px solid var(--accent); background:var(--accent); color:#fff; cursor:pointer; text-decoration:none; }}
  .actions .btn {{ background:transparent; color:var(--accent); }}
  footer {{ max-width:960px; margin:0 auto; padding:0 1rem 2rem; color:var(--muted); font-family:system-ui,sans-serif; font-size:.8rem; }}
</style>
</head>
<body>
<header>
  <h1>Encabezados de los periódicos de la CDMX</h1>
  <p>Actualizado: {ahora.strftime('%d/%m/%Y %H:%M')} (hora de CDMX)</p>
</header>

<main>
{tarjetas_html}
</main>

<section class="trending">
  <h2>Tendencias en México</h2>
  <p class="note">Fuente: {html.escape(fuente_t or 'no disponible')}</p>
  {bloque}
  <div class="actions">
    <button type="button" onclick="location.reload()">Recargar página</button>
    <a class="btn" href="https://trends.google.com/trending?geo=MX" target="_blank" rel="noopener">Google Trends</a>
    <a class="btn" href="https://trends24.in/mexico/" target="_blank" rel="noopener">Trends24 (X)</a>
  </div>
</section>

<footer>
  Titulares de los feeds RSS de cada medio. Los medios sin feed usan la portada del {RESPALDO_FECHA}.
</footer>
</body>
</html>
"""


def main():
    ahora = datetime.now(MX)
    tarjetas = []

    for medio, url in FEEDS:
        try:
            titular, enlace = ultimas_noticias(medio, url)
            tarjetas.append((medio, titular, enlace, "Leer nota"))
            print(f"{medio}: OK")
        except Exception as e:
            print(f"Falló {medio}: {e}")

    ya = {t[0] for t in tarjetas}
    for medio, titular, enlace in RESPALDO:
        if medio not in ya:
            tarjetas.append((medio, titular, enlace, f"Portada del {RESPALDO_FECHA}"))

    # Mantener el orden de los medios
    orden = ["Reforma", "El Universal", "Excélsior", "La Jornada", "El Heraldo", "El Financiero"]
    tarjetas.sort(key=lambda t: orden.index(t[0]) if t[0] in orden else 99)

    nombre_t, tendencias = obtener_tendencias()

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(generar_pagina(tarjetas, tendencias, nombre_t, ahora))
    print("index.html generado.")


if __name__ == "__main__":
    main()
