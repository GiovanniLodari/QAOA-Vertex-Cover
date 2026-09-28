# QAOA vs classical solvers for Minimum Vertex Cover

> At equal problem size, can QAOA with increasing depth *p* compete with the best classical optimizers in terms of *approximation ratio*? How does the result change with simulated noise and on real IBM hardware?

University project for the Quantum Computing course. All the work is in the notebook [`quantum_mvc.ipynb`](quantum_mvc.ipynb); [`quantum_mvc.html`](quantum_mvc.html) is its export, readable without installing anything. The notebook text is in Italian.

## What it contains

1. **Problem and formulation**: Minimum Vertex Cover on Erdős–Rényi graphs (N = 6, 8, 10 vertices, 20 instances per size, edge probability 0.25 / 0.5 / 0.75), translated into a **QUBO** and then into an Ising Hamiltonian.
2. **Classical solvers**: Branch & Bound with a matching-based lower bound (exact solution, used as the reference), Greedy and Simulated Annealing.
3. **QAOA** with COBYLA and depth p = 1…5, in three regimes:
   - ideal simulation with PennyLane;
   - depolarizing noise in PennyLane;
   - Qiskit Aer with a noise model derived from a generic backend.
4. **Real IBM hardware**: run with `SamplerV2` on a single instance (N = 8, p = 1 and 2), limited by the available compute quota.
5. **Final comparison** of classical solvers and QAOA, picking the best *p* per instance, and future work.

## Results

Final comparison (best *p* per instance for QAOA, ideal simulation):

| Solver | Mean ratio | Std. dev. | Max ratio | Mean time (s) |
|---|---|---|---|---|
| Branch & Bound | 1.0000 | 0.0000 | 1.0000 | 0.0001 |
| Greedy | 1.0194 | 0.0674 | 1.5000 | 0.0001 |
| Simulated Annealing | 1.0138 | 0.0533 | 1.3333 | 0.0625 |
| QAOA (best p) | 1.0000 | 0.0000 | 1.0000 | 0.3716 |

QAOA's ratio matches the optimum, but it should be read with care: the best *p* is chosen after the fact knowing the exact optimum, and an instance counts as solved if an optimal solution appears at least once in the 1024 shots. That is why the notebook also uses $p_\text{opt}$, the probability of sampling an optimal solution:

| Configuration | $p_\text{opt}$ (p = 1) | $p_\text{opt}$ (p = 2) |
|---|---|---|
| Aer ideal | 0.1846 | 0.2168 |
| Aer with noise | 0.1904 | 0.1992 |
| Real IBM hardware | 0.1689 | 0.1172 |

At p = 1 the Aer noise model reproduces the hardware well; at p = 2 the hardware degrades more than the model predicts. The hardware comparison covers a single instance, so it is indicative, not conclusive.

## Running it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook quantum_mvc.ipynb
```

- The notebook saves long computations in `cache/` and `data/` (checkpoints), which are not in the repository: the first run recomputes everything.
- The real-hardware section needs an IBM Quantum account. Copy `.env.example` to `.env` and put your key in `IBM_API_KEY`. Without a key the other sections still work.

## Structure

| Path | Content |
|---|---|
| `quantum_mvc.ipynb` | Notebook with experiments, results and commentary |
| `utils/qubo.py` | QUBO construction and Ising conversion |
| `utils/graph.py` | Instance generation, cover validation and repair, result aggregation |
| `utils/result.py` | Shared data structures |
| `utils/display.py` | Tables and plots |
