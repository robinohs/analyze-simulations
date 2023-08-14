import os
import time
from typing import List, Tuple
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from florasat.statistics.utils import Config, load_stats, fix_loading_mathjax


def compare_delays(config: Config):
    for cstl in config.cstl:
        for sim_name in config.sim_name:
            named_dfs: List[Tuple[str, pd.DataFrame]] = []
            for alg in config.algorithms:
                print("\t", f"Working on {alg}/{cstl}/{sim_name}...")
                # Load all runs
                df = load_stats(config, cstl, sim_name, alg)
                # Concat runs
                df = pd.concat(df)
                # Filter for delivered and Normal packets
                df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]

                # convert delays into ms
                df["queueDelay"] = (df["queueDelay"] * 1000).round()
                df["procDelay"] = (df["procDelay"] * 1000).round()
                df["transDelay"] = (df["transDelay"] * 1000).round()
                df["propDelay"] = (df["propDelay"] * 1000).round()

                # add to data
                named_dfs.append((alg, df))

            ########## Plot data ##########
            fig = go.Figure()

            for delay in ["queueDelay", "procDelay", "transDelay", "propDelay"]:
                print(f"Create plot for {delay}...")
                fig = go.Figure()

                for name, df in named_dfs:
                    fig.add_trace(go.Box(x=df[delay].values, boxpoints=False, name=name))

                # generate plot
                fig.update_xaxes(title_text="Delay [ms]", nticks=20)
                fig.update_layout(showlegend = False)

                # write plot to file
                file_path = config.results_path.joinpath(cstl).joinpath(sim_name)
                os.makedirs(file_path, exist_ok=True)
                file_path = file_path.joinpath(f"compare-{delay}.pdf")
                print("\t", "Write plot to file", file_path)
                fix_loading_mathjax()
                fig.write_image(file_path, engine="kaleido")
