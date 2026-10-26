import html
import os
import re
from datetime import datetime, timedelta, timezone

import requests

SOURCE = "https://trends24.in/mexico/"
OUT_DIR = "."
OUT_FILE = os.path.join(OUT_DIR, "index.html")
MX = timezone(timedelta(hours=-6))

# Portadas: se actualizan a mano editando esta lista.
PORTADAS_FECHA = "23 de octubre de 2026"
PORTADAS = [
    ("Reforma", "Agasaja proveedor a directores del INE",
     "Funcionarios acuden a reuniones con Hernández Casillas; alertan consejeros sobre contratos millonarios.",
     "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"),
    ("El Universal", "Alerta financiera en la Modalidad 40 de pensiones",
     "La presidenta señala pérdidas de miles de millones de pesos desde 2023; la comisión de Seguridad Social evalúa citar a Zoé Robledo.",
     "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"),
    ("Excélsior", "A debate, los cambios a la Modalidad 40",
     "Sheinbaum justifica regular la norma tras detectar fraudes; Ricardo Monreal plantea legislar para darle permanencia jurídica.",
     "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"),
    ("La Jornada", "Sheinbaum: ajustes a la Modalidad 40 del IMSS por uso fraudulento",
     "La modalidad habría generado 27 mil millones de pesos al Instituto, pero no compensa la carga financiera.",
     "https://media.jornada.com.mx/2026/10/23/"),
    ("El Economista", "Existen 798 mil pensiones asociadas al plan de jubilación Modalidad 40",
     "Cifra que ubica el tema de las pensiones en el centro de la agenda económica del día.",
     "https://www.unotv.com/nacional/las-de-hoy-23-de-octubre-de-2026/"),
    ("La Razón", "Sheinbaum niega nexos “perversos” con el narco",
     "Entre los otros titulares de la edición: la CIA habría frenado la captura de El Chapo tres meses después de su fuga.",
     "https://www.razon.com.mx/version-impresa/2026/10/23/version-impresa-23-de-octubre-2026/"),
]


def obtener_tendencias():
    r = requests.get(
       SOURCE,
       headers={
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml",
           "Accept-Language": "es-MX,es;q=0.9",
       },
       timeout=30,
   )
    r.raise_for_status()
    m = re.search(
        r"Today's top X \(Twitter\) trends and hashtags in Mexico:\s*(.+?)\.\s",
        r.text,
    )
    if not m:
        raise RuntimeError("No se encontró la lista de tendencias en Trends24")
    texto = html.unescape(m.group(1))
    tendencias = [t.strip() for t in texto.split(",") if t.strip()]
    if len(tendencias) < 3:
        raise RuntimeError("La lista de tendencias llegó incompleta")
    return tendencias[:5]


def generar_pagina(tendencias, ahora):
    portadas_html = "\n".join(
        f"""  <article>
    <h2>{html.escape(medio)}</h2>
    <h3>{html.escape(titular)}</h3>
    <p>{html.escape(resumen)}</p>
    <a href="{html.escape(url)}">Fuente</a>
  </article>"""
        for medio, titular, resumen, url in PORTADAS
    )
    tendencias_html = "\n".join(
        f"    <li><strong>{html.escape(t)}</strong></li>" for t in tendencias
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
  article h3 {{ font-size:1.1rem; margin:0 0 .4rem; line-height:1.3; }}
  article p {{ margin:0 0 .6rem; font-size:.95rem; color:var(--muted); }}
  article a {{ font-family:system-ui,sans-serif; font-size:.85rem; color:var(--accent); text-decoration:none; }}
  .trending {{ max-width:960px; margin:0 auto; padding:1rem 1rem 2rem; border-top:3px double var(--ink); }}
  .trending h2 {{ font-family:system-ui,sans-serif; font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin:1rem 0 .4rem; }}
  .trending .note {{ font-family:system-ui,sans-serif; font-size:.8rem; color:var(--muted); margin:0 0 .8rem; }}
  .trending ol {{ padding-left:1.2rem; }}
  .trending li {{ margin-bottom:.5rem; font-size:.95rem; }}
  .trending .btn {{ display:inline-block; font-family:system-ui,sans-serif; font-size:.85rem; padding:.45rem .9rem; border:1px solid var(--accent); border-radius:4px; color:var(--accent); text-decoration:none; margin-top:.4rem; }}
  footer {{ max-width:960px; margin:0 auto; padding:0 1rem 2rem; color:var(--muted); font-family:system-ui,sans-serif; font-size:.8rem; }}
</style>
</head>
<body>
<header>
  <h1>Encabezados de los periódicos de la CDMX</h1>
  <p>Tendencias actualizadas: {ahora.strftime('%d/%m/%Y %H:%M')} (hora de CDMX)</p>
</header>

<main>
{portadas_html}
</main>

<section class="trending">
  <h2>Trending en X México</h2>
  <p class="note">Según Trends24. Se actualiza cada hora.</p>
  <ol>
{tendencias_html}
  </ol>
  <a class="btn" href="{SOURCE}" target="_blank" rel="noopener">Ver tendencias en vivo</a>
</section>

<footer>
  Portadas del {PORTADAS_FECHA}; se actualizan a mano. Las tendencias se actualizan solas.
</footer>
</body>
</html>
"""


def main():
    ahora = datetime.now(MX)
    tendencias = obtener_tendencias()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(generar_pagina(tendencias, ahora))
    print("Tendencias:", ", ".join(tendencias))


if __name__ == "__main__":
    main()
