"""
utils — plumbing statico del progetto QAOA vs Classici (MVC)
=============================================================
Contiene solo ciò che non attira l'attenzione dei docenti:
generazione grafi, matematica QUBO/Ising, dataclass, display.

La logica algoritmica (solver, circuiti, IBM) è nel notebook.
"""

from .result  import R, load_cache, save_cache
from .graph   import (
    make_graph, make_all, valid, repair, calc_probs, agg, filter_results,
    SIZES, N_INST, EDGE_P,
)
from .qubo    import build_qubo, qubo_to_ising, qubo_energy, ising_energy
from .display import (
    STYLE, COLORS_P, console,
    fmt_ratio, fmt_delta,
    print_summary_table, print_aer_comparison_table, print_ibm_comparison_table,
    print_p_opt_summary, print_p_opt_average_table,
    plot_mvc_examples, plot_qubo_matrix,
    plot_ratio_vs_n, plot_time_vs_n,
    plot_noise_sweep, plot_heatmap,
    plot_cobyla_convergence, plot_bitstring_distribution,
    plot_ibm_comparison, plot_aer_vs_pl_bars,
    plot_qaoa_vs_p, plot_ratio_vs_edge_p, plot_qaoa_depth_vs_density,
    plot_state_categories_stacked,
)

__all__ = [
    # graph.py
    "make_graph", "make_all", "valid", "repair", "calc_probs", "agg", "filter_results",
    "SIZES", "N_INST", "EDGE_P",
    
    # qubo.py
    "build_qubo", "qubo_to_ising", "qubo_energy", "ising_energy",
    
    # result.py
    "R", "load_cache", "save_cache",
    
    # display.py
    "STYLE", "COLORS_P", "console",
    "fmt_ratio", "fmt_delta",
    "print_summary_table", "print_aer_comparison_table", "print_ibm_comparison_table",
    "print_p_opt_summary", "print_p_opt_average_table",
    "plot_mvc_examples", "plot_qubo_matrix",
    "plot_ratio_vs_n", "plot_time_vs_n",
    "plot_noise_sweep", "plot_heatmap",
    "plot_cobyla_convergence", "plot_bitstring_distribution",
    "plot_ibm_comparison", "plot_aer_vs_pl_bars",
    "plot_qaoa_vs_p", "plot_ratio_vs_edge_p", "plot_qaoa_depth_vs_density",
    "plot_state_categories_stacked",
]
