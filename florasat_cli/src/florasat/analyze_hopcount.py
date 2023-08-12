from typing import List, Tuple
import pandas as pd

from florasat.utils import (
    Config,
    load_stats,
    plot_cdf,
)


def analyze_hopcounts(config: Config):
    ########### load data ##########
    named_dfs: List[Tuple[str, pd.DataFrame]] = []
    for alg in config.algorithms:
        print("\t", f"Working on {alg}/{config.cstl}/{config.sim_name}")
        # Load all runs
        df = load_stats(config, alg)
        # Concat runs
        df = pd.concat(df)
        # Filter for delivered and Normal packets
        df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
        # add to data
        named_dfs.append((alg, df))

    ########## Plot data ##########
    file_path = config.results_path.joinpath(
        f"hopcount-{config.cstl}-{config.sim_name}.cdf.pdf"
    )
    plot_cdf(named_dfs, "hops", file_path)
