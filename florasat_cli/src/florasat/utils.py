from dataclasses import dataclass
import os
from pathlib import Path
import pandas as pd
from typing import List, Tuple
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time

pd.options.plotting.backend = "plotly"


@dataclass
class Config:
    algorithms: List[str]
    cstl: str
    sim_name: str
    runs: int
    florasat_results_path: Path
    routes_path: Path
    results_path: Path


def load_simulation_paths(config: Config, alg: str, run: int) -> Tuple[Path, Path]:
    path_directory = (
        config.florasat_results_path.joinpath(alg)
        .joinpath(config.cstl)
        .joinpath(config.sim_name)
    )
    content_dir: List[str] = os.listdir(path_directory)

    stats_file_name = f"{run}.stats.csv"
    stats_file_path = path_directory.joinpath(stats_file_name)

    routes_file_name = f"{run}.routes.csv"
    routes_file_path = path_directory.joinpath(routes_file_name)

    if not stats_file_name or not routes_file_name in content_dir:
        raise FileNotFoundError(
            f"Could not find {stats_file_name} or {routes_file_name} in {path_directory}"
        )

    return (stats_file_path, routes_file_path)


def get_route_dump_file(config: Config, alg: str, run: int) -> Tuple[Path, Path]:
    path = (
        config.routes_path.joinpath(alg)
        .joinpath(config.cstl)
        .joinpath(config.sim_name)
    )
    file_path = path.joinpath(f"{run}.routes.msgpack")
    return (path, file_path)


def load_stats(config: Config, alg: str) -> List[pd.DataFrame]:
    dfs: List[pd.DataFrame] = []
    for run in range(0, config.runs):
        (stats_fp, _) = load_simulation_paths(config, alg, run)
        print("\t\t", "Read:", stats_fp)
        dfs.append(pd.read_csv(stats_fp))
    return dfs


def plot_cdf(dfs: List[Tuple[str, pd.DataFrame]], col: str, file_path: Path):
    print("\t", "Create plot...")
    fig = make_subplots()
    for name, df in dfs:
        stats_df = (
            df.groupby(col)[col]
            .agg("count")
            .pipe(pd.DataFrame)
            .rename(columns={col: "frequency"})
        )
        # if not continuous:
        #     stats_df = stats_df.reindex(list(range(0, max_val + 1)), fill_value=0)

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
    print("\t", "Write plot to file...")
    fig.write_image(file_path, engine="kaleido")
