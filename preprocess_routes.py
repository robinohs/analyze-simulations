from utils import get_route_dump_file, load_simulation_paths
import route_loader


def preprocess_routes(algorithms, cstl, sim_name, runs_per_sim):
    ########### load data ##########
    for alg in algorithms:
        print("\t", f"Preprocess routes for {alg}/{cstl}/{sim_name}...")
        for run in range(0, runs_per_sim):
            # load and process routes
            (_, routes_fp) = load_simulation_paths(alg, cstl, sim_name, run)
            (path, file_path) = get_route_dump_file(alg, cstl, sim_name, run)
            print("\t","\t", "Read + Convert:", routes_fp)
            print("\t","\t", "-> Dump to:", file_path)
            # Call Rust library function
            route_loader.process_routes(routes_fp, path, file_path)
