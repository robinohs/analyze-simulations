from typing import List, Tuple
import pandas as pd

from utils import find_max_value, load_simulation_paths, load_routes, load_stats, plot_cdf

########## CONFIG ##########
algorithms = [("DSPA", "dspr"), ("DDRA", "ddra"), ("RandomRoute", "random")]
cstl = "iridium"
sim_name = "normal"
runs_per_sim = 4
##############################

########### load data ##########
named_dfs: List[Tuple[str, pd.DataFrame]] = []
for name, alg in algorithms:
    # Load all runs
    df = load_stats(alg, cstl, sim_name, runs_per_sim)
    # Concat runs
    df = pd.concat(df)
    # Filter for delivered and Normal packets
    df = df.loc[(df["dropReason"] == 99) & (df["type"] == "N")]
    # add to data
    named_dfs.append((name, df))

########## Plot data ##########
max_hops = find_max_value(list(map(lambda df: df[1], named_dfs)), "hops")

file_name = f"hopcount-{cstl}-{sim_name}.cdf.pdf"
plot_cdf(named_dfs, max_hops, "hops", file_name)
