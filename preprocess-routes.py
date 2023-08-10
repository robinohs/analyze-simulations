import os
import pickle
from utils import find_max_value, get_route_dump_file, load_simulation_paths, load_routes, load_stats, plot_cdf
import route_loader
########## CONFIG ##########
algorithms = [("DSPA", "dspr"), ("DDRA", "ddra"), ("RandomRoute", "random")]
# algorithms = [("DSPA", "dspr")]
cstl = "iridium"
sim_name = "normal"
runs_per_sim = 4
##############################

########### load data ##########
for name, alg in algorithms:
    print("Process:", name)
    for run in range(0, runs_per_sim):
        # load and process routes
        (_, routes_fp) = load_simulation_paths(alg, cstl, sim_name, run)
        (path, file_path) = get_route_dump_file(alg, cstl, sim_name, run)
        print("\tRead + Convert:", routes_fp)
        print("\t-> Dump to:", file_path)
        # Call Rust library function
        route_loader.process_routes(routes_fp, path, file_path) # type: ignore
        
