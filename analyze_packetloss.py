import time
from typing import List, Tuple
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from utils import load_stats


def analyze_packetloss(algorithms, cstl, sim_name, runs_per_sim):
    ########### load data ##########
    named_dfs: List[Tuple[str, pd.DataFrame]] = []
    for alg in algorithms:
        print("\t", f"Working on {alg}/{cstl}/{sim_name}...")
        # Load all runs
        df = load_stats(alg, cstl, sim_name, runs_per_sim)
        # Concat runs
        df = pd.concat(df)
        # add to data
        named_dfs.append((alg, df))

    ########### Process data ##########
    processed_dfs: List[Tuple[str, pd.DataFrame]] = []
    for name, alg in named_dfs:
        print("\t", "Process data...")
        alg["recorded"] = (alg["recorded"] / 10_000).round() / 100

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
    file_name = f"packetloss-{cstl}-{sim_name}.sum.pdf"
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
    )
    print("\t", "Write plot to file...")
    fig.write_image(file_name, engine="kaleido")
    time.sleep(1)
    fig.write_image(file_name, engine="kaleido")
