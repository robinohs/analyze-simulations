import os
from typing import List, Tuple
import pandas as pd
from florasat_statistics import load_sat_stats
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from florasat.statistics.utils import (
    Config,
    fix_loading_mathjax,
    get_sats_dump_file,
    load_simulation_paths,
    plot_cdf,
)


def analyze_queues(config: Config):
    for cstl in config.cstl:
        for sim_name in config.sim_name:
            plot_dfs: List[Tuple[str, pd.DataFrame]] = []
            for alg in config.algorithms:
                print("\t", f"Working on {alg}/{cstl}/{sim_name}")
                # Load all runs
                run_dfs = []
                for run in range(0, config.runs):
                    (stats_path, _, _) = load_simulation_paths(
                        config, cstl, sim_name, alg, run
                    )
                    (_, file_path) = get_sats_dump_file(
                        config, cstl, sim_name, alg, run
                    )

                    print("\t", "Load", file_path)
                    satellites = load_sat_stats(str(file_path))

                    df = pd.DataFrame(columns=["id", "timestamp", "queueSize"])

                    for sat in satellites:
                        id = sat.sat_id
                        entries = [[id, entry.to, entry.qs] for entry in sat.entries]

                        df = pd.concat(
                            [pd.DataFrame(entries, columns=df.columns), df],
                            ignore_index=True,
                        )

                    print(df.head())

                    df = (
                        df.groupby(["id", "timestamp"])["queueSize"]
                        .mean()
                        .pipe(pd.DataFrame)
                    )

                    print(df.head())

                    df = (
                        df.groupby(["timestamp"])["queueSize"]
                        .sum()
                        .pipe(pd.DataFrame)
                    )

                    print(df.head())
                    run_dfs.append(df)

                df_overall = pd.concat(run_dfs)
                plot_dfs.append((alg, df_overall))

            ########## Plot data ##########
            print("\t", "Create plot...")
            fig = make_subplots()
            for name, df in plot_dfs:
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        x=df.index,
                        y=df["queueSize"],
                        mode="lines+markers",
                    )
                )
            fig.update_traces(line=dict(width=1), marker=dict(size=3))
            fig.update_layout(
                legend=dict(yanchor="top", y=0.95, xanchor="left", x=0.05),
            )
            fig.update_xaxes(title_text="Time (s)", nticks=10)
            fig.update_yaxes(title_text="Simultaneously queued packets", nticks=10)
            print("\t", "Write plot to file...")
            file_path = config.results_path.joinpath(cstl).joinpath(sim_name)
            os.makedirs(file_path, exist_ok=True)
            file_path = file_path.joinpath(f"queues.histogram.pdf")
            fix_loading_mathjax()
            fig.write_image(file_path, engine="kaleido")
