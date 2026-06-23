"""
BOARD WEB de la ARENA — genera board.html listo para abrir en el navegador.
Lee los JSON de paper_arena y construye una tabla visual con todos los datos relevantes.

Uso:  python -m trading_latino.live.board_web
      (genera data_store/paper_arena/board.html — ábrir en navegador)
"""
from __future__ import annotations
import json
import time
from collections import defaultdict
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
MIN_VEREDICTO = 15   # n mínimo para dar veredicto firme

POLITICAS = ("fixed", "be05", "be10", "t125", "trail")
POL_LABEL = {"fixed": "2R fijo", "be05": "BE0.5R", "be10": "BE1R", "t125": "1.25R", "trail": "Trail"}


def _stat(vals):
    if not vals:
        return 0, None, None
    n = len(vals)
    win = sum(1 for v in vals if v > 0) / n
    exp = sum(vals) / n
    return n, win, exp


def _color(exp, n, min_n=MIN_VEREDICTO):
    if n < min_n:
        return "#888"        # gris — poca muestra
    if exp > 0.15:
        return "#22c55e"     # verde fuerte
    if exp > 0.02:
        return "#86efac"     # verde suave
    if exp >= -0.05:
        return "#fbbf24"     # amarillo — neutral
    if exp >= -0.20:
        return "#f97316"     # naranja — negativo
    return "#ef4444"         # rojo — retirar


def _veredicto(exp, n, min_n=MIN_VEREDICTO):
    if n < min_n:
        return "📊 recopilando datos"
    if exp > 0.20:
        return "✅ GANADORA"
    if exp > 0.05:
        return "🟢 prometedora"
    if exp >= -0.05:
        return "🟡 neutral"
    if exp >= -0.20:
        return "🟠 débil"
    return "❌ retirar"


def cargar():
    """Devuelve (ops_por_competidor, agregado_por_estr)."""
    competidores = []
    estr_agg = defaultdict(list)
    for f in sorted(REG.glob("*.json")):
        if f.stem.startswith("_"):
            continue
        parts = f.stem.split("_")
        tf = parts[-1]; coin = parts[-2]; estr = "_".join(parts[:-2])
        try:
            ops = json.loads(f.read_text())
        except Exception:
            continue
        cerr = [o for o in ops if o.get("status") == "cerrada" and isinstance(o.get("exits"), dict)]
        ab = [o for o in ops if o.get("status") == "abierta"]
        pnls = [o["pnl"] for o in cerr]
        exits_por_pol = {p: [o["exits"][p] for o in cerr if p in o.get("exits", {})] for p in POLITICAS}
        sesiones = defaultdict(list)
        for o in cerr:
            sesiones[o.get("sesion", "?")].append(o["exits"]["fixed"])
        mtime = f.stat().st_mtime
        competidores.append({
            "estr": estr, "coin": coin, "tf": tf,
            "cerradas": len(cerr), "abiertas": len(ab),
            "pnls": pnls, "exits": exits_por_pol,
            "sesiones": dict(sesiones), "mtime": mtime,
        })
        estr_agg[estr].extend(pnls)
    return competidores, estr_agg


def css():
    return """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #e2e8f0; padding: 20px; }
    h1 { font-size: 1.4rem; color: #f8fafc; margin-bottom: 4px; }
    .sub { font-size: 0.8rem; color: #64748b; margin-bottom: 24px; }
    h2 { font-size: 1.05rem; color: #94a3b8; margin: 24px 0 10px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    th { background: #1e293b; color: #94a3b8; padding: 8px 10px; text-align: left; font-weight: 600;
         position: sticky; top: 0; z-index: 10; white-space: nowrap; }
    td { padding: 7px 10px; border-bottom: 1px solid #1a1a2e; white-space: nowrap; }
    tr:hover td { background: #1e293b; }
    .n { color: #64748b; font-size: 0.78rem; }
    .pos { color: #22c55e; font-weight: 600; }
    .neg { color: #ef4444; font-weight: 600; }
    .neu { color: #fbbf24; }
    .grey { color: #64748b; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 0.72rem;
             font-weight: 600; }
    .tag-winner { background: #14532d; color: #86efac; }
    .tag-prom   { background: #052e16; color: #4ade80; }
    .tag-neutral{ background: #422006; color: #fbbf24; }
    .tag-weak   { background: #431407; color: #fb923c; }
    .tag-retire { background: #450a0a; color: #f87171; }
    .tag-data   { background: #1e293b; color: #94a3b8; }
    .pol-best   { background: #1a3a1a; color: #86efac; border-radius: 4px; padding: 2px 4px; }
    .coins      { color: #7dd3fc; font-size: 0.75rem; }
    .ses-good   { color: #4ade80; }
    .ses-bad    { color: #f87171; }
    .ses-neutral{ color: #fbbf24; }
    .sep { border-left: 2px solid #1e293b; }
    """


def fila_estr(estr, pnls, agg_exits=None):
    n, win, exp = _stat(pnls)
    color = _color(exp, n)
    ver = _veredicto(exp, n)
    # badge class
    bclass = ("tag-winner" if "GANADORA" in ver else
              "tag-prom" if "prometedora" in ver else
              "tag-neutral" if "neutral" in ver else
              "tag-weak" if "débil" in ver else
              "tag-retire" if "retirar" in ver else "tag-data")
    wt = f"{win*100:.0f}%" if win is not None else "—"
    et = f"{exp:+.2f}R" if exp is not None else "—"
    ec = "pos" if (exp or 0) > 0 else ("neg" if (exp or 0) < -0.02 else "neu")
    cells = [
        f'<td style="color:{color};font-weight:700">{estr}</td>',
        f'<td class="n">{n}</td>',
        f'<td class="{"pos" if (win or 0)>0.55 else ("neg" if (win or 0)<0.40 else "neu")}">{wt}</td>',
        f'<td class="{ec}">{et}</td>',
    ]
    if agg_exits:
        for pol in POLITICAS:
            vals = agg_exits.get(pol, [])
            _, _, ep = _stat(vals)
            pt = f"{ep:+.2f}R" if ep is not None else "—"
            pc = "pos" if (ep or 0) > 0.02 else ("neg" if (ep or 0) < -0.02 else "neu")
            cells.append(f'<td class="{pc} sep">{pt}</td>')
    cells.append(f'<td><span class="badge {bclass}">{ver}</span></td>')
    return "<tr>" + "".join(cells) + "</tr>\n"


def tabla_resumen(competidores, estr_agg):
    # Agregar exits por estrategia
    estr_exits = defaultdict(lambda: defaultdict(list))
    for c in competidores:
        for pol, vals in c["exits"].items():
            estr_exits[c["estr"]][pol].extend(vals)

    filas_data = []
    for estr, pnls in estr_agg.items():
        n, _, exp = _stat(pnls)
        filas_data.append((estr, pnls, exp or 0, n))
    filas_data.sort(key=lambda x: -x[2])

    heads = "".join(f"<th>{h}</th>" for h in
                    ["Estrategia", "N ops", "Win%", "Retorno (fixed)"] +
                    [f"Salida: {POL_LABEL[p]}" for p in POLITICAS] + ["Veredicto"])
    rows = "".join(fila_estr(estr, pnls, estr_exits.get(estr)) for estr, pnls, _, _ in filas_data)
    return f"<table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table>"


def tabla_detalle(competidores):
    # Ordenar: primero las que tienen datos, por retorno desc
    with_data = sorted([c for c in competidores if c["cerradas"] > 0], key=lambda x: -sum(x["pnls"]) / (len(x["pnls"]) or 1))
    sin_data = [c for c in competidores if c["cerradas"] == 0]

    heads = "".join(f"<th>{h}</th>" for h in
                    ["Estrategia", "Moneda", "TF", "Cerradas", "Abiertas", "Win%",
                     "Ret(fixed)", "Asia", "Londres", "NY", "Veredicto"])

    def fila(c):
        n, win, exp = _stat(c["pnls"])
        color = _color(exp, n, min_n=5)
        ver = _veredicto(exp, n, min_n=5)
        bclass = ("tag-winner" if "GANADORA" in ver else
                  "tag-prom" if "prometedora" in ver else
                  "tag-neutral" if "neutral" in ver else
                  "tag-weak" if "débil" in ver else
                  "tag-retire" if "retirar" in ver else "tag-data")
        wt = f"{win*100:.0f}%" if win is not None else "—"
        et = f"{exp:+.2f}R" if exp is not None else "—"
        ec = "pos" if (exp or 0) > 0 else ("neg" if (exp or 0) < -0.02 else "neu")

        def ses_cel(ses):
            v = c["sesiones"].get(ses, [])
            if not v:
                return '<td class="grey">—</td>'
            _, _, ep = _stat(v)
            cl = "ses-good" if (ep or 0) > 0.05 else ("ses-bad" if (ep or 0) < -0.05 else "ses-neutral")
            return f'<td class="{cl}">{ep:+.2f}R<span class="n"> n={len(v)}</span></td>'

        return (f'<tr>'
                f'<td style="color:{color};font-weight:600">{c["estr"]}</td>'
                f'<td class="coins">{c["coin"]}</td>'
                f'<td class="grey">{c["tf"]}</td>'
                f'<td class="n">{n}</td>'
                f'<td class="n">{c["abiertas"]}</td>'
                f'<td class="{"pos" if (win or 0)>0.55 else ("neg" if (win or 0)<0.40 else "neu")}">{wt}</td>'
                f'<td class="{ec}">{et}</td>'
                + ses_cel("asia") + ses_cel("londres") + ses_cel("ny") +
                f'<td><span class="badge {bclass}">{ver}</span></td>'
                f'</tr>\n')

    def fila_vacia(c):
        return (f'<tr>'
                f'<td class="grey">{c["estr"]}</td>'
                f'<td class="grey">{c["coin"]}</td>'
                f'<td class="grey">{c["tf"]}</td>'
                f'<td class="grey">0</td>'
                f'<td class="n">{c["abiertas"]}</td>'
                f'<td colspan="5" class="grey">—</td>'
                f'<td><span class="badge tag-data">📊 recopilando datos</span></td>'
                f'</tr>\n')

    rows = "".join(fila(c) for c in with_data)
    rows += "".join(fila_vacia(c) for c in sin_data)
    return f"<table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table>"


def tabla_exits(competidores, estr_agg, estr_exits):
    """Tabla de qué política de salida conviene a cada estrategia."""
    filas_data = []
    for estr, pnls in estr_agg.items():
        n = len(pnls)
        if n < 5:
            continue
        exs = estr_exits.get(estr, {})
        stats = {}
        for pol in POLITICAS:
            _, _, ep = _stat(exs.get(pol, []))
            stats[pol] = ep or -99
        best_pol = max(stats, key=lambda p: stats[p])
        filas_data.append((estr, n, stats, best_pol))
    filas_data.sort(key=lambda x: -(x[2].get("fixed") or -99))

    heads = "".join(f"<th>{h}</th>" for h in
                    ["Estrategia", "N"] + [POL_LABEL[p] for p in POLITICAS] + ["Mejor salida"])
    rows = []
    for estr, n, stats, best in filas_data:
        cells = [f'<td style="font-weight:600">{estr}</td>', f'<td class="n">{n}</td>']
        for pol in POLITICAS:
            ep = stats.get(pol)
            et = f"{ep:+.2f}R" if ep is not None and ep > -90 else "—"
            pc = "pos" if (ep or -99) > 0.02 else ("neg" if (ep or -99) < -0.02 else "neu")
            cls = "pol-best" if pol == best else pc
            cells.append(f'<td class="{cls}">{et}</td>')
        cells.append(f'<td class="coins">{POL_LABEL[best]}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"<table><thead><tr>{heads}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def generar_html():
    competidores, estr_agg = cargar()
    ult_mtime = max((c["mtime"] for c in competidores), default=0)
    hace = int((time.time() - ult_mtime) / 60)
    total_cerr = sum(c["cerradas"] for c in competidores)
    total_ab = sum(c["abiertas"] for c in competidores)
    n_estrs = len(estr_agg)

    estr_exits = defaultdict(lambda: defaultdict(list))
    for c in competidores:
        for pol, vals in c["exits"].items():
            estr_exits[c["estr"]][pol].extend(vals)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arena Board — Trading Jaime Merino</title>
<style>{css()}</style>
</head>
<body>
<h1>⚡ Arena Board — Paper Trading</h1>
<p class="sub">
  {n_estrs} estrategias · {total_cerr} ops cerradas · {total_ab} abiertas · actualizado hace {hace} min
  &nbsp;|&nbsp; <em>Solo lectura — sin dinero real</em>
</p>

<h2>🏆 Ranking por Estrategia (todas las monedas y temporalidades sumadas)</h2>
{tabla_resumen(competidores, estr_agg)}

<h2>📋 Detalle por Competidor (con desglose por sesión)</h2>
{tabla_detalle(competidores)}

<h2>🚪 Comparativa de Políticas de Salida (qué salida funciona mejor por estrategia)</h2>
<p style="color:#64748b;font-size:0.78rem;margin-bottom:10px">
  2R fijo = salida al objetivo · BE0.5R = mover stop a entrada cuando llega al 50% del objetivo ·
  BE1R = break-even cuando llega al objetivo · 1.25R = objetivo más pequeño · Trail = stop trailing
</p>
{tabla_exits(competidores, estr_agg, estr_exits)}

<p style="color:#1e293b;font-size:0.7rem;margin-top:32px">
  Generado por board_web.py · Costes incluidos (COSTE=0.0008 = 0.08% ida+vuelta)
</p>
</body>
</html>"""
    out = REG / "board.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    out = generar_html()
    print(f"Board generado: {out}")
    print("Abre ese archivo en tu navegador para ver las tablas.")


if __name__ == "__main__":
    main()
