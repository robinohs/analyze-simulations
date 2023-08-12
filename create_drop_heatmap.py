from math import sqrt
from dataclasses import dataclass, asdict
import time
from typing import Dict, List, Tuple
import pandas as pd
from route_loader import load_routes
import plotly.graph_objects as go
import plotly.express as px
import route_loader

from utils import get_route_dump_file, load_simulation_paths, load_stats


@dataclass
class Groundstation:
    id: int
    lat: float
    lon: float
    alt: int


# def calculate_between_coordinates(
#     p1: Tuple[float, float], p2: Tuple[float, float]
# ) -> Tuple[float, float]:
#     (src_lat, src_lon) = p1
#     (dst_lat, dst_lon) = p2

#     # calc middle lat
#     lower_lat, upper_lat = (
#         (src_lat + 90, dst_lat + 90)
#         if src_lat < dst_lat
#         else (dst_lat + 90, src_lat + 90)
#     )
#     # print(lower_lat, upper_lat)
#     lat_distance_inner = upper_lat - lower_lat
#     lat_distance_outer = lower_lat + 180 - upper_lat
#     assert lat_distance_inner + lat_distance_outer == 180

#     if lat_distance_inner < lat_distance_outer:
#         m_lat = lower_lat + lat_distance_inner / 2 - 90
#     else:
#         m_lat = (lower_lat - upper_lat / 2) - 90
#     print(lower_lat - 90, upper_lat - 90)
#     print(m_lat)

#     # calc middle lon
#     left_lon, right_lon = (
#         (src_lon + 180, dst_lon + 180)
#         if src_lon < dst_lon
#         else (dst_lon + 180, src_lon + 180)
#     )
#     lon_distance_inner = right_lon - left_lon
#     lon_distance_outer = left_lon + 360 - right_lon
#     assert lon_distance_inner + lon_distance_outer == 360

#     if lon_distance_inner < lon_distance_outer:
#         m_lon = (left_lon + lon_distance_inner / 2) - 180
#     else:
#         m_lon = (left_lon - lon_distance_outer / 2) - 180
#     print(left_lon - 180, right_lon - 180)
#     print(m_lon)
#     return (m_lat, m_lon)


def create_drop_heatmap(algorithms, cstl, sim_name, runs_per_sim):
    ########### load data ##########
    for alg in algorithms:
        ground_stations: List = []
        seen_ids = set()
        # get groundstations that were involved in traffic
        run_dfs = []
        for run in range(0, runs_per_sim):
            (stats_fp, _) = load_simulation_paths(alg, cstl, sim_name, run)
            df = pd.read_csv(stats_fp)
            # load and process routes
            (_, file_path) = get_route_dump_file(alg, cstl, sim_name, run)

            print("\t", "Load", file_path)
            routes = load_routes(file_path)

            print("\t", "Get ground stations...")
            for r in routes:
                for h in r.hops:
                    if h.typ == "G" and h.id not in seen_ids:
                        seen_ids.add(h.id)
                        gs = Groundstation(h.id, h.lat, h.lon, h.alt)
                        ground_stations.append(asdict(gs))

            print("\t", "Fill dataframe with drop locations...")

            last_lats = list(map(lambda x: round(x.hops[-1].lat), routes))
            last_lons = list(map(lambda x: round(x.hops[-1].lon), routes))

            df["dropLat"] = last_lats
            df["dropLon"] = last_lons

            df = df.loc[df["dropReason"] != 99]
            run_dfs.append(df)

        df = pd.concat(run_dfs)

        df = (
            df.groupby(["dropLat", "dropLon"])["dropLat"]
            .agg("count")
            .pipe(pd.DataFrame)
            .rename(columns={"dropLat": "dropped"})
            .astype("Int64")
        )

        print("\t", f"Create plot for {alg}...")
        fig = go.Figure()

        # Add dropspots
        for (lat, lon), dropped in df.itertuples():
            fig.add_trace(
                go.Scattergeo(
                    lon=[lon],
                    lat=[lat],
                    mode="markers",
                    showlegend=False,
                    opacity=0.6,
                    marker=dict(
                        size=dropped**(1/3),
                        symbol="circle",
                        color="red",
                    ),
                )
            )

        # Add groundstations
        gs_df = pd.DataFrame(ground_stations)
        fig.add_trace(
            go.Scattergeo(
                lon=gs_df["lon"],
                lat=gs_df["lat"],
                text=gs_df["id"],
                textposition="bottom right",
                mode="markers+text",
                showlegend=False,
                marker=dict(
                    size=5,
                    symbol="circle",
                    color="black",
                ),
            )
        )

        print("\t", "Write plot to file...")
        file_name = f"dropspots-{alg}-{cstl}-{sim_name}.map.pdf"
        fig.write_image(file_name, engine="kaleido")
        time.sleep(1)
        fig.write_image(file_name, engine="kaleido")

    # gs_df = pd.DataFrame(ground_stations)

    # print("\t", "Create plot...")
    # fig = go.Figure()

    # # Add groundstations
    # fig.add_trace(
    #     go.Scattergeo(
    #         lon=gs_df["lon"],
    #         lat=gs_df["lat"],
    #         text=gs_df["id"],
    #         showlegend=False,
    #         marker=dict(
    #             size=5,
    #             symbol="circle",
    #             color="black",
    #         ),
    #     )
    # )

    # for (name, df) in named_dfs:
    #     print(name)
    #     print(df)

    # print("\t", "Write plot to file...")
    # file_name = f"traffic-topology-{cstl}-{sim_name}.map.pdf"
    # fig.write_image(file_name, engine="kaleido")
    # time.sleep(1)
    # fig.write_image(file_name, engine="kaleido")