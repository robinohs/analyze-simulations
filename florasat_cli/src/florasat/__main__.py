import os
import pathlib
import argparse
import sys
import tomli

from florasat.analyze_distances import analyze_distances
from florasat.analyze_hopcount import analyze_hopcounts
from florasat.analyze_packetloss import analyze_packetloss
from florasat.preprocess_routes import preprocess_routes
from florasat.create_drop_heatmap import create_drop_heatmap
from florasat import utils


# Create CLI
def dir_path(string):
    path = pathlib.Path(string)
    if path.is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path to a directory")


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cstl",
        help="Constellation name from FLoRaSat",
        dest="cstl",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--name",
        help="Simulation name from FLoRaSat",
        dest="sim_name",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--algs",
        help="Algorithms for comparison.",
        dest="algs",
        type=str,
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--runs",
        help="Number of simulation repeats",
        dest="runs",
        type=int,
        required=False,
    )

    parser.add_argument(
        "--flora",
        help="Path to read results written by FLoRaSat. If not specified, loaded from config.",
        dest="florasat_results_path",
        type=dir_path,
        required=False,
    )

    parser.add_argument(
        "--routes",
        help="Path to read/store pre-processed routes. If not specified, loaded from config.",
        dest="routes_path",
        type=dir_path,
        required=False,
    )

    parser.add_argument(
        "--results",
        help="Path to read/store results. If not specified, loaded from config.",
        dest="results_path",
        type=dir_path,
        required=False,
    )

    parser.add_argument(
        "--preprocess-routes",
        help="Preprocess routes",
        dest="f_preprocess_routes",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--hops",
        help="Generate hops CDF",
        dest="f_hops",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--distances",
        help="Generate distances CDF",
        dest="f_distances",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--packetloss",
        help="Generate packetloss graph",
        dest="f_packetloss",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--drop-heatmap",
        help="Create packet drop heatmap",
        dest="f_drop_heatmap",
        action="store_true",
        required=False,
    )

    args = parser.parse_args()

    # load config if required value was not set in CLI
    if (
        args.florasat_results_path is None
        or args.routes_path is None
        or args.results_path is None
        or args.runs is None
    ):
        try:
            path = pathlib.Path(__file__).parent.resolve().joinpath("config.toml")
            with open(path, "rb") as f:
                try:
                    toml_dict = tomli.load(f)
                except tomli.TOMLDecodeError:
                    print("X Config file does not contain valid TOML.")
                    sys.exit(1)
        except FileNotFoundError as e:
            print("X Could not load", e.filename)
            sys.exit(1)

        if args.florasat_results_path is None:
            try:
                path = pathlib.Path(toml_dict["florasat_results_path"])
                if not path.is_dir():
                    os.makedirs(path, exist_ok=True)
                args.florasat_results_path = path
            except KeyError:
                print(
                    f"X Could not find a value for 'florasat_results_path' in config file."
                )
                sys.exit(1)
            except OSError as e:
                print(f"X Failed:", e)
                sys.exit(1)

        if args.routes_path is None:
            try:
                path = pathlib.Path(toml_dict["routes_path"])
                if not path.is_dir():
                    os.makedirs(path, exist_ok=True)
                args.routes_path = path
            except KeyError:
                print(f"X Could not find a value for 'routes_path' in config file.")
                sys.exit(1)
            except OSError as e:
                print(f"X Failed:", e)
                sys.exit(1)

        if args.results_path is None:
            try:
                path = pathlib.Path(toml_dict["results_path"])
                if not path.is_dir():
                    os.makedirs(path, exist_ok=True)
                args.results_path = path
            except KeyError:
                print(f"X Could not find a value for 'results_path' in config file.")
                sys.exit(1)
            except OSError as e:
                print(f"X Failed:", e)
                sys.exit(1)

        if args.runs is None:
            try:
                runs = int(toml_dict["runs"])
                args.runs = runs
            except KeyError:
                print(f"X Could not find a value for 'runs' in config file.")
                sys.exit(1)
            except ValueError:
                print(f"X Value for 'runs' in config file is no valid integer number.")
                sys.exit(1)

    print("")

    print("Run with configuration:")
    print("-> Cstl:", "\t", "\t", "\t", args.cstl)
    print("-> Simulation name:", "\t", "\t", args.sim_name)
    print("-> Algorithms:", "\t", "\t", "\t", args.algs)
    print("-> Runs:", "\t", "\t", "\t", args.runs)
    print("-> FLoRaSat result path:", "\t", args.florasat_results_path)
    print("-> Routes path:", "\t", "\t", args.routes_path)
    print("-> Results path:", "\t", "\t", args.results_path)
    print("-> Preprocess routes:", "\t", "\t", args.f_preprocess_routes)
    print("-> Gen. hops CDF:", "\t", "\t", args.f_hops)
    print("-> Gen. distance CDF:", "\t", "\t", args.f_distances)
    print("-> Gen. packetloss graph:", "\t", args.f_packetloss)
    print("-> Gen. drop heatmap:", "\t", "\t", args.f_drop_heatmap)

    # Validation
    print("")
    if not args.runs > 0:
        print("X Failure: At least 1 run required...")
        sys.exit(1)

    if (
        not args.f_preprocess_routes
        and not args.f_hops
        and not args.f_distances
        and not args.f_packetloss
        and not args.f_drop_heatmap
    ):
        print("")
        print("Nothing to do...")
        sys.exit(0)

    config = utils.Config(
        args.algs,
        args.cstl,
        args.sim_name,
        args.runs,
        args.florasat_results_path,
        args.routes_path,
        args.results_path,
    )

    if args.f_preprocess_routes:
        print("")
        print("Preprocess routes...")
        try:
            preprocess_routes(config)
        except FileNotFoundError as e:
            print("X Failed to preprocess routes. Could not find:", e.filename)
            sys.exit(1)

    if args.f_hops:
        print("")
        print("Run Hops CDF generation...")
        try:
            analyze_hopcounts(config)
        except FileNotFoundError as e:
            print("X Failed to generate hops CDF. Could not find:", e.filename)
            sys.exit(1)

    if args.f_distances:
        print("")
        print("Run Distance CDF generation...")
        try:
            analyze_distances(config)
        except FileNotFoundError as e:
            print("X Failed to generate distance CDF. Could not find:", e.filename)
            print(
                "Are routes preprocessed? This is required once after FLoRaSat simulation runs."
            )
            sys.exit(1)

    if args.f_packetloss:
        print("")
        print("Run packetloss graph generation...")
        try:
            analyze_packetloss(config)
        except FileNotFoundError as e:
            print("X Failed to generate packetloss graph. Could not find:", e.filename)
            sys.exit(1)

    if args.f_drop_heatmap:
        print("")
        print("Run drop heatmap generation...")
        try:
            create_drop_heatmap(config)
        except FileNotFoundError as e:
            print("X Failed to generate drop heatmap. Could not find:", e.filename)
            print(
                "Are routes preprocessed? This is required once after FLoRaSat simulation runs."
            )
            sys.exit(1)


def main():
    run()


if __name__ == "__main__":
    main()
