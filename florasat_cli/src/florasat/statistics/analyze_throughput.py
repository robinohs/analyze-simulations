from math import ceil, floor
import os
from typing import List, Tuple
import numpy as np
import pandas as pd
from florasat_statistics import load_sat_stats
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from florasat.statistics.utils import (
    Config,
    apply_default,
    load_stats,
)


def analyze_throughput(config: Config):
    for cstl in config.cstl:
        for sim_name in config.sim_name:
            plot_dfs: List[Tuple[str, pd.DataFrame]] = []
            # old_max = 0
            # traffics: List[pd.DataFrame] = []
            for alg in config.algorithms:
                print("\t", f"Working on {alg}/{cstl}/{sim_name}")
                # Load all runs
                df = load_stats(config, cstl, sim_name, alg)
                # Concat runs
                df = pd.concat(df)

                df["created"] = df["created"].round(1)
                df["recorded"] = df["recorded"].round(1)

                df = df.loc[(df["type"] == "N") & (df["dropReason"] == 99)]

                df = (
                    df.groupby(["recorded", "size"])["recorded"]
                    .count()
                    .pipe(pd.DataFrame)
                    .rename(columns={"recorded": "count"})
                    .reset_index()
                )

                print(df)
                df["count"] = df["count"] / config.runs
                print(df)
                df["datarate"] = df["size"] * df["count"] * 10 / 1024 / 1024
                print(df)

                # df_t = df[["created", "size"]]

                # df_t = (
                #     df_t.groupby(["created", "size"])["created"]
                #     .count()
                #     .pipe(pd.DataFrame)
                #     .rename(columns={"created": "count"})
                #     .reset_index()
                # )

                # old_max = max(old_max, floor(df_t["created"].max()))

                # print(df_t)

                # traffics.append(traffic)

                # print(old_max)
                plot_dfs.append((alg, df))

            # fill with prev numbers
            ## find max
            max_val = 0
            for alg, df in plot_dfs:
                max_val = max(max_val, df["recorded"].max())

            processed_dfs: List[Tuple[str, pd.DataFrame]] = []
            for alg, df in plot_dfs:
                float_list = []
                for i in range(0, ceil(max_val)):
                    for x in range(0, 10):
                        float_list.append(round(i + round(x / 10, 1), 1))

                df = df.set_index("recorded").reindex(float_list, fill_value=0).reset_index()

                df["datarate"] = df["datarate"].round(2)

                df = (
                    df.groupby(pd.cut(df["recorded"], 250, right=True))["datarate"]
                    .mean()
                    .reset_index()
                )
                # print(df.tail(20))

                entries = []
                for index, row in df.iterrows():
                    start = max(0.0, row.recorded.left + 0.001)
                    end = row.recorded.right
                    # middle = start + (end - start) / 2
                    datarate = row.datarate

                    entries.append([start, datarate])
                    entries.append([end, datarate])
                    # entries.append([middle, datarate])

                df = pd.DataFrame(entries, columns=["recorded", "datarate"])

                # df = df.reindex(indicies, fill_value=np.NaN).fillna(method="ffill")
                processed_dfs.append((alg, df))

            ########## Plot data ##########
            print("\t", "Create plot...")
            fig = make_subplots()
            for name, df in processed_dfs:
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        x=df["recorded"],
                        y=df["datarate"],
                    ),
                )
            fig.update_traces(line=dict(width=1), marker=dict(size=3))
            fig.update_layout(
                legend=dict(yanchor="top", y=0.95, xanchor="left", x=0.05),
            )
            # fig.update_layout(barmode='stack')
            fig.update_xaxes(
                title_text="Time (s)",
                nticks=10,
                showgrid=True,
                ticks="outside",
                tickangle=35,
            )
            fig.update_yaxes(
                title_text="Throughput (MB/s)",
                nticks=10,
            )
            print("\t", "Write plot to file...")
            file_path = config.results_path.joinpath(cstl).joinpath(sim_name)
            os.makedirs(file_path, exist_ok=True)
            file_path = file_path.joinpath(f"throughput.comparison.pdf")
            apply_default(fig, size=18)
            fig.write_image(file_path, engine="kaleido")
