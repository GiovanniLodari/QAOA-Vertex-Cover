"""
utils/display.py
================
Funzioni di visualizzazione condivise: palette, tabelle Rich, grafici matplotlib.

Tutto ciò che riguarda "come mostrare" i risultati è qui.
Il notebook chiama queste funzioni senza contenere codice di plotting diretto.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import networkx as nx

from rich.console import Console
from rich.table   import Table
from rich.text    import Text
from rich         import box

from .result import R
from .graph import agg, valid


console = Console()


# ════════════════════════════════════════════════════════════════════════════
# Palette colori
# ════════════════════════════════════════════════════════════════════════════

STYLE: dict[str, dict] = {
    "branch_and_bound":    {"c": "#2ca02c", "ls": "-",  "m": "s", "lbl": "Branch & Bound"},
    "greedy":              {"c": "#1f77b4", "ls": "--", "m": "o", "lbl": "Greedy"},
    "simulated_annealing": {"c": "#ff7f0e", "ls": "-.", "m": "^", "lbl": "Sim. Annealing"},
    #"haskell_bt":          {"c": "#8c564b", "ls": "-",  "m": "P", "lbl": "Haskell BT"},
    #"prolog_clp":          {"c": "#9467bd", "ls": ":",  "m": "D", "lbl": "Prolog CLP(B)"},
    "qaoa_p1":             {"c": "#d62728", "ls": "--", "m": "v", "lbl": "QAOA p=1"},
    "qaoa_p2":             {"c": "#e377c2", "ls": "--", "m": "v", "lbl": "QAOA p=2"},
    "qaoa_p3":             {"c": "#bcbd22", "ls": "--", "m": "v", "lbl": "QAOA p=3"},
    "qaoa_p4":             {"c": "#9467bd", "ls": "--", "m": "v", "lbl": "QAOA p=4"},
    "qaoa_p5":             {"c": "#8c564b", "ls": "--", "m": "v", "lbl": "QAOA p=5"},
    "qaoa_best":           {"c": "#d62728", "ls": "-",  "m": "v", "lbl": "QAOA (best p)"},
    "ibm_hw":              {"c": "#17becf", "ls": "-",  "m": "*", "lbl": "IBM Quantum HW"},
}

COLORS_P = {1: "#d62728", 2: "#e377c2", 3: "#bcbd22", 4: "#9467bd", 5: "#8c564b"}


# ════════════════════════════════════════════════════════════════════════════
# Formattazione Rich
# ════════════════════════════════════════════════════════════════════════════

def fmt_ratio(v: float) -> Text:
    """Colora il ratio: verde=ottimo, giallo=buono, rosso=lontano."""
    if v <= 1.01:
        style = "bold green"
    elif v < 1.05:
        style = "green"
    elif v < 1.15:
        style = "yellow"
    else:
        style = "red"
    return Text(f"{v:.4f}", style=style)


def fmt_delta(delta: float) -> Text:
    """Colora il Δ ratio (IBM−ideale): rosso=peggio, verde=uguale/meglio."""
    if delta > 0.05:
        style = "bold red"
    elif delta > 0.02:
        style = "red"
    elif delta > 0.0:
        style = "yellow"
    else:
        style = "green"
    sign = "+" if delta >= 0 else ""
    return Text(f"{sign}{delta:.4f}", style=style)


# ════════════════════════════════════════════════════════════════════════════
# Tabelle Rich
# ════════════════════════════════════════════════════════════════════════════

PARADIGM: dict[str, str] = {
    "branch_and_bound":    "Imperativo",
    "greedy":              "Imperativo",
    "simulated_annealing": "Imperativo",
    "haskell_bt":          "Funzionale",
    "prolog_clp":          "Logico",
    "qaoa_p1":             "Quantistico",
    "qaoa_p2":             "Quantistico",
    "qaoa_p3":             "Quantistico",
    "qaoa_p4":             "Quantistico",
    "qaoa_p5":             "Quantistico",
    "ibm_hw":              "Quantistico",
}

ORDER_CLASSICAL = [
    "branch_and_bound", "greedy", "simulated_annealing",
    #"haskell_bt", "prolog_clp",
]
ORDER_QAOA = ["qaoa_p1", "qaoa_p2", "qaoa_p3", "qaoa_p4", "qaoa_p5"]


def print_summary_table(
    results:     list[R],
    title:       str | None = None,
    show_ibm:    bool = False,
) -> None:
    """
    Tabella riassuntiva con avg/std/max ratio e tempo medio per solver.
    """
    order = ORDER_CLASSICAL + ORDER_QAOA
    if show_ibm:
        order += ["ibm_hw"]

    if title is None:
        has_qaoa = any(r.solver in ORDER_QAOA for r in results)
        title = "Confronto completo: Algoritmi Classici vs QAOA" if has_qaoa else "Confronto parziale dei Solver Classici"

    t = Table(title=title, box=box.DOUBLE_EDGE,
              header_style="bold white on dark_blue")
    for col, kw in [
        ("Solver",    {"min_width": 20, "style": "bold"}),
        #("Paradigma", {"min_width": 12}),
        ("Avg Ratio", {"justify": "right", "min_width": 10}),
        ("Std Ratio", {"justify": "right", "min_width": 10}),
        ("Max Ratio", {"justify": "right", "min_width": 10}),
        ("Avg t (s)", {"justify": "right", "min_width": 10}),
        ("n",         {"justify": "right", "min_width":  6}),
    ]:
        t.add_column(col, **kw)

    for s in order:
        rs  = [r.ratio for r in results if r.solver == s and r.ratio > 0]
        ts_ = [r.t     for r in results if r.solver == s and r.t     > 0]
        if not rs:
            continue
        avg_r = np.mean(rs); std_r = np.std(rs); max_r = np.max(rs)
        avg_t = np.mean(ts_) if ts_ else float("nan")

        t.add_row(
            STYLE.get(s, {}).get("lbl", s),
            #PARADIGM.get(s, "—"),
            fmt_ratio(avg_r),
            f"{std_r:.4f}",
            f"{max_r:.4f}",
            f"{avg_t:.4f}",
            str(len(rs)),
        )

    console.print(t)


def print_detailed_comparison_table(
    results:     list[R],
    sizes:       list[int],
    solvers:     list[str] | None = None,
) -> None:
    """
    Tabella comparativa dettagliata divisa per dimensione N.
    Mostra N, Solver, Avg Ratio, Std Ratio, Max Ratio, Avg t (s), e il numero di grafi.
    Ideale per l'analisi di QAOA (best p) contro i solver classici.
    """
    if solvers is None:
        solvers = ORDER_CLASSICAL + ["qaoa_best"]
        
    t = Table(title="Confronto Dettagliato per N: Solver Classici vs QAOA (best p)", box=box.DOUBLE_EDGE,
              header_style="bold white on dark_green")
    
    for col, kw in [
        ("N",         {"justify": "right", "style": "bold cyan"}),
        ("Solver",    {"min_width": 20, "style": "bold"}),
        ("Avg Ratio", {"justify": "right", "min_width": 10}),
        ("Std Ratio", {"justify": "right", "min_width": 10}),
        ("Max Ratio", {"justify": "right", "min_width": 10}),
        ("Avg t (s)", {"justify": "right", "min_width": 10}),
        ("n_grafi",   {"justify": "right", "min_width":  6}),
    ]:
        t.add_column(col, **kw)
        
    for n_val in sizes:
        first_for_n = True
        for s in solvers:
            rs  = [r.ratio for r in results if r.solver == s and r.n == n_val and r.ratio > 0]
            ts_ = [r.t     for r in results if r.solver == s and r.n == n_val and r.t     > 0]
            
            if not rs:
                continue
                
            avg_r = np.mean(rs); std_r = np.std(rs); max_r = np.max(rs)
            avg_t = np.mean(ts_) if ts_ else float("nan")
            
            n_display = str(n_val) if first_for_n else ""
            
            t.add_row(
                n_display,
                STYLE.get(s, {}).get("lbl", s),
                fmt_ratio(avg_r),
                f"{std_r:.4f}",
                f"{max_r:.4f}",
                f"{avg_t:.6f}",
                str(len(rs)),
            )
            first_for_n = False
        if not first_for_n:
            t.add_section()
            
    console.print(t)


def print_aer_comparison_table(
    qaoa_results: list[R],
    aer_results:  list[dict],
    qaoa_sizes:   list[int],
    p_list:       list[int],
) -> None:
    """
    Tabella: PennyLane ideale | Qiskit ideale | Qiskit HW-noise | Δ(Ideal-PL) | Δ(HW-PL) | Δ(HW-Ideal).
    """
    t = Table(
        title="PennyLane ideale vs Qiskit ideale vs Qiskit HW-noise",
        box=box.ROUNDED, header_style="bold white on dark_red",
    )
    for col, kw in [
        ("N",            {"justify": "right", "min_width":  4}),
        ("p",            {"justify": "right", "min_width":  4}),
        ("OPT",          {"justify": "right", "min_width":  5}),
        ("PL ideale",    {"justify": "right", "min_width": 11}),
        ("Qiskit ideal", {"justify": "right", "min_width": 13}),
        ("Qiskit HW",    {"justify": "right", "min_width": 11}),
        ("Δ (Ideal−PL)", {"justify": "right", "min_width": 12}),
        ("Δ (HW−PL)",    {"justify": "right", "min_width": 11}),
        ("Δ (HW−Ideal)", {"justify": "right", "min_width": 12}),
    ]:
        t.add_column(col, **kw)

    for n_val in qaoa_sizes:
        for p_val in p_list:
            pl_vals = [r.ratio for r in qaoa_results
                       if r.solver == f"qaoa_p{p_val}" and r.n == n_val and r.ratio > 0]
            qi_vals = [r["ratio_ideal"] for r in aer_results
                       if r["n"] == n_val and r["p"] == p_val and r["ratio_ideal"] > 0]
            qh_vals = [r["ratio_hw"]    for r in aer_results
                       if r["n"] == n_val and r["p"] == p_val and r["ratio_hw"]    > 0]
            if not pl_vals:
                continue

            opt_val = next((r["opt"] for r in aer_results
                            if r["n"] == n_val and r["p"] == p_val), "—")
            pl_m = np.mean(pl_vals)
            qi_m = np.mean(qi_vals) if qi_vals else float("nan")
            qh_m = np.mean(qh_vals) if qh_vals else float("nan")
            
            delta_ideal_pl = qi_m - pl_m
            delta_hw_pl    = qh_m - pl_m
            delta_hw_ideal = qh_m - qi_m

            t.add_row(
                str(n_val), str(p_val), str(opt_val),
                fmt_ratio(pl_m),
                fmt_ratio(qi_m) if not np.isnan(qi_m) else Text("n/d", "dim"),
                fmt_ratio(qh_m) if not np.isnan(qh_m) else Text("n/d", "dim"),
                fmt_delta(delta_ideal_pl) if not np.isnan(delta_ideal_pl) else Text("—", "dim"),
                fmt_delta(delta_hw_pl) if not np.isnan(delta_hw_pl) else Text("—", "dim"),
                fmt_delta(delta_hw_ideal) if not np.isnan(delta_hw_ideal) else Text("—", "dim"),
            )

    console.print(t)


def print_ibm_comparison_table(
    qaoa_results: list[R],
    aer_results:  list[dict],
    ibm_results:  list[dict],
    qaoa_sizes:   list[int],
    p_list:       list[int],
    iid:          int,
) -> None:
    """
    Tabella estesa: PL ideale | Aer ideale | Aer HW | IBM reale | Δ(IBM−PL) | Δ(IBM−Aer HW) | Δ(IBM−Aer Id).

    ibm_results: lista di dict con chiavi n, iid, p, ratio (e opzionalmente 'ibm': IBMResult).
    Supporta sia il formato piatto {n, iid, p, ratio, ...} che il formato annidato {ibm: obj}.
    """
    t = Table(
        title="Confronto completo — PL ideale vs Aer vs IBM Quantum reale",
        box=box.ROUNDED, header_style="bold white on navy_blue",
    )
    for col, kw in [
        ("N",           {"justify": "right", "min_width":  4}),
        ("p",           {"justify": "right", "min_width":  4}),
        ("PL ideale",   {"justify": "right", "min_width": 10}),
        ("Aer id.",     {"justify": "right", "min_width": 10}),
        ("Aer HW",      {"justify": "right", "min_width":  9}),
        ("IBM reale",   {"justify": "right", "min_width": 10}),
        ("Δ IBM−PL",    {"justify": "right", "min_width": 10}),
        ("Δ IBM−AerHW", {"justify": "right", "min_width": 12}),
        ("Δ IBM−AerId", {"justify": "right", "min_width": 12}),
    ]:
        t.add_column(col, **kw)

    def _ibm_ratio(r: dict) -> float:
        """Estrae il ratio da un dict IBM (formato piatto o annidato)."""
        if "ibm" in r and hasattr(r["ibm"], "ratio"):
            return r["ibm"].ratio
        return r.get("ratio", -1.0)

    for n_val in qaoa_sizes:
        for p_val in p_list:
            pl_vals = [r.ratio for r in qaoa_results
                       if r.solver == f"qaoa_p{p_val}" and r.n == n_val and r.ratio > 0 and (iid is None or r.iid == iid)]
            qi_vals = [r["ratio_ideal"] for r in aer_results
                       if r["n"] == n_val and r["p"] == p_val and r["ratio_ideal"] > 0 and (iid is None or r["iid"] == iid)]
            qh_vals = [r["ratio_hw"]    for r in aer_results
                       if r["n"] == n_val and r["p"] == p_val and r["ratio_hw"]    > 0 and (iid is None or r["iid"] == iid)]

            ibm_vals = [
                _ibm_ratio(r) for r in ibm_results
                if r["n"] == n_val and r["p"] == p_val and _ibm_ratio(r) > 0
            ]

            if not pl_vals or not ibm_vals:
                continue

            pl_m  = np.mean(pl_vals)
            qi_m  = np.mean(qi_vals)  if qi_vals  else float("nan")
            qh_m  = np.mean(qh_vals)  if qh_vals  else float("nan")
            ibm_m = np.mean(ibm_vals)
            
            delta_ibm_pl = ibm_m - pl_m
            delta_ibm_hw = ibm_m - qh_m if not np.isnan(qh_m) else float("nan")
            delta_ibm_id = ibm_m - qi_m if not np.isnan(qi_m) else float("nan")

            t.add_row(
                str(n_val), str(p_val),
                fmt_ratio(pl_m),
                fmt_ratio(qi_m)  if not np.isnan(qi_m)  else Text("n/d", "dim"),
                fmt_ratio(qh_m)  if not np.isnan(qh_m)  else Text("n/d", "dim"),
                fmt_ratio(ibm_m),
                fmt_delta(delta_ibm_pl),
                fmt_delta(delta_ibm_hw) if not np.isnan(delta_ibm_hw) else Text("—", "dim"),
                fmt_delta(delta_ibm_id) if not np.isnan(delta_ibm_id) else Text("—", "dim"),
            )

    console.print(t)


# ════════════════════════════════════════════════════════════════════════════
# Grafici matplotlib
# ════════════════════════════════════════════════════════════════════════════

def plot_mvc_examples(G: nx.Graph | None = None) -> None:
    """Mostra 3 configurazioni (cover non valida + 2 MVC) su un grafo di esempio."""
    if G is None:
        G = nx.Graph()
        G.add_edges_from([(0,1),(0,2),(1,3),(2,3),(3,4),(4,5),(2,5)])
    pos = nx.spring_layout(G, seed=7)

    configs = [
        ({1, 2, 3}, "Cover NON valida  |S|=3\n(arco (4,5) scoperto)"),
        ({0, 3, 5}, "Minimum Vertex Cover  |S|=3\n(soluzione #1)"),
        ({1, 2, 4}, "Minimum Vertex Cover  |S|=3\n(soluzione #2)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8))
    for ax, (cover, title) in zip(axes, configs):
        nc = ["#e74c3c" if n in cover else "#95a5a6" for n in G.nodes()]
        ec = ["#2ecc71" if u in cover or v in cover else "#e74c3c"
              for u, v in G.edges()]
        nx.draw_networkx(G, pos, ax=ax, node_color=nc, edge_color=ec,
                         node_size=600, font_color="white",
                         font_weight="bold", width=2.5)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    plt.suptitle("Esempio di cover non valida e due cover valide",
                 fontsize=10, y=1.02)
    plt.tight_layout()
    plt.show()


def plot_qubo_matrix(Q: np.ndarray, title: str = "Matrice QUBO $Q$") -> None:
    """Visualizza la matrice QUBO come heatmap con annotazioni."""
    n = Q.shape[0]
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    im = ax.imshow(Q, cmap="RdBu_r", vmin=-2.5, vmax=2.5)
    plt.colorbar(im, ax=ax)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{Q[i,j]:.1f}", ha="center", va="center", fontsize=12)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([f"$x_{{{i}}}$" for i in range(n)], fontsize=11)
    ax.set_yticklabels([f"$x_{{{i}}}$" for i in range(n)], fontsize=11)
    ax.set_title(title, fontsize=12)
    plt.tight_layout()
    plt.show()


def plot_ratio_vs_n(
    results:     list[R],
    order:       list[str]  | None = None,
    qaoa_sizes:  list[int]  | None = None,
    title_cl:    str = "Solver classici",
    title_qa:    str = "QAOA vs classici",
) -> None:
    """
    Due subplot affiancati: (1) solo classici, (2) QAOA + greedy + SA.
    Se nei risultati non c'è alcun algoritmo QAOA, mostra un solo plot.
    """
    ag = agg(results)
    if order is None:
        order = ORDER_CLASSICAL + ORDER_QAOA

    # Controlliamo se ci sono risultati per algoritmi QAOA
    has_qaoa = any(s in ORDER_QAOA for s in ag)
    
    n_cols = 2 if has_qaoa else 1
    fig, axes = plt.subplots(1, n_cols, figsize=(7 * n_cols, 5))
    
    if n_cols == 1:
        axes_list = [axes]
        solvers_list = [ORDER_CLASSICAL]
        titles_list = [title_cl]
    else:
        axes_list = axes
        solvers_list = [ORDER_CLASSICAL, ORDER_QAOA + ["greedy", "simulated_annealing"]]
        titles_list = [title_cl, title_qa]

    for ax, solvers, title in zip(axes_list, solvers_list, titles_list):
        for s in solvers:
            if s not in ag:
                continue
            ns = sorted(ag[s])
            m  = [ag[s][n][0] for n in ns]
            sd = [ag[s][n][1] for n in ns]
            st = STYLE[s]
            ax.plot(ns, m, label=st["lbl"], color=st["c"],
                    ls=st["ls"], marker=st["m"], lw=2, ms=7)
            ax.fill_between(ns,
                            [a - b for a, b in zip(m, sd)],
                            [a + b for a, b in zip(m, sd)],
                            color=st["c"], alpha=0.12)

        ax.axhline(1.0, color="#2ca02c", ls="-", lw=1.5, label="OPT")
        ax.set_xlabel("N")
        ax.set_ylabel("Approximation ratio")
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0.95)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    plt.show()

def plot_ratio_vs_edge_p(
    results:     list[R],
    n_inst:      int = 10,
    edge_p_list: list[float] = [0.25, 0.5, 0.75],
    order:       list[str] | None = None,
    title:       str = "Approximation ratio vs Densità"
) -> None:
    """
    Plot dell'approximation ratio in funzione della densità del grafo (edge_p).
    Disegna un singolo grafico con tutte le curve fornite in `results`.
    """
    if order is None:
        order = ORDER_CLASSICAL + ORDER_QAOA
    
    from collections import defaultdict
    map_p = defaultdict(lambda: defaultdict(list))
    
    for r in results:
        if r.ratio > 0:
            idx = r.iid // n_inst
            p = edge_p_list[idx] if idx < len(edge_p_list) else 0.5
            map_p[r.solver][p].append(r.ratio)
            
    fig, ax = plt.subplots(figsize=(8, 5))

    for s in order:
        if s not in map_p:
            continue
            
        ps = sorted(map_p[s].keys())
        m = [np.mean(map_p[s][p]) for p in ps]
        sd = [np.std(map_p[s][p]) for p in ps]
        st = STYLE.get(s, {"c": "black", "ls": "-", "m": "o", "lbl": s})
        
        ax.plot(ps, m, label=st["lbl"], color=st["c"],
                ls=st["ls"], marker=st["m"], lw=2, ms=7)
        ax.fill_between(ps,
                        [a - b for a, b in zip(m, sd)],
                        [a + b for a, b in zip(m, sd)],
                        color=st["c"], alpha=0.12)

    ax.axhline(1.0, color="#2ca02c", ls="-", lw=1.5, label="OPT")
    ax.set_xlabel("Probabilità arco $p_{edge}$")
    ax.set_ylabel("Approximation ratio")
    ax.set_title(title)
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(edge_p_list)
    
    plt.tight_layout()
    plt.show()

# def plot_ratio_vs_edge_p(
#     results:     list[R],
#     n_inst:      int = 10,
#     edge_p_list: list[float] = [0.25, 0.5, 0.75],
#     order:       list[str] | None = None,
#     title_cl:    str = "Solver classici vs Densità",
#     title_qa:    str = "QAOA vs classici vs Densità"
# ) -> None:
#     """
#     Plot dell'approximation ratio in funzione della densità del grafo (edge_p).
#     Si assume che le istanze siano state generate in blocchi di `n_inst` per ciascun valore di `edge_p`.
#     """
#     if order is None:
#         order = ORDER_CLASSICAL + ORDER_QAOA
    
#     # Raggruppiamo i risultati per solver e poi per edge_p
#     # map_p[solver][edge_p] = [ratio1, ratio2, ...]
#     from collections import defaultdict
#     map_p = defaultdict(lambda: defaultdict(list))
    
#     for r in results:
#         if r.ratio > 0:
#             idx = r.iid // n_inst
#             p = edge_p_list[idx] if idx < len(edge_p_list) else 0.5
#             map_p[r.solver][p].append(r.ratio)
            
#     has_qaoa = any(s in ORDER_QAOA for s in map_p)
#     n_cols = 2 if has_qaoa else 1
#     fig, axes = plt.subplots(1, n_cols, figsize=(7 * n_cols, 5))
    
#     if n_cols == 1:
#         axes_list = [axes]
#         solvers_list = [ORDER_CLASSICAL]
#         titles_list = [title_cl]
#     else:
#         axes_list = axes
#         solvers_list = [ORDER_CLASSICAL, ORDER_QAOA + ["greedy", "simulated_annealing"]]
#         titles_list = [title_cl, title_qa]

#     for ax, solvers, title in zip(axes_list, solvers_list, titles_list):
#         for s in solvers:
#             if s not in map_p:
#                 continue
            
#             ps = sorted(map_p[s].keys())
#             m = [np.mean(map_p[s][p]) for p in ps]
#             sd = [np.std(map_p[s][p]) for p in ps]
#             st = STYLE.get(s, {"c": "black", "ls": "-", "m": "o", "lbl": s})
            
#             ax.plot(ps, m, label=st["lbl"], color=st["c"],
#                     ls=st["ls"], marker=st["m"], lw=2, ms=7)
#             ax.fill_between(ps,
#                             [a - b for a, b in zip(m, sd)],
#                             [a + b for a, b in zip(m, sd)],
#                             color=st["c"], alpha=0.12)

#         ax.axhline(1.0, color="#2ca02c", ls="-", lw=1.5, label="OPT")
#         ax.set_xlabel("Probabilità arco $p_{edge}$")
#         ax.set_ylabel("Approximation ratio")
#         ax.set_title(title)
#         ax.legend(fontsize=8)
#         ax.grid(True, alpha=0.3)
#         ax.set_ylim(bottom=0.95)
#         ax.set_xticks(edge_p_list)

#     plt.tight_layout()
#     plt.show()


def plot_qaoa_vs_p(results: list[R], sizes: list[int] = [6, 8, 10], title: str = "Efficacia di QAOA in funzione della profondità") -> None:
    """
    Plot specifico per QAOA: mostra come varia l'approximation ratio al crescere 
    della profondità p del circuito, per diverse dimensioni N.
    """
    import re
    # Estrarre risultati solo QAOA
    qaoa_results = [r for r in results if r.solver.startswith("qaoa_p") and r.ratio > 0]
    if not qaoa_results:
        print("Nessun risultato QAOA trovato da plottare.")
        return
        
    # Raggruppare per (N, p)
    from collections import defaultdict
    data = defaultdict(lambda: defaultdict(list))
    
    for r in qaoa_results:
        match = re.search(r"qaoa_p(\d+)", r.solver)
        if match:
            p_val = int(match.group(1))
            data[r.n][p_val].append(r.ratio)
            
    fig, ax = plt.subplots(figsize=(7, 5))
    
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    markers = ["o", "s", "^", "D", "v"]
    
    for i, n in enumerate(sizes):
        if n not in data:
            continue
            
        p_vals = sorted(data[n].keys())
        means = [np.mean(data[n][p]) for p in p_vals]
        stds = [np.std(data[n][p]) for p in p_vals]
        
        c = colors[i % len(colors)]
        m = markers[i % len(markers)]
        
        ax.plot(p_vals, means, label=f"N={n}", color=c, marker=m, lw=2, ms=7)
        ax.fill_between(p_vals, 
                        [a - b for a, b in zip(means, stds)],
                        [a + b for a, b in zip(means, stds)],
                        color=c, alpha=0.15)
                        
    ax.axhline(1.0, color="black", ls="--", lw=1.5, label="OPT")
    ax.set_xlabel("Profondità QAOA (p)")
    ax.set_ylabel("Approximation ratio")
    ax.set_title(title)
    ax.set_xticks(sorted({p for n in data for p in data[n]}))
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def plot_time_vs_n(results: list[R]) -> None:
    """Tempi di esecuzione in scala logaritmica."""
    ag_t = agg(results, "t")
    fig, ax = plt.subplots(figsize=(9, 5))
    for s in ORDER_CLASSICAL + ORDER_QAOA:
        if s not in ag_t:
            continue
        ns = sorted(ag_t[s])
        m  = [ag_t[s][n][0] for n in ns]
        st = STYLE[s]
        ax.plot(ns, m, label=st["lbl"], color=st["c"],
                ls=st["ls"], marker=st["m"], lw=2, ms=6)
    ax.set_yscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel("Tempo medio (s) — scala log")
    ax.set_title("Tempi di esecuzione")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, which="both")
    plt.tight_layout()
    plt.show()


def plot_noise_sweep(
    sweep:       dict[int, list[dict]],
    classical_n8: list[R] = None,
    n_val:       int = 8,
) -> None:
    """
    Grafico singolo: degrado QAOA con rumore crescente.
    Il confronto con i classici è stato rimosso (spostato in sez. 5).
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    for p_val in sweep:
        probs  = [s["prob"]  for s in sweep[p_val]]
        ratios = [s["ratio"] for s in sweep[p_val]]
        ax.plot(probs, ratios,
                label=f"QAOA p={p_val}",
                color=COLORS_P[p_val], ls="--", marker="v", lw=2, ms=7)
    
    ax.axhline(1.0, color="#2ca02c", ls="-", lw=1.5, label="OPT")
    ax.set_xlabel("Probabilità errore (depolarizing)")
    ax.set_ylabel("Approximation ratio")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0.95)

    ax.set_title(f"Degrado QAOA con rumore crescente (N={n_val})")
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.show()


def plot_heatmap(
    results:    list[R],
    qaoa_sizes: list[int],
) -> None:
    """Heatmap approximation ratio (solver × N), escluso B&B."""
    all_s = [s for s in ORDER_CLASSICAL + ORDER_QAOA if s != "branch_and_bound"]
    mat   = np.full((len(all_s), len(qaoa_sizes)), np.nan)
    for i, s in enumerate(all_s):
        for j, n in enumerate(qaoa_sizes):
            vs = [r.ratio for r in results if r.solver == s and r.n == n and r.ratio > 0]
            if vs:
                mat[i, j] = np.mean(vs)

    fig, ax = plt.subplots(figsize=(7, max(4, len(all_s) * 0.7 + 1)))
    im = ax.imshow(mat, cmap="RdYlGn_r", vmin=1.0, vmax=1.3, aspect="auto")
    plt.colorbar(im, ax=ax, label="Approximation ratio")
    ax.set_xticks(range(len(qaoa_sizes)))
    ax.set_xticklabels([f"N={n}" for n in qaoa_sizes])
    ax.set_yticks(range(len(all_s)))
    ax.set_yticklabels([STYLE[s]["lbl"] for s in all_s])

    for i in range(len(all_s)):
        for j in range(len(qaoa_sizes)):
            v = mat[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                        fontsize=10, fontweight="bold",
                        color="white" if v > 1.15 else "black")

    _qi = [i for i, s in enumerate(all_s) if s in ORDER_QAOA]
    if _qi:
        ax.axhline(_qi[0] - 0.5, color="white", lw=2.5, ls="--")
    ax.set_title("Heatmap  approximation ratio  (verde = ottimo)", fontsize=12)
    plt.tight_layout()
    plt.show()


def plot_cobyla_convergence(
    energy_hists: dict[int, list[float]],
    G:            nx.Graph,
    opt:          int,
) -> None:
    """
    Curva di convergenza COBYLA per p=1,2,3 su un grafo di riferimento.

    energy_hists : {p: lista di valori ⟨H_C⟩ durante l'ottimizzazione}
    """
    fig, axes = plt.subplots(1, len(energy_hists), figsize=(13, 4), sharey=False)
    if len(energy_hists) == 1:
        axes = [axes]

    for ax, (p_val, hist) in zip(axes, sorted(energy_hists.items())):
        color = COLORS_P.get(p_val, "gray")
        ax.plot(hist, color=color, lw=1.5)
        ax.axhline(min(hist), color=color, ls="--", lw=1, alpha=0.6,
                   label=f"min={min(hist):.2f}")
        ax.set_title(f"QAOA p={p_val}   N={G.number_of_nodes()}   OPT={opt}", fontsize=11)
        ax.set_xlabel("Iterazione")
        ax.set_ylabel("⟨$H_C$⟩")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.suptitle(f"Convergenza COBYLA (N={G.number_of_nodes()})", fontsize=12, y=1.02)
    plt.tight_layout()
    plt.show()


def plot_bitstring_distribution(
    G:       nx.Graph,
    counts:  dict[tuple, int],
    opt:     int,
    title:   str               = "",
    n_top:   int               = 14,
    n_shots: int               = 2048,
    ax:      plt.Axes | None   = None,
) -> None:
    """
    Istogramma a barre dei bitstring più frequenti.
    Verde = ottimo, Blu = valida non-ottima, Rosso = non valida.

    Se ax è None crea una figura autonoma (10×4); altrimenti disegna
    sull'asse fornito — utile per subplot affiancati nel notebook.
    """
    nodes = list(G.nodes())
    top   = sorted(counts.items(), key=lambda x: -x[1])[:n_top]
    labels, freqs, cols = [], [], []

    for bs, cnt in top:
        cov = {nodes[i] for i, b in enumerate(bs) if b}
        labels.append("".join(str(b) for b in bs) + f"\n|S|={sum(bs)}")
        freqs.append(cnt / n_shots)
        if valid(G, cov) and len(cov) == opt:
            cols.append("#2ca02c")
        elif valid(G, cov):
            cols.append("#1f77b4")
        else:
            cols.append("#e74c3c")

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(10, 4))

    ax.bar(range(len(labels)), freqs, color=cols, edgecolor="white", lw=0.4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=7, rotation=45, ha="right")
    ax.set_ylabel("Frequenza")
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_title(title or "🟢 OPT   🔵 valida   🔴 non valida", fontsize=11)

    if standalone:
        plt.tight_layout()
        plt.show()


def plot_ibm_comparison(
    ideal_counts_by_p: dict[int, dict[tuple, int]],
    aer_counts_by_p:   dict[int, dict[tuple, int]],
    ibm_counts_by_p:   dict[int, dict[tuple, int]],
    G:                 nx.Graph,
    opt:               int,
    p_list:            list[int],
    n_shots:           int = 1024,
) -> None:
    """
    Griglia (len(p_list) x 3): PL/Aer ideale | Aer HW-noise | IBM reale.
    """
    fig, axes = plt.subplots(len(p_list), 3, figsize=(18, 4.5 * len(p_list)))
    
    # Se p_list ha 1 solo elemento, axes è un array 1D. Lo forziamo a 2D.
    if len(p_list) == 1:
        axes = [axes]
        
    for i, p in enumerate(p_list):
        datasets = [
            (ideal_counts_by_p.get(p, {}), f"Simulatore ideale (p={p})"),
            (aer_counts_by_p.get(p, {}),   f"Qiskit Aer HW-noise (p={p})"),
            (ibm_counts_by_p.get(p, {}),   f"IBM Quantum Reale (p={p})"),
        ]
        for j, (counts, title) in enumerate(datasets):
            ax = axes[i][j]
            if not counts:
                ax.axis("off")
                continue
            plot_bitstring_distribution(G, counts, opt,
                                        title=title, n_top=12,
                                        n_shots=n_shots, ax=ax)

    plt.suptitle(
        f"Distribuzione bitstring (N={G.number_of_nodes()})",
        fontsize=14, y=1.02 if len(p_list) == 1 else 1.01,
    )
    plt.tight_layout()
    plt.show()


def print_p_opt_summary(
    configs: dict[str, dict[int, dict[tuple, int]]],
    G:       nx.Graph,
    opt:     int,
    p_list:  list[int],
    n_shots: int = 1024,
    sort_by_p_opt: bool = True,
) -> None:
    """
    Stampa una tabella riassuntiva (una per ogni profondità p) 
    con le probabilità di ottenere la stringa ottima (p_opt).
    
    configs: dizionario che mappa il nome della configurazione 
             al suo dizionario di conteggi (p -> counts).
             Es. {"Aer HW-noise": aer_counts, "IBM reale": ibm_counts}
    """
    from rich.columns import Columns
    
    nodes = list(G.nodes())
    
    def get_p_opt(counts: dict) -> float:
        if not counts: return 0.0
        opt_shots = 0
        for bs, cnt in counts.items():
            # Controlliamo se la stringa/tupla usa spin {-1, 1} o bit {0, 1}
            is_spin = any(int(x) == -1 for x in bs)
            
            cov = set()
            for i, b in enumerate(bs):
                v = int(b)
                if is_spin:
                    # Se sono spin (z): z=-1 significa x=1 (incluso), z=1 significa x=0 (escluso)
                    bit = 1 if v == -1 else 0
                else:
                    bit = 1 if v > 0 else 0
                
                if bit:
                    cov.add(nodes[i])
                    
            if valid(G, cov) and len(cov) == opt:
                opt_shots += cnt
        return opt_shots / n_shots

    # Troviamo prima il p_opt globale massimo per evidenziare il p ottimale
    global_max = 0.0
    best_p = None
    for p_val in p_list:
        for label, counts_by_p in configs.items():
            val = get_p_opt(counts_by_p.get(p_val, {}))
            if val > global_max:
                global_max = val
                best_p = p_val

    tables = []
    for p_val in p_list:
        rows = []
        for label, counts_by_p in configs.items():
            val = get_p_opt(counts_by_p.get(p_val, {}))
            rows.append((label, val))
            
        if sort_by_p_opt:
            rows.sort(key=lambda x: x[1], reverse=True)
            
        # Troviamo il massimo interno a questa tabella
        max_in_table = max([v for _, v in rows]) if rows else 0.0
        
        # Evidenziamo il titolo della tabella se è il p ottimale
        title_style = "bold yellow" if p_val == best_p and global_max > 0 else "white"
        
        t = Table(title=f"[{title_style}]Probabilità Ottimo (p={p_val})[/{title_style}]", box=box.SIMPLE_HEAD, min_width=35)
        t.add_column("Configurazione", style="cyan")
        t.add_column("p_opt", justify="right")
        t.add_column(f"Shot ottimi / {n_shots}", justify="right", style="dim")
        
        for label, val in rows:
            if "IBM" in label:
                color = "green"
            elif val == max_in_table and max_in_table > 0:
                color = "yellow"
            else:
                color = "white"
                
            t.add_row(
                label, 
                f"[{color}]{val:.4f}[/{color}]",
                f"[{color}]~{int(val * n_shots)}[/{color}]"
            )
        tables.append(t)
        
    # Usiamo una console con larghezza forzata per evitare che vada a capo
    from rich.console import Console
    wide_console = Console(width=300)
    wide_console.print(Columns(tables, expand=False, equal=True))


def plot_aer_vs_pl_bars(
    qaoa_results: list[R],
    aer_results:  list[dict],
    qaoa_sizes:   list[int],
    p_list:       list[int],
) -> None:
    """
    Barchart affiancato: ratio medio per p — PL ideale vs Qiskit ideale vs Qiskit HW.
    Mostra un subplot per ogni dimensione N in qaoa_sizes. 
    Include le barre di errore (deviazione standard).
    """
    n_plots = len(qaoa_sizes)
    if n_plots == 0:
        return
        
    fig, axes = plt.subplots(1, n_plots, figsize=(7 * n_plots, 5), sharey=True)
    if n_plots == 1:
        axes = [axes]

    for ax, n_val in zip(axes, qaoa_sizes):
        x     = np.arange(len(p_list))
        width = 0.25

        for offset, key, label, color in [
            (-width, "ratio_ideal", "Qiskit — ideale",   "#2ca02c"),
            (0,      "ratio_hw",    "Qiskit — HW noise", "#d62728"),
            (width,  None,          "PennyLane — ideale", "#ff7f0e"),
        ]:
            vals, stds = [], []
            for p_val in p_list:
                if key is not None:
                    vs = [r[key] for r in aer_results
                          if r["n"] == n_val and r["p"] == p_val and r[key] > 0]
                else:
                    vs = [r.ratio for r in qaoa_results
                          if r.solver == f"qaoa_p{p_val}" and r.n == n_val and r.ratio > 0]
                
                vals.append(np.mean(vs) if vs else float("nan"))
                stds.append(np.std(vs) if vs else 0.0)

            bars = ax.bar(x + offset, vals, width, label=label,
                          color=color, alpha=0.85, edgecolor="white",
                          yerr=stds, capsize=4, error_kw={'alpha': 0.5})
            
            for bar, v in zip(bars, vals):
                if not np.isnan(v):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.005,
                            f"{v:.3f}", ha="center", va="bottom", fontsize=8)

        ax.axhline(1.0, color="black", ls="--", lw=1.2, alpha=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f"p={p}" for p in p_list])
        ax.set_ylabel("Approximation ratio medio")
        ax.set_title(f"N={n_val} — confronto modelli di rumore", fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_ylim(bottom=0.95)

    plt.suptitle("PennyLane ideale vs Qiskit ideale vs Qiskit hardware-noise",
                 fontsize=12, y=1.02)
    plt.tight_layout()
    plt.show()


def plot_qaoa_depth_vs_density(
    results: list[R], 
    n_inst: int = 10,
    sizes: list[int] = [6, 8, 10], 
    edge_p_list: list[float] = [0.25, 0.5, 0.75],
    title: str = "QAOA: Impatto della Profondità (p) in base alla Densità"
) -> None:
    """
    Crea un subplot per ogni dimensione N.
    In ogni subplot l'asse X è la profondità p, e le linee rappresentano le diverse densità.
    """
    import matplotlib.ticker as ticker
    from collections import defaultdict
    
    # map_data[N][edge_p][p] = [ratio1, ratio2, ...]
    map_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for r in results:
        if r.ratio > 0 and r.solver.startswith("qaoa_p"):
            try:
                p_val = int(r.solver.split("_p")[1])
            except:
                continue
            idx = r.iid // n_inst
            ep = edge_p_list[idx] if idx < len(edge_p_list) else 0.5
            map_data[r.n][ep][p_val].append(r.ratio)

    valid_sizes = [n for n in sizes if n in map_data]
    if not valid_sizes:
        return
        
    fig, axes = plt.subplots(1, len(valid_sizes), figsize=(5 * len(valid_sizes), 5), sharey=True)
    if len(valid_sizes) == 1:
        axes = [axes]
        
    colors = {0.25: "#1f77b4", 0.5: "#ff7f0e", 0.75: "#d62728"}
    markers = {0.25: "o", 0.5: "s", 0.75: "^"}
    
    for ax, n in zip(axes, valid_sizes):
        for ep in edge_p_list:
            if ep not in map_data[n]:
                continue
                
            p_vals = sorted(map_data[n][ep].keys())
            if not p_vals:
                continue
                
            means = [np.mean(map_data[n][ep][p]) for p in p_vals]
            stds = [np.std(map_data[n][ep][p]) for p in p_vals]
            
            c = colors.get(ep, "black")
            m = markers.get(ep, "x")
            
            ax.plot(p_vals, means, label=f"Densità {ep:.2f}", color=c, marker=m, lw=2, ms=7)
            ax.fill_between(p_vals,
                            [a - b for a, b in zip(means, stds)],
                            [a + b for a, b in zip(means, stds)],
                            color=c, alpha=0.15)
                            
        ax.axhline(1.0, color="#2ca02c", ls="-", lw=1.5, label="OPT")
        ax.set_title(f"Dimensione N={n}")
        ax.set_xlabel("Profondità QAOA (p)")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, alpha=0.3)
        if ax == axes[0]:
            ax.set_ylabel("Approximation ratio")
            ax.legend(fontsize=9, loc="best")

    fig.suptitle(title, fontsize=14, y=1.02)
    plt.tight_layout()
    plt.show()

def plot_state_categories_stacked(
    stats:  dict[int, dict[str, dict[str, list[float]]]],
    p_list: list[int]
) -> None:
    """
    Genera uno Stacked Bar Chart per le probabilità medie di 
    Ottimo, Valido (Subottimo) e Non Valido.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    bar_width = 0.5
    x_pos = np.arange(len(p_list))

    configs = list(stats[p_list[0]].keys())  # es. ["Ideale", "HW"] o altri

    for idx, config in enumerate(configs[:2]):
        ax = axes[idx]
        
        avg_opt = [np.mean(stats[p][config]["opt"]) for p in p_list]
        avg_val = [np.mean(stats[p][config]["val"]) for p in p_list]
        avg_inv = [np.mean(stats[p][config]["inv"]) for p in p_list]
        
        ax.bar(x_pos, avg_opt, bar_width, label="Ottimo", color="#2ca02c", edgecolor="white")
        ax.bar(x_pos, avg_val, bar_width, bottom=avg_opt, label="Valido (Subottimo)", color="#1f77b4", edgecolor="white")
        ax.bar(x_pos, avg_inv, bar_width, bottom=np.array(avg_opt)+np.array(avg_val), label="Non Valido", color="#e74c3c", edgecolor="white")
        
        ax.set_title(f"Qiskit Aer - {config}", fontsize=13)
        ax.set_xlabel("Profondità p")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(p_list)
        ax.grid(axis='y', alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Probabilità Media")
            ax.legend()

    plt.suptitle("Distribuzione media delle categorie di stato (20 grafi N=8, densità 0.50)", fontsize=15, y=1.05)
    plt.tight_layout()
    plt.show()

def print_p_opt_average_table(
    stats:  dict[int, dict[str, dict[str, list[float]]]],
    p_list: list[int]
) -> None:
    """
    Stampa le tabelle affiancate con il p_opt medio calcolato.
    """
    from rich.columns import Columns
    
    tables = []
    configs = list(stats[p_list[0]].keys())
    
    for p_val in p_list:
        t = Table(title=f"p_opt Medio (p={p_val})", box=box.SIMPLE_HEAD, min_width=25)
        t.add_column("Configurazione", style="cyan")
        t.add_column("p_opt", justify="right")
        
        for config in configs:
            media = np.mean(stats[p_val][config]["opt"])
            color = "green" if "HW" in config else "white"
            t.add_row(f"{config}", f"[{color}]{media:.4f}[/{color}]")
            
        tables.append(t)

    from rich.console import Console
    local_console = Console(width=300)
    local_console.print(Columns(tables, expand=False, equal=True))


def print_p_opt_table_finale(stats, p_list, iid):
    """Come print_p_opt_average_table, ma per la singola istanza IBM:
       titolo senza «Medio» e hardware reale evidenziato distintamente."""
    from rich.columns import Columns
    from rich.console import Console
    tables = []
    configs = list(stats[p_list[0]].keys())
    for p_val in p_list:
        t = Table(title=f"p_opt — istanza iid={iid} (p={p_val})",
                  box=box.SIMPLE_HEAD, min_width=25)
        t.add_column("Configurazione", style="cyan")
        t.add_column("p_opt", justify="right")
        for config in configs:
            media = np.mean(stats[p_val][config]["opt"])
            if   "reale" in config: color = "bold magenta"
            elif "HW"    in config: color = "green"
            else:                   color = "white"
            t.add_row(config, f"[{color}]{media:.4f}[/{color}]")
        tables.append(t)
    Console(width=300).print(Columns(tables, expand=False, equal=True))