from typing import List, Tuple
import pandas as pd

from utils import (
    load_stats,
    plot_cdf,
)


def analyze_hopcounts(algorithms, cstl, sim_name, runs_per_sim):
    ########### load data ##########
    named_dfs: List[Tuple[str, pd.DataFrame]] = []
    for alg in algorithms:
        print("\t", f"Working on {alg}/{cstl}/{sim_name}")
        # Load all runs
        df = load_stats(alg, cstl, sim_name, runs_per_sim)
        # Concat runs
        df = pd.concat(df)
        # Filter for delivered and Normal packets
        df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
        # add to data
        named_dfs.append((alg, df))

    ########## Plot data ##########
    file_name = f"hopcount-{cstl}-{sim_name}.cdf.pdf"
    plot_cdf(named_dfs, "hops", file_name)
