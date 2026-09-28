"""
utils/graph.py
==============
Generazione istanze, validazione cover, repair e aggregazione risultati.
"""

from __future__ import annotations

import numpy as np
import networkx as nx
from collections import defaultdict
from typing import Sequence

from .result import R


# ── Parametri di default per la generazione delle istanze ───────────────────
SIZES:  list[int] = [6, 8, 10, 12, 15, 20]
N_INST: int       = 10
EDGE_P: float | Sequence[float] = 0.5


# ── Generazione ──────────────────────────────────────────────────────────────

def make_graph(n: int, i: int, edge_p: float = EDGE_P) -> nx.Graph:
    """Grafo Erdős–Rényi con seed deterministico."""
    G = nx.erdos_renyi_graph(n=n, p=edge_p, seed=1000 + n * 100 + i)
    G.graph["instance_id"] = i
    return G


def make_all(
    sizes:  Sequence[int] = SIZES,
    n_inst: int           = N_INST,
    edge_p: float | Sequence[float] = EDGE_P,
) -> dict[int, list[nx.Graph]]:
    """Genera tutte le istanze come dizionario {n: [G₀, G₁, …]}.
    Se edge_p è una lista, genera n_inst grafi per ciascuna probabilità.
    """
    if isinstance(edge_p, (int, float)):
        edge_p_list = [float(edge_p)]
    else:
        edge_p_list = edge_p
        
    out = {}
    for n in sizes:
        graphs = []
        iid = 0
        for p in edge_p_list:
            for _ in range(n_inst):
                G = make_graph(n, iid, p)
                G.graph["p_edge"] = p
                graphs.append(G)
                iid += 1
        out[n] = graphs
    return out


# ── Validazione e riparazione ────────────────────────────────────────────────

def valid(G: nx.Graph, cov: set) -> bool:
    """Restituisce True se *cov* è una vertex cover valida per G."""
    return all(u in cov or v in cov for u, v in G.edges())


def repair(G: nx.Graph, cov: set) -> set:
    """
    Aggiunge vertici alla cover finché non copre tutti gli archi.
    Strategia greedy: ad ogni passo rimuovi il nodo di grado massimo
    nel sottografo degli archi scoperti.
    """
    cov = set(cov)
    H   = G.copy()
    # Rimuovi gli archi già coperti
    for u, v in G.edges():
        if u in cov or v in cov:
            H.remove_edge(u, v)
    while H.number_of_edges():
        nd = max(H.nodes(), key=H.degree)
        cov.add(nd)
        H.remove_node(nd)
    return cov


def calc_probs(G: nx.Graph, nodes: list, opt: int, counts: dict) -> tuple[float, float, float]:
    """
    Calcola le frazioni di probabilità: p_opt, p_valido_subottimo, p_invalido.
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0, 0.0, 0.0
    
    p_opt = p_val_sub = p_inv = 0.0
    for bs, cnt in counts.items():
        cover = {nodes[i] for i, b in enumerate(bs) if b}
        is_valid = valid(G, cover) # Controlla se è un vertex cover valido
        prob = cnt / total
        
        if is_valid:
            if sum(bs) == opt:
                p_opt += prob      # Cover Ottimo
            else:
                p_val_sub += prob  # Cover Valido ma subottimo
        else:
            p_inv += prob          # Non valido
            
    return p_opt, p_val_sub, p_inv


# ── Aggregazione risultati ───────────────────────────────────────────────────

def agg(
    results: list[R],
    metric:  str = "ratio",
) -> dict[str, dict[int, tuple[float, float]]]:
    """
    Aggrega i risultati per solver e dimensione n.

    Restituisce:
        { solver_name: { n: (mean, std) } }

    I risultati con metrica ≤ 0 sono esclusi (marcatori di errore).
    """
    d: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        v = getattr(r, metric)
        if v > 0:
            d[r.solver][r.n].append(v)
    return {
        s: {n: (float(np.mean(vs)), float(np.std(vs))) for n, vs in nd.items()}
        for s, nd in d.items()
    }


def filter_results(
    results: list[R],
    *,
    solvers: list[str] | None = None,
    sizes:   list[int] | None = None,
    max_iid: int | None       = None,
) -> list[R]:
    """Filtra la lista di risultati per solver, dimensioni e istanze."""
    out = results
    if solvers is not None:
        out = [r for r in out if r.solver in solvers]
    if sizes is not None:
        out = [r for r in out if r.n in sizes]
    if max_iid is not None:
        out = [r for r in out if r.iid < max_iid]
    return out
