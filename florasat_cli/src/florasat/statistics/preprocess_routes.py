from florasat.statistics.utils import Config, get_route_dump_file, load_simulation_paths
import florasat_statistics


def preprocess_routes(config: Config):
    ########### load data ##########
    for cstl in config.cstl:
        for sim_name in config.sim_name:
            for alg in config.algorithms:
                print("\t", f"Preprocess routes for {alg}/{cstl}/{sim_name}...")
                for run in range(0, config.runs):
                    # load and process routes
                    (_, routes_fp) = load_simulation_paths(
                        config, cstl, sim_name, alg, run
                    )
                    (path, file_path) = get_route_dump_file(
                        config, cstl, sim_name, alg, run
                    )
                    print("\t", "\t", "Read + Convert:", routes_fp)
                    print("\t", "\t", "-> Dump to:", file_path)
                    # Call Rust library function
                    florasat_statistics.process_routes(
                        str(routes_fp), str(path), str(file_path)
                    )
