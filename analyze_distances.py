from typing import List, Tuple
import pandas as pd
import route_loader
import route_loader

from utils import (
    get_route_dump_file,
    load_simulation_paths,
    plot_cdf,
)


def analyze_distances(algorithms, cstl, sim_name, runs_per_sim):
    ########### load data ##########
    plot_dfs: List[Tuple[str, pd.DataFrame]] = []
    for alg in algorithms:
        print("\t", f"Working on {alg}/{cstl}/{sim_name}")
        # Load all runs
        run_dfs = []
        for run in range(0, runs_per_sim):
            (stats_path, _) = load_simulation_paths(alg, cstl, sim_name, run)
            (_, file_path) = get_route_dump_file(alg, cstl, sim_name, run)

            print("\t", "Load", file_path)
            routes = route_loader.load_routes(file_path)
            distances = list(map(lambda r: r.length, routes))

            print("\t", "Load stats dataframe")
            df = pd.read_csv(stats_path)

            df["distance"] = distances
            df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
            run_dfs.append(df)
        df_overall = pd.concat(run_dfs)
        plot_dfs.append((alg, df_overall))

    ########## Plot data ##########
    file_name = f"distance-{cstl}-{sim_name}.cdf.pdf"
    plot_cdf(plot_dfs, "distance", file_name)
