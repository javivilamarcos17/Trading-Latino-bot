"""
Intento de capturar la "discreción" de Merino con Machine Learning.
Como solo mira el gráfico, todo lo que él ve está en los datos. Damos al modelo su "vista"
(estado multi-temporal de indicadores) y que aprenda a predecir el movimiento.
Juez: hold-out 2026 (jamás visto). El sobreajuste es el enemigo.

Uso:  python -m trading_latino.research.ml
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

from trading_latino.backtest.engine import preparar

_COL = {"verde_claro": 2, "verde_oscuro": 1, "rojo_oscuro": -1, "rojo_claro": -2}


def _enc(arr):
    return np.array([_COL.get(x, 0) for x in arr], dtype=float)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    d = preparar("BTC")
    master = d["master"]
    al = d["al"]
    precio = d["h1"]["cierre"].to_numpy(dtype=float)

    def c(rol, n):
        return al[rol][n].to_numpy(dtype=float)

    X = pd.DataFrame({
        "dist_ema55_h4": precio / c("h4", "ema_lenta") - 1,
        "dist_poc_h4": precio / c("h4", "poc") - 1,
        "dist_vwap_h4": precio / c("h4", "vwap") - 1,
        "sqz_val_h4": c("h4", "sqz_valor"),
        "sqz_val_h1": c("h1", "sqz_valor"),
        "sqz_col_h4": _enc(al["h4"]["sqz_color"].to_numpy()),
        "sqz_col_h1": _enc(al["h1"]["sqz_color"].to_numpy()),
        "adx_h4": c("h4", "adx"),
        "adx_pend_h4": c("h4", "adx_pendiente"),
        "di_diff_h4": c("h4", "di_pos") - c("h4", "di_neg"),
        "rsi_h4": c("h4", "rsi"),
        "rsi_h1": c("h1", "rsi"),
        "volrel_h4": c("h4", "volumen_rel"),
        "emacross_h4": c("h4", "ema_rapida") / c("h4", "ema_lenta") - 1,
        "emacross_d": c("diario", "ema_rapida") / c("diario", "ema_lenta") - 1,
        "dist_ema55_d": precio / c("diario", "ema_lenta") - 1,
    }, index=master)

    H = 32  # horizonte ~32h (como su hold típico)
    p = pd.Series(precio, index=master)
    fwd = p.shift(-H) / p - 1
    y = (fwd > 0).astype(int)

    anio = master.year
    tr = anio <= 2024
    te = anio == 2025
    ho = anio == 2026
    valido = fwd.notna().to_numpy()

    Xtr, ytr = X[tr & valido], y[tr & valido]
    m = HistGradientBoostingClassifier(max_iter=300, max_depth=4, learning_rate=0.05,
                                       l2_regularization=1.0, random_state=0)
    m.fit(Xtr, ytr)

    def ev(mask, nombre):
        mk = mask & valido
        if mk.sum() == 0:
            return
        Xm, ym = X[mk], y[mk]
        pr = m.predict_proba(Xm)[:, 1]
        acc = accuracy_score(ym, (pr > 0.5).astype(int))
        auc = roc_auc_score(ym, pr)
        base = ym.mean()
        # estrategia simple: largo cuando P(sube)>0.55; retorno medio 32h (bruto)
        f = fwd[mk].to_numpy()
        sel = pr > 0.55
        ret_sel = f[sel].mean() * 100 if sel.sum() else float("nan")
        print(f"  {nombre:<14} acc {acc*100:4.1f}% (base {base*100:4.1f}%) | AUC {auc:.3f} | "
              f"señales {sel.sum():5d} | ret medio 32h cuando 'sube' {ret_sel:+.2f}%")

    print("ML prediciendo subida a 32h (juez = 2026):")
    ev(tr, "train 21-24")
    ev(te, "test 2025")
    ev(ho, "HOLD-OUT 26")


if __name__ == "__main__":
    main()
