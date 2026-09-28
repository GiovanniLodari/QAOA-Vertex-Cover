"""
utils/qubo.py
=============
Hamiltoniano QUBO per Minimum Vertex Cover
------------------------------------------
Variabile binaria x_v ∈ {0,1} per ogni vertice v.

    H(x) = A · Σ_{(u,v)∈E} (1 − x_u)(1 − x_v)   [penalità archi scoperti]
          + B · Σ_v x_v                             [dimensione della cover]

con A >> B (tipicamente A=2, B=1).

Mappatura spin–bit per QAOA
----------------------------
Lo spin Ising z_v ∈ {-1, +1} è legato alla variabile binaria da:
    x_v = (1 − z_v) / 2   →   z_v = 1 − 2·x_v

Sostituendo, l'Hamiltoniano diventa:
    H_C = Σ_{i<j} J_{ij} Z_i Z_j + Σ_i h_i Z_i  + costante
"""

from __future__ import annotations

import numpy as np
import networkx as nx


def build_qubo(G: nx.Graph, A: float = 2.0, B: float = 1.0) -> np.ndarray:
    """
    Costruisce la matrice QUBO Q per Minimum Vertex Cover su G.

    Parametri
    ---------
    G : grafo non orientato
    A : peso della penalità per archi scoperti  (deve essere > B)
    B : peso del termine di dimensione cover

    Restituisce
    -----------
    Q : matrice (n×n) tale che H(x) = x^T Q x
        (le variabili x sono indicizzate nell'ordine di G.nodes())
    """
    nodes = list(G.nodes())
    idx   = {v: i for i, v in enumerate(nodes)}
    n     = len(nodes)
    Q     = np.zeros((n, n))

    # Termine lineare: B · x_v  →  diagonale
    for v in nodes:
        Q[idx[v], idx[v]] += B

    # Termine di penalità: A·(1−x_u)(1−x_v) = A − A·x_u − A·x_v + A·x_u·x_v
    # Il termine costante +A è ignorato (non influisce sull'ottimizzazione).
    # I termini lineari −A·x_u e −A·x_v vanno sulla diagonale.
    # Il termine bilineare A·x_u·x_v va sulle off-diagonali (simmetrizzato).
    for u, v in G.edges():
        i, j = idx[u], idx[v]
        Q[i, i] -= A
        Q[j, j] -= A
        Q[i, j] += A / 2
        Q[j, i] += A / 2

    return Q


def qubo_to_ising(
    Q: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Converte la matrice QUBO in coefficienti Ising tramite x_v = (1−z_v)/2.

    Restituisce
    -----------
    J      : matrice (n×n) dei coefficienti ZZ  (solo triangolo superiore non nullo)
    h      : vettore (n,) dei coefficienti Z
    offset : costante energetica (da tenere per ricostruire il valore assoluto)

    L'Hamiltoniano Ising è:
        H_C = Σ_{i<j} J[i,j] · Z_i Z_j  +  Σ_i h[i] · Z_i  +  offset
    """
    n    = Q.shape[0]
    Qs   = (Q + Q.T) / 2          # simmetrizza per sicurezza
    J    = np.zeros((n, n))
    h    = np.zeros(n)
    offset = 0.0

    for i in range(n):
        for j in range(n):
            if i == j:
                h[i]    -= Qs[i, i] / 2
                offset  += Qs[i, i] / 2
            elif i < j:
                J[i, j] += Qs[i, j] / 2
                h[i]    -= Qs[i, j] / 2
                h[j]    -= Qs[i, j] / 2
                offset  += Qs[i, j] / 2

    return J, h, offset


def qubo_energy(Q: np.ndarray, x: np.ndarray) -> float:
    """Calcola H(x) = x^T Q x per una soluzione binaria x."""
    return float(x @ Q @ x)


def ising_energy(
    J: np.ndarray,
    h: np.ndarray,
    offset: float,
    z: np.ndarray,
) -> float:
    """Calcola H_C per una configurazione di spin z ∈ {-1,+1}^n."""
    n = len(z)
    e = offset + float(h @ z)
    for i in range(n):
        for j in range(i + 1, n):
            e += J[i, j] * z[i] * z[j]
    return e
