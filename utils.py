PATH = "/home/royal/omnetpp-6.0.1/samples/florasat/simulations/routing/results"

import os
import csv
import numpy as np
import pandas as pd
from typing import Iterable, List, Tuple, TypeVar
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time
import itertools
import msgspec

pd.options.plotting.backend = "plotly"


# class Hop(msgspec.Struct):
#     """Class to represent a groundstation hop"""

#     type: str
#     id: int
#     lat: float
#     lon: float
#     alt: int


# class Route(msgspec.Struct):
#     """Class for keeping track of packet routes"""

#     pid: int
#     hops: List[Hop]

Route = Tuple[int, int, List[Tuple[str, int, float, float, int]]]

K = TypeVar("K")


class hash_list(list):
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Iterable):
            args = args[0]
        super().__init__(args)

    def __hash__(self):
        return hash(e for e in self)


def pairwise(iterable: Iterable[K]) -> Iterable[Tuple[K, K]]:
    "s -> (s0, s1), (s1, s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def load_routes(path: str) -> List[Route]:
    with open(path, "rb") as f:
        content = f.read()
    print("\t", "Decode")
    routes = msgspec.msgpack.decode(content, type=List[Route])
    return routes


def load_simulation_paths(
    alg_name: str, cstl_name: str, name: str, run: int
) -> Tuple[str, str]:
    path_directory = f"{PATH}/{alg_name}/{cstl_name}/{name}"
    content_dir: List[str] = os.listdir(path_directory)

    stats_file_name = f"{run}.stats.csv"
    stats_file_path = f"{path_directory}/{stats_file_name}"

    routes_file_name = f"{run}.routes.csv"
    routes_file_path = f"{path_directory}/{routes_file_name}"

    if not stats_file_name or not routes_file_name in content_dir:
        raise FileNotFoundError(
            f"Could not find {stats_file_name} or {routes_file_name} in {path_directory}"
        )

    return (stats_file_path, routes_file_path)


def find_min_value(dfs: List[pd.DataFrame], value: str) -> int:
    assert len(dfs) > 0
    min_val = dfs.pop()[value].min()
    for df in dfs:
        df_min = df[value].min()
        if df_min < min_val:
            min_val = df_min
    return min_val


def find_max_value(dfs: List[pd.DataFrame], value: str) -> int:
    assert len(dfs) > 0
    max_val = dfs.pop()[value].max()
    for df in dfs:
        df_max = df[value].max()
        if df_max > max_val:
            max_val = df_max
    return max_val


def load_stats(alg: str, cstl: str, name: str, runs: int = 4) -> List[pd.DataFrame]:
    dfs: List[pd.DataFrame] = []
    for run in range(0, runs):
        (stats_fp, _) = load_simulation_paths(alg, cstl, name, run)
        print("Read:", stats_fp)
        dfs.append(pd.read_csv(stats_fp))
    return dfs


def plot_cdf(
    dfs: List[Tuple[str, pd.DataFrame]],
    max_val,
    col: str,
    file_name: str,
    continuous=False,
):
    fig = make_subplots()
    for name, df in dfs:
        stats_df = (
            df.groupby(col)[col]
            .agg("count")
            .pipe(pd.DataFrame)
            .rename(columns={col: "frequency"})
        )
        if not continuous:
            stats_df = stats_df.reindex(list(range(0, max_val + 1)), fill_value=0)

        stats_df["pdf"] = stats_df["frequency"] / sum(stats_df["frequency"])

        stats_df["cdf"] = stats_df["pdf"].cumsum()
        stats_df = stats_df.reset_index()

        fig.add_trace(
            go.Scatter(
                name=name,
                x=stats_df[col].values,
                y=stats_df["cdf"],
                mode="markers+lines",
            )
        )
    fig.update_traces(line=dict(width=2), marker=dict(size=2))
    fig.update_layout(
        legend=dict(yanchor="bottom", y=0.05, xanchor="right", x=0.95),
    )
    print("Write to file")
    fig.write_image(file_name, engine="kaleido")
    # time.sleep(1)
    # print("Write2")
    # fig.write_image(file_name, engine="kaleido")


def get_route_dump_file(
    alg: str, cstl: str, sim_name: str, run: int
) -> Tuple[str, str]:
    path = f"routes/{alg}/{cstl}/{sim_name}"
    file_path = f"{path}/{run}.routes.msgpack"
    return (path, file_path)
