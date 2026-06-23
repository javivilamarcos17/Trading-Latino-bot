"""
BOARD WEB de la ARENA — genera board.html listo para abrir en el navegador.
Diseño simplificado: tabla clara, un vistazo para decidir qué funciona y qué no.

Uso:  python -m trading_latino.live.board_web
      (genera data_store/paper_arena/board.html — abrir en navegador)
"""
from __future__ import annotations
import json
import time
from collections import defaultdict
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "data_store" / "paper_arena"
MIN_N = 12    # mínimo para dar veredicto firme

POLITICAS = ("fixed", "be05", "be10", "t125", "trail")
POL_LABEL  = {"fixed": "2R fijo", "be05": "BE 0.5R", "be10": "BE 1R", "t125": "1.25R", "trail": "Trail"}


def _stat(vals):
    if not vals: return 0, None, None
    n = len(vals)
    return n, sum(1 for v in vals if v > 0) / n, sum(vals) / n


def cargar():
    """Devuelve lista de dicts con info por estrategia (agrupando todas las monedas/TFs)."""
    estr_data = defaultdict(lambda: {
        "pnls": [], "exits": defaultdict(list),
        "por_tf": defaultdict(list), "por_coin": defaultdict(list),
        "sesiones": defaultdict(list), "abiertas": 0,
    })
    mtime_max = 0
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
        ab   = [o for o in ops if o.get("status") == "abierta"]
        d = estr_data[estr]
        d["abiertas"] += len(ab)
        for o in cerr:
            v = o["exits"]["fixed"]
            d["pnls"].append(v)
            d["por_tf"][tf].append(v)
            d["por_coin"][coin].append(v)
            d["sesiones"][o.get("sesion", "?")].append(v)
            for pol in POLITICAS:
                if pol in o.get("exits", {}):
                    d["exits"][pol].append(o["exits"][pol])
        mtime_max = max(mtime_max, f.stat().st_mtime)
    return estr_data, mtime_max


def mejor_exit(exits):
    """Qué política de salida tiene mayor expectativa."""
    best, best_v = "fixed", -99
    for pol in POLITICAS:
        vals = exits.get(pol, [])
        if len(vals) < 5: continue
        v = sum(vals) / len(vals)
        if v > best_v:
            best_v = v; best = pol
    return best, best_v


def mejor_tf(por_tf):
    """TF con mayor expectativa (mín 3 ops)."""
    best_tf, best_v = "—", -99
    for tf, vals in sorted(por_tf.items()):
        if len(vals) < 3: continue
        v = sum(vals) / len(vals)
        if v > best_v:
            best_v = v; best_tf = tf
    return best_tf, best_v


def veredicto(exp, n):
    if n < 5:  return ("🔍 sin datos", "#334155")
    if n < MIN_N: return ("🔍 acumulando", "#334155")
    if exp > 0.25:  return ("✅ GANADORA",  "#14532d")
    if exp > 0.05:  return ("🟢 prometedora", "#052e16")
    if exp >= -0.05: return ("🟡 neutral",  "#422006")
    if exp >= -0.20: return ("🟠 débil",    "#431407")
    return ("❌ descartar",  "#450a0a")


def generar_html():
    estr_data, mtime_max = cargar()
    hace = int((time.time() - mtime_max) / 60)
    total_ops = sum(len(d["pnls"]) for d in estr_data.values())
    total_ab  = sum(d["abiertas"] for d in estr_data.values())

    # Ordenar estrategias por expectativa (mayor a menor), luego sin datos al final
    rows_data = []
    for estr, d in estr_data.items():
        n, win, exp = _stat(d["pnls"])
        rows_data.append((estr, d, n, win, exp))
    rows_data.sort(key=lambda x: (x[2] >= 5, x[4] if x[4] is not None else -99), reverse=True)

    # Clasificar en 3 buckets
    ganadoras    = [(e, d, n, w, ex) for e, d, n, w, ex in rows_data if n >= MIN_N and (ex or 0) > 0.05]
    acumulando   = [(e, d, n, w, ex) for e, d, n, w, ex in rows_data if n < MIN_N]
    descartables = [(e, d, n, w, ex) for e, d, n, w, ex in rows_data if n >= MIN_N and (ex or 0) <= 0.05]

    def badge(text, bg="#334155", fg="#e2e8f0"):
        return f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:99px;font-size:0.75rem;font-weight:700;white-space:nowrap">{text}</span>'

    def pill_exp(exp, n):
        if exp is None or n < 5:
            c = "#64748b"
        elif exp > 0.10: c = "#22c55e"
        elif exp > 0: c = "#86efac"
        elif exp > -0.10: c = "#fbbf24"
        else: c = "#ef4444"
        t = f"{exp:+.2f}R" if exp is not None else "—"
        return f'<span style="color:{c};font-weight:700">{t}</span>'

    def pill_win(win, n):
        if win is None or n < 5: return '<span style="color:#64748b">—</span>'
        c = "#22c55e" if win > 0.55 else ("#ef4444" if win < 0.40 else "#fbbf24")
        return f'<span style="color:{c};font-weight:600">{win*100:.0f}%</span>'

    def fila_tabla(estr, d, n, win, exp):
        ver_txt, ver_bg = veredicto(exp, n)
        mejor_t, mejor_tv = mejor_tf(d["por_tf"])
        be_pol, be_val = mejor_exit(d["exits"])
        sal_txt = POL_LABEL.get(be_pol, be_pol) if n >= 5 else "—"
        # coins activos
        coins_txt = " / ".join(sorted(d["por_coin"].keys()))
        # sesion ganadora (si tiene datos)
        ses_best = ""; ses_best_v = -99
        for ses, sv in d["sesiones"].items():
            if ses == "?" or len(sv) < 3: continue
            ev = sum(sv) / len(sv)
            if ev > ses_best_v: ses_best = ses; ses_best_v = ev
        ses_col = f'<span style="color:#7dd3fc">{ses_best}</span>' if ses_best else "—"
        return (f'<tr>'
                f'<td style="font-weight:700;color:#f8fafc">{estr}</td>'
                f'<td style="color:#94a3b8">{coins_txt}</td>'
                f'<td style="color:#64748b">{n}</td>'
                f'<td>{pill_win(win, n)}</td>'
                f'<td>{pill_exp(exp, n)}</td>'
                f'<td style="color:#94a3b8">{mejor_t}</td>'
                f'<td style="color:#64748b;font-size:0.78rem">{sal_txt}</td>'
                f'<td>{ses_col}</td>'
                f'<td>{badge(ver_txt, ver_bg)}</td>'
                f'</tr>\n')

    def seccion(titulo, filas, color):
        if not filas: return ""
        tabla_rows = "".join(fila_tabla(*f) for f in filas)
        cabecera = (f'<div style="background:{color};padding:8px 14px;border-radius:8px 8px 0 0;'
                    f'font-weight:700;color:#f8fafc;margin-top:24px">{titulo}</div>')
        cols = "<tr>" + "".join(f"<th>{h}</th>" for h in
               ["Estrategia", "Monedas", "N ops", "Win %", "Retorno (R)", "Mejor TF", "Mejor salida", "Sesión top", "Estado"]) + "</tr>"
        return (cabecera +
                f'<table><thead>{cols}</thead><tbody>{tabla_rows}</tbody></table>')

    resumen_banner = (
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px">'
        f'<div style="background:#1e293b;padding:12px 20px;border-radius:10px">'
        f'<div style="font-size:1.5rem;font-weight:800;color:#22c55e">{len(ganadoras)}</div>'
        f'<div style="font-size:0.8rem;color:#64748b">estrategias funcionando</div></div>'
        f'<div style="background:#1e293b;padding:12px 20px;border-radius:10px">'
        f'<div style="font-size:1.5rem;font-weight:800;color:#fbbf24">{len(acumulando)}</div>'
        f'<div style="font-size:0.8rem;color:#64748b">acumulando datos</div></div>'
        f'<div style="background:#1e293b;padding:12px 20px;border-radius:10px">'
        f'<div style="font-size:1.5rem;font-weight:800;color:#ef4444">{len(descartables)}</div>'
        f'<div style="font-size:0.8rem;color:#64748b">débiles / descartar</div></div>'
        f'<div style="background:#1e293b;padding:12px 20px;border-radius:10px">'
        f'<div style="font-size:1.5rem;font-weight:800;color:#e2e8f0">{total_ops}</div>'
        f'<div style="font-size:0.8rem;color:#64748b">ops cerradas totales</div></div>'
        f'<div style="background:#1e293b;padding:12px 20px;border-radius:10px">'
        f'<div style="font-size:1.5rem;font-weight:800;color:#7dd3fc">{total_ab}</div>'
        f'<div style="font-size:0.8rem;color:#64748b">ops abiertas ahora</div></div>'
        f'</div>'
    )

    # Sección de exits por estrategia (solo ganadoras, compacta)
    def exits_compacto():
        if not ganadoras: return ""
        rows = []
        for estr, d, n, win, exp in ganadoras:
            if n < 5: continue
            celdas = [f'<td style="font-weight:700;color:#22c55e">{estr}</td>', f'<td style="color:#64748b">{n}</td>']
            best_pol, best_val = "—", -99
            for pol in POLITICAS:
                vals = d["exits"].get(pol, [])
                if not vals: celdas.append('<td style="color:#334155">—</td>'); continue
                _, _, ev = _stat(vals)
                c = "#22c55e" if (ev or 0) > 0.05 else ("#ef4444" if (ev or 0) < -0.02 else "#fbbf24")
                is_best = (ev or 0) > (best_val or -99)
                bg = "background:#1a3a1a;" if is_best else ""
                celdas.append(f'<td style="{bg}color:{c}">{ev:+.2f}R</td>')
                if (ev or -99) > best_val: best_val = ev or 0; best_pol = POL_LABEL[pol]
            celdas.append(f'<td style="color:#7dd3fc;font-size:0.78rem">{best_pol}</td>')
            rows.append("<tr>" + "".join(celdas) + "</tr>")
        if not rows: return ""
        cols = "<tr>" + "".join(f"<th>{h}</th>" for h in
               ["Estrategia", "N"] + list(POL_LABEL.values()) + ["Mejor"]) + "</tr>"
        return (f'<div style="background:#14532d;padding:8px 14px;border-radius:8px 8px 0 0;'
                f'font-weight:700;color:#f8fafc;margin-top:24px">🚪 Política de salida óptima (solo las que funcionan)</div>'
                f'<table><thead>{cols}</thead><tbody>{"".join(rows)}</tbody></table>'
                f'<p style="color:#64748b;font-size:0.75rem;margin:6px 0 0">Fondo verde = mejor opción para esa estrategia</p>')

    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: #0a0a0f; color: #e2e8f0; padding: 24px; }
h1 { font-size: 1.5rem; color: #f8fafc; margin-bottom: 3px; }
.sub { font-size: 0.8rem; color: #475569; margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; font-size: 0.83rem; margin-bottom: 4px; }
th { background: #0f172a; color: #64748b; padding: 8px 12px; text-align: left; font-weight: 600;
     position: sticky; top: 0; z-index: 10; white-space: nowrap; border-bottom: 1px solid #1e293b; }
td { padding: 8px 12px; border-bottom: 1px solid #111827; }
tr:hover td { background: #111827; }
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arena — Trading Jaime Merino</title>
<style>{css}</style>
</head>
<body>
<h1>⚡ Arena · Paper Trading</h1>
<p class="sub">Actualizado hace {hace} min · Datos reales en vivo (Hyperliquid) · Sin dinero real · Costes incluidos (0.08% ida+vuelta)</p>
{resumen_banner}
{seccion("✅ Estrategias funcionando (n≥12, exp>0.05R)", ganadoras, "#14532d")}
{seccion("🔍 Acumulando datos (n&lt;12 — esperar antes de juzgar)", acumulando, "#1e3a5f")}
{seccion("❌ Débiles o descartar (n≥12, exp≤0.05R)", descartables, "#450a0a")}
{exits_compacto()}
<p style="color:#1e293b;font-size:0.7rem;margin-top:28px">
  board_web.py · Regenerar: python -m trading_latino.live.board_web
</p>
</body>
</html>"""

    out = REG / "board.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    out = generar_html()
    print(f"Board generado: {out}")


if __name__ == "__main__":
    main()
