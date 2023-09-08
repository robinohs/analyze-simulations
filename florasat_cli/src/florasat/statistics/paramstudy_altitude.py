import os
from florasat_statistics import load_routes
import pandas as pd
from florasat.statistics.utils import (
    Config,
    apply_default,
    get_route_dump_file,
    load_simulation_paths,
    load_stats,
)
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px


def paramstudy_altitude(config: Config):
    cstl_distances = {}
    cstl_delays = {}
    sizes = []
    for cstl in config.cstl:
        size = cstl.split("-")[2]
        sizes.append(size)
        print("Working on cstl", size)
        sim_distances = {}
        sim_delays = {}
        for sim_name in config.sim_name:
            alt = sim_name.split("-")[-1]
            # print("Working on alt", alt)

            alg_distances = {}
            alg_delays = {}

            for alg in config.algorithms:
                # print("\t", f"Working on {alg}")
                (stats_path, _, _) = load_simulation_paths(
                    config, cstl, sim_name, alg, 0
                )
                (_, file_path) = get_route_dump_file(config, cstl, sim_name, alg, 0)

                routes = load_routes(str(file_path))
                distances = list(map(lambda r: r.length, routes))

                df = pd.read_csv(stats_path)
                df["distance"] = distances

                df["e2e-delay"] = (
                    (
                        df["queueDelay"]
                        + df["procDelay"]
                        + df["transDelay"]
                        + df["propDelay"]
                    )
                    * 1000
                ).round()

                df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]

                mean_distance = df["distance"].mean()
                mean_delay = df["e2e-delay"].mean()

                alg_distances[alg] = mean_distance
                alg_delays[alg] = mean_delay

                # new_record = pd.DataFrame([{'Name':'Jane', 'Age':25, 'Location':'Madrid'}])
                # sim_df = pd.concat([sim_df, new_record], ignore_index=True)

                # fig.add_trace(
                #     go.Scatter(
                #         name="Test",
                #         x=stats_df["distance"].values,
                #         y=stats_df["cdf"],
                #         mode="markers+lines",
                #     )
                # )
            
            mean_distance = 0
            keys = len(alg_distances.keys())
            for key in alg_distances.keys():
                mean_distance += alg_distances[key]

            mean_distance = mean_distance / keys

            mean_delay = 0
            keys = len(alg_delays.keys())
            for key in alg_delays.keys():
                mean_delay += alg_delays[key]

            mean_delay = mean_delay / keys

            sim_distances[alt] = mean_distance
            sim_delays[alt] = mean_delay
        cstl_distances[size] = sim_distances
        cstl_delays[size] = sim_delays
    print(cstl_distances)
    print(cstl_delays)

    # plot delays
    df = pd.DataFrame.from_dict(cstl_delays)

    df.index = df.index.astype(int)

    df = df.sort_index()

    # smallest = [df[size].min() for size in sizes]
    # smallest = min(smallest) * 0.95  # type: ignore

    # biggest = [df[size].max() for size in sizes]
    # biggest = max(biggest) * 1.01  # type: ignore

    # print(smallest, biggest)

    fig = px.bar(
        df, x=df.index, y=sizes, barmode="group", text_auto=True
    )

    fig.update_traces(
        # textfont_size=26, textangle=90, textposition="inside", cliponaxis=False
        texttemplate="%{value:.2f}",
    )

    fig.update_layout(
        legend={
            "title_text": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.18,
            "xanchor": "left",
            "x": -0.1,
        },
        xaxis_title="Altitude [km]",
        yaxis_title="Avg. Packet Delay [ms]",
    )

    # fig.update_yaxes(range=[smallest, biggest])

    print("\t", "Write plot to file...")
    file_path = config.results_path
    os.makedirs(file_path, exist_ok=True)
    file_path = file_path.joinpath(f"paramstudy-altitude-delays.pdf")
    apply_default(fig)
    fig.write_image(file_path, engine="kaleido")


    # # plot distances
    df = pd.DataFrame.from_dict(cstl_distances)

    df.index = df.index.astype(int)

    df = df.sort_index()

    # smallest = [df[alg].min() for alg in config.algorithms]
    # smallest = min(smallest) * 0.95  # type: ignore

    # biggest = [df[alg].max() for alg in config.algorithms]
    # biggest = max(biggest) * 1.01  # type: ignore

    # print(smallest, biggest)

    fig = px.bar(
        df, x=df.index, y=sizes, barmode="group", text_auto=True
    )

    fig.update_traces(
        # textfont_size=26, textangle=90, textposition="inside", cliponaxis=False
        texttemplate="%{value:.0f}",
    )

    fig.update_layout(
        legend={
            "title_text": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.18,
            "xanchor": "left",
            "x": -0.1,
        },
        xaxis_title="Altitude [km]",
        yaxis_title="Avg. Packet Distance [km]",
    )

    # fig.update_yaxes(range=[smallest, biggest])

    print("\t", "Write plot to file...")
    file_path = config.results_path
    os.makedirs(file_path, exist_ok=True)
    file_path = file_path.joinpath(f"paramstudy-altitude-distances.pdf")
    apply_default(fig)
    fig.write_image(file_path, engine="kaleido")

