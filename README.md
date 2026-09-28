# QAOA vs solver classici per il Minimum Vertex Cover

> A parità di dimensione del problema, QAOA con profondità crescente *p* riesce a competere con i migliori ottimizzatori classici in termini di *approximation ratio*? Come cambia il risultato con il rumore simulato e su hardware IBM reale?

Progetto per il corso di Quantum Computing. Tutto il lavoro è nel notebook [`quantum_mvc.ipynb`](quantum_mvc.ipynb); [`quantum_mvc.html`](quantum_mvc.html) ne è l'esportazione, leggibile senza installare nulla.

## Cosa contiene

1. **Problema e formulazione**: Minimum Vertex Cover su grafi Erdős–Rényi (N = 6, 8, 10 vertici, 20 istanze per dimensione, probabilità d'arco 0,25 / 0,5 / 0,75), tradotto in **QUBO** e poi in Hamiltoniano di Ising.
2. **Solver classici**: Branch & Bound con lower bound basato sul matching (soluzione esatta, usata come riferimento), Greedy e Simulated Annealing.
3. **QAOA** con COBYLA e profondità p = 1…5, in tre regimi:
   - simulazione ideale con PennyLane;
   - rumore depolarizzante in PennyLane;
   - Qiskit Aer con un modello di rumore derivato da un backend generico.
4. **Hardware IBM reale**: esecuzione con `SamplerV2` su una singola istanza (N = 8, p = 1 e 2), per la quota di calcolo disponibile.
5. **Confronto finale** tra classici e QAOA, scegliendo il miglior *p* per istanza, e sviluppi futuri.

## Risultati

Confronto finale (miglior *p* per istanza per QAOA, simulazione ideale):

| Solver | Ratio medio | Dev. std. | Ratio massimo | Tempo medio (s) |
|---|---|---|---|---|
| Branch & Bound | 1,0000 | 0,0000 | 1,0000 | 0,0001 |
| Greedy | 1,0194 | 0,0674 | 1,5000 | 0,0001 |
| Simulated Annealing | 1,0138 | 0,0533 | 1,3333 | 0,0625 |
| QAOA (miglior p) | 1,0000 | 0,0000 | 1,0000 | 0,3716 |

Il ratio di QAOA coincide con l'ottimo, ma va letto con cautela: il miglior *p* è scelto a posteriori conoscendo l'ottimo esatto, e il ratio conta un'istanza come risolta se una soluzione ottima compare almeno una volta nei 1024 shot. Per questo il notebook usa anche $p_\text{opt}$, la probabilità di campionare una soluzione ottima:

| Configurazione | $p_\text{opt}$ (p = 1) | $p_\text{opt}$ (p = 2) |
|---|---|---|
| Aer ideale | 0,1846 | 0,2168 |
| Aer con rumore | 0,1904 | 0,1992 |
| IBM hardware reale | 0,1689 | 0,1172 |

A p = 1 il modello di rumore di Aer riproduce bene l'hardware; a p = 2 l'hardware degrada più di quanto il modello preveda. Il confronto su hardware riguarda una sola istanza, quindi è indicativo e non conclusivo.

## Esecuzione

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook quantum_mvc.ipynb
```

- Il notebook salva i calcoli lunghi in `cache/` e `data/` (checkpoint), che non sono nel repository: alla prima esecuzione ricalcola tutto.
- La sezione su hardware reale richiede un account IBM Quantum. Copia `.env.example` in `.env` e inserisci la tua chiave in `IBM_API_KEY`. Senza chiave le altre sezioni funzionano comunque.

## Struttura

| Percorso | Contenuto |
|---|---|
| `quantum_mvc.ipynb` | Notebook con esperimenti, risultati e commenti |
| `utils/qubo.py` | Costruzione del QUBO e conversione in Ising |
| `utils/graph.py` | Generazione delle istanze, validazione e riparazione delle cover, aggregazione dei risultati |
| `utils/result.py` | Strutture dati condivise |
| `utils/display.py` | Tabelle e grafici |
