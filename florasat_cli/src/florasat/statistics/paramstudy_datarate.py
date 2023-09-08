import os
from florasat_statistics import load_routes, load_sat_stats
import numpy as np
import pandas as pd
from florasat.statistics.utils import (
    Config,
    apply_default,
    get_route_dump_file,
    get_sats_dump_file,
    load_simulation_paths,
    load_stats,
)
import plotly.express as px


def paramstudy_datarate(config: Config):
    cstl_queues = {}
    cstl_delays = {}
    sizes = set()
    datarates = set()
    for cstl in config.cstl:
        size = int(cstl.split("-")[1])
        sizes.add(size)
        print("Working on cstl", size)
        sim_queues = {}
        sim_delays = {}
        for sim_name in config.sim_name:
            datarate = int(sim_name.split("-")[-1])
            datarate = int(datarate / 1000000)
            datarates.add(datarate)
            # print("Working on alt", alt)

            alg_queues = {}
            alg_delays = {}

            for alg in config.algorithms:
                # print("\t", f"Working on {alg}")
                (stats_path, _, _) = load_simulation_paths(
                    config, cstl, sim_name, alg, 0
                )
                (_, file_path) = get_sats_dump_file(config, cstl, sim_name, alg, 0)

                satellites = load_sat_stats(str(file_path))

                df = pd.DataFrame(columns=["id", "timestamp", "queueSize"])
                for sat in satellites:
                    id = sat.sat_id
                    entries = [[id, entry.start, entry.qs] for entry in sat.entries]

                    df = pd.concat(
                        [pd.DataFrame(entries, columns=df.columns), df],
                        ignore_index=True,
                    )
                df["timestamp"] = df["timestamp"].round(1)

                df = (
                    df.groupby(["timestamp"])["queueSize"]
                    .mean()
                    .pipe(pd.DataFrame)
                    .reset_index()
                )

                # print(df)

                mean_queue = df["queueSize"].mean()
                alg_queues[alg] = mean_queue

                df = pd.read_csv(stats_path)

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

                mean_delay = df["e2e-delay"].mean()

                alg_delays[alg] = mean_delay

            # preprocess queues
            mean_queues = 0
            keys = len(alg_queues.keys())
            for key in alg_queues.keys():
                mean_queues += alg_queues[key]
            mean_queues = mean_queues / keys
            sim_queues[datarate] = mean_queues

            # preprocess delays
            mean_delay = 0
            keys = len(alg_delays.keys())
            for key in alg_delays.keys():
                mean_delay += alg_delays[key]
            mean_delay = mean_delay / keys

            sim_delays[datarate] = mean_delay

        cstl_queues[size] = sim_queues
        cstl_delays[size] = sim_delays

    sizes = list(sizes)
    sizes.sort()
    datarates = list(datarates)
    datarates.sort()

    for size in sizes:
        factor = None
        for datarate in datarates:
            if factor is None:
                factor = 1 / cstl_queues[size][datarate]
                print(f"Set {size} {datarate} to 0")
                cstl_queues[size][datarate] = 0.0
            else:
                print(
                    f"Set {size} {datarate} to {(cstl_queues[size][datarate] * factor - 1) * 100}"
                )
                cstl_queues[size][datarate] = (
                    cstl_queues[size][datarate] * factor - 1
                ) * 100

    ###################################################################
    ########################### plot queues ###########################
    ###################################################################
    df = pd.DataFrame.from_dict(cstl_queues)
    df.index = df.index.astype(int)
    df = df.sort_index()

    fig = px.bar(df, x=df.index, y=sizes, barmode="group", text_auto=True)

    fig.update_traces(
        # textfont_size=26, textangle=90, textposition="inside", cliponaxis=False
        texttemplate="+%{value:.2f}%",
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
        xaxis_title="Datarate [MBit/s]",
        yaxis_title="Relative Congestion",
    )

    fig.update_xaxes(type="category")
    # fig.update_traces(marker_line_color="#000", marker_line_width=1)

    print("\t", "Write plot to file...")
    file_path = config.results_path
    os.makedirs(file_path, exist_ok=True)
    file_path = file_path.joinpath(f"paramstudy-datarate-congestion.pdf")
    apply_default(fig)
    fig.write_image(file_path, engine="kaleido")

    ###################################################################
    ########################### plot delays ###########################
    ###################################################################
    df = pd.DataFrame.from_dict(cstl_delays)
    df.index = df.index.astype(int)
    df = df.sort_index()

    sizes = [int(x) for x in sizes]

    fig = px.bar(df, x=df.index, y=sizes, barmode="group", text_auto=True)

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
        xaxis_title="Datarate [MBit/s]",
        yaxis_title="Avg. Packet Delay [ms]",
    )

    fig.update_xaxes(type="category")

    print("\t", "Write plot to file...")
    file_path = config.results_path
    os.makedirs(file_path, exist_ok=True)
    file_path = file_path.joinpath(f"paramstudy-datarate-delays.pdf")
    apply_default(fig)
    fig.write_image(file_path, engine="kaleido")
