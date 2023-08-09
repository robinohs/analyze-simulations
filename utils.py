PATH = "/home/royal/omnetpp-6.0.1/samples/florasat/simulations/routing/results"

import os
import csv
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time

pd.options.plotting.backend = "plotly"


@dataclass
class GroundStation:
    """Class to represent a groundstation hop"""

    id: int
    lat: float
    lon: float


@dataclass
class SatelliteHop:
    """Class to represent a satellite hop"""

    id: int
    lat: float
    lon: float


@dataclass
class Route:
    """Class for keeping track of packet routes"""

    pid: int
    hops: List[GroundStation | SatelliteHop]


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


def plot_cdf(dfs: List[Tuple[str, pd.DataFrame]], max_val, col: str, file_name: str):
    fig = make_subplots()
    for name, df in dfs:
        stats_df = (
            df.groupby(col)[col]
            .agg("count")
            .pipe(pd.DataFrame)
            .rename(columns={col: "frequency"})
        )
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
    fig.update_traces(line=dict(width=2.5), marker=dict(size=5))
    fig.update_layout(
        legend=dict(yanchor="bottom", y=0.05, xanchor="right", x=0.95),
    )
    fig.write_image(file_name, engine="kaleido")
    time.sleep(1)
    fig.write_image(file_name, engine="kaleido")


def load_routes(routes_path: str) -> Dict[int, Route]:
    def parse_row(row: List[str]) -> Tuple[int, str, int, float, float]:
        pid = int(row[0])
        type = row[1]
        id = int(row[2])
        lat = float(row[3])
        lon = float(row[4])
        return (pid, type, id, lat, lon)

    route_dict = dict()

    with open(routes_path) as routes_file:
        reader = csv.reader(routes_file)
        current_id = None
        route: List[GroundStation | SatelliteHop] = []
        for num, row in enumerate(reader):
            if num == 0:
                continue
            (pid, type, id, lat, lon) = parse_row(row)
            if current_id is None:
                current_id = pid
            elif current_id != pid:
                # finish up creation
                assert len(route) >= 1  # at least 1 hop
                route_dict[current_id] = Route(current_id, route)
                current_id = pid
                route.clear()
            # add hop
            if type == "S":
                hop = SatelliteHop(id, lat, lon)
            else:
                hop = GroundStation(id, lat, lon)
            route.append(hop)
    return route_dict
