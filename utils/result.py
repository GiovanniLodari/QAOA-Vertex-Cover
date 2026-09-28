"""
utils/result.py
==============
Strutture dati condivise da tutti i moduli del progetto.
"""

from dataclasses import dataclass


@dataclass
class R:
    """Risultato di un singolo run su una singola istanza."""
    solver: str   # es. "branch_and_bound", "qaoa_p1", …
    n:      int   # numero di nodi del grafo
    iid:    int   # instance id (0..N_INST-1)
    sz:     int   # dimensione della cover trovata
    opt:    int   # ottimo noto (da B&B); -1 se non disponibile
    ratio:  float # sz/opt  (approximation ratio); -1 se opt non noto
    t:      float # tempo di esecuzione in secondi
    ok:     bool  # la cover è valida?

    # ── helper ──────────────────────────────────────────────────────────────
    def is_optimal(self) -> bool:
        return self.ok and self.opt > 0 and self.sz == self.opt

    def __repr__(self) -> str:
        star = "★" if self.is_optimal() else " "
        return (
            f"R({star}{self.solver}, n={self.n}, iid={self.iid}, "
            f"sz={self.sz}, opt={self.opt}, ratio={self.ratio:.4f}, "
            f"t={self.t:.4f}s, ok={self.ok})"
        )


def load_cache(filepath: str, current_config: dict):
    """
    Carica i dati dalla cache se il file esiste e la configurazione corrisponde.
    Restituisce i dati cachati, oppure None se la cache è assente o obsoleta.
    """
    import os, pickle
    if os.path.exists(filepath):
        try:
            with open(filepath, "rb") as f:
                cached = pickle.load(f)
            if isinstance(cached, tuple) and cached[-1] == current_config:
                if len(cached) == 2:
                    return cached[0]
                return cached[:-1]
        except Exception:
            pass
    return None


def save_cache(filepath: str, current_config: dict, *data) -> None:
    """
    Salva i dati e la configurazione nel file di cache.
    Puoi passare dinamicamente uno o N dati da salvare.
    Esempio: save_cache("file.pkl", CONFIG, risultato1, risultato2)
    """
    import os, pickle
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        pickle.dump((*data, current_config), f)
