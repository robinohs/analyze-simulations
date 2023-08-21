import os
import time
from typing import List, Tuple
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from florasat.statistics.utils import Config, load_stats, fix_loading_mathjax


def analyze_packetloss(config: Config):
    for cstl in config.cstl:
        for sim_name in config.sim_name:
            named_dfs: List[Tuple[str, pd.DataFrame]] = []
            for alg in config.algorithms:
                print("\t", f"Working on {alg}/{cstl}/{sim_name}...")
                # Load all runs
                df = load_stats(config, cstl, sim_name, alg)
                # Concat runs
                df = pd.concat(df)
                # add to data
                named_dfs.append((alg, df))

            ########### Process data ##########
            processed_dfs: List[Tuple[str, pd.DataFrame]] = []
            for name, alg in named_dfs:
                print("\t", "Process data...")
                alg["recorded"] = alg["recorded"].round(2)

                delivered = (
                    alg.loc[alg["dropReason"] == 99]
                    .groupby("recorded")["recorded"]
                    .agg("count")
                    .pipe(pd.DataFrame)
                    .rename(columns={"recorded": "sum_recvd"})
                    .cumsum()
                    .astype("Int64")
                )

                dropped = (
                    alg.loc[alg["dropReason"] != 99]
                    .groupby("recorded")["recorded"]
                    .agg("count")
                    .pipe(pd.DataFrame)
                    .rename(columns={"recorded": "sum_dropped"})
                    .cumsum()
                    .astype("Int64")
                )

                # fill <NA> with previous value or if that value is undefined 0
                combined = delivered.join(dropped)
                combined.fillna(method="ffill", inplace=True)
                combined.fillna(0, inplace=True)

                # calculate ratio
                combined["sum"] = combined["sum_recvd"] + combined["sum_dropped"]
                combined["ratio_dropped"] = combined["sum_dropped"] / combined["sum"]

                processed_dfs.append((name, combined))

            ########## Plot data ##########
            print("\t", "Create plot...")
            fig = make_subplots()
            for name, df in processed_dfs:
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        x=df.index,
                        y=df["ratio_dropped"],
                        mode="lines",
                    )
                )
            fig.update_traces(line=dict(width=2), marker=dict(size=2))
            fig.update_layout(
                legend=dict(yanchor="top", y=0.95, xanchor="left", x=0.05),
                yaxis_range=[0, 1]
            )
            fig.update_xaxes(title_text="Time (s)", nticks=10)
            fig.update_yaxes(title_text='Packetloss [%]', dtick=0.1)
            print("\t", "Write plot to file...")
            file_path = config.results_path.joinpath(cstl).joinpath(sim_name)
            os.makedirs(file_path, exist_ok=True)
            file_path = file_path.joinpath(f"packetloss.sum.pdf")
            fix_loading_mathjax()
            fig.write_image(file_path, engine="kaleido")
