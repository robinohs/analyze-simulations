from itertools import chain, repeat
import json
import time
from typing import Dict, Iterable, List, Tuple
import numpy as np
import pandas as pd
import route_loader
from multiprocessing import Pool, cpu_count
from functools import cache, lru_cache, reduce
import route_loader

from utils import (
    find_max_value,
    find_min_value,
    get_route_dump_file,
    hash_list,
    load_simulation_paths,
    load_routes,
    load_stats,
    plot_cdf,
)

###########
# distance # occurrence
# 150      # 54
# 165      # 23


########## CONFIG ##########
algorithms = [
    ("Random", "random"),
    ("DSPA", "dspr"),
    ("DDRA", "ddra")
    ]
# algorithms = [("DSPA", "dspr")]
cstl = "iridium"
sim_name = "normal"
runs_per_sim = 4
##############################

########### load data ##########


def load_data(algs, cstl, sim_name, runs_per_sim) -> List[Tuple[str, pd.DataFrame]]:
    plot_dfs: List[Tuple[str, pd.DataFrame]] = []
    for name, alg in algs:
        # Load all runs
        run_dfs = []
        for run in range(0, runs_per_sim):
            print("Working on", alg, cstl, sim_name, run)
            (stats_path, _) = load_simulation_paths(alg, cstl, sim_name, run)
            (_, file_path) = get_route_dump_file(alg, cstl, sim_name, run)

            print("\t", "Load", file_path)
            routes = route_loader.load_routes(file_path)
            distances = list(map(lambda r: r.length, routes))

            print("\t", "Load stats dataframe")
            df = pd.read_csv(stats_path)

            # print("\t", "Combine dataframe and distances")
            df["distance"] = distances
            df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
            run_dfs.append(df)
        df_overall = pd.concat(run_dfs)
        plot_dfs.append((name, df_overall))
    return plot_dfs


########## Plot data ##########

plot_dfs = load_data(algorithms, cstl, sim_name, runs_per_sim)

print("Plot data")
max_distance = find_max_value(list(map(lambda df: df[1], plot_dfs)), "distance")
file_name = f"distance-{cstl}-{sim_name}.cdf.pdf"
plot_cdf(plot_dfs, max_distance, "distance", file_name, continuous=True)
