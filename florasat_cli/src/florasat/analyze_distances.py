from typing import List, Tuple
import pandas as pd
import florasat_statistics

from florasat.utils import (
    Config,
    get_route_dump_file,
    load_simulation_paths,
    plot_cdf,
)


def analyze_distances(config: Config):
    ########### load data ##########
    plot_dfs: List[Tuple[str, pd.DataFrame]] = []
    for alg in config.algorithms:
        print("\t", f"Working on {alg}/{config.cstl}/{config.sim_name}")
        # Load all runs
        run_dfs = []
        for run in range(0, config.runs):
            (stats_path, _) = load_simulation_paths(config, alg, run)
            (_, file_path) = get_route_dump_file(config, alg, run)

            print("\t", "Load", file_path)
            routes = florasat_statistics.load_routes(str(file_path))
            distances = list(map(lambda r: r.length, routes))

            print("\t", "Load stats dataframe")
            df = pd.read_csv(stats_path)

            df["distance"] = distances
            df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
            run_dfs.append(df)
        df_overall = pd.concat(run_dfs)
        plot_dfs.append((alg, df_overall))

    ########## Plot data ##########
    file_path = config.results_path.joinpath(
        f"distance-{config.cstl}-{config.sim_name}.cdf.pdf"
    )
    plot_cdf(plot_dfs, "distance", file_path)
