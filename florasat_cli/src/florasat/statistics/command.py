import os
from pathlib import Path
import sys
from typing import Any

import tomli
from florasat.statistics.analyze_distances import analyze_distances
from florasat.statistics.analyze_hopcount import analyze_hopcounts
from florasat.statistics.analyze_packetloss import analyze_packetloss
from florasat.statistics.compare_delays import compare_delays
from florasat.statistics.preprocess_routes import preprocess_routes
from florasat.statistics.create_drop_heatmap import create_drop_heatmap
from florasat.statistics.analyze_e2edelay import analyze_e2edelay
from florasat.statistics import utils

config_name = ".florasat_config.toml"


def generate_statistics_subparser(subparsers):
    stats_parser = subparsers.add_parser(
        "statistics", help="Create statistics for FLoRaSat"
    )

    stats_parser.add_argument(
        "--cstl",
        help="Constellation name from FLoRaSat",
        dest="cstl",
        type=str,
        nargs="+",
        required=True,
    )

    stats_parser.add_argument(
        "--name",
        help="Simulation names from FLoRaSat",
        dest="sim_name",
        type=str,
        nargs="+",
        required=True,
    )

    stats_parser.add_argument(
        "--algs",
        help="Algorithms for comparison.",
        dest="algs",
        type=str,
        nargs="+",
        required=True,
    )

    stats_parser.add_argument(
        "--runs",
        help="Number of simulation repeats",
        dest="runs",
        type=int,
        required=False,
    )

    stats_parser.add_argument(
        "--config",
        help="Path to config. Only required if config was not initialized at pre-defined location.",
        dest="config_path",
        type=str,
        required=False,
    )

    stats_parser.add_argument(
        "--flora",
        help="Path to read results written by FLoRaSat. If not specified, loaded from config.",
        dest="florasat_results_path",
        type=str,
        required=False,
    )

    stats_parser.add_argument(
        "--routes",
        help="Path to read/store pre-processed routes. If not specified, loaded from config.",
        dest="routes_path",
        type=str,
        required=False,
    )

    stats_parser.add_argument(
        "--results",
        help="Path to read/store results. If not specified, loaded from config.",
        dest="results_path",
        type=str,
        required=False,
    )

    stats_parser.add_argument(
        "--preprocess-routes",
        help="Preprocess routes",
        dest="f_preprocess_routes",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--hops",
        help="Generate hops CDF",
        dest="f_hops",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--distances",
        help="Generate distances CDF",
        dest="f_distances",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--packetloss",
        help="Generate packetloss graph",
        dest="f_packetloss",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--drop-heatmap",
        help="Create packet drop heatmap",
        dest="f_drop_heatmap",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--e2e-delay",
        help="Generate E2E delay CDF",
        dest="f_e2e_delay_cdf",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--compare-delay",
        help="Generate delay comparison graph",
        dest="f_compare_delay",
        action="store_true",
        required=False,
    )

    stats_parser.add_argument(
        "--all",
        help="Generate all statistics",
        dest="f_all",
        action="store_true",
        required=False,
    )


def handle_run(args):
    # load config if required value was not set in CLI
    if (
        args.florasat_results_path is None
        or args.routes_path is None
        or args.results_path is None
        or args.runs is None
    ):
        config = __load_config(args.config_path)

        if args.florasat_results_path is None:
            try:
                path = Path(config["florasat_results_path"])
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
                path = Path(config["routes_path"])
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
                path = Path(config["results_path"])
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
                runs = int(config["runs"])
                args.runs = runs
            except KeyError:
                print(f"X Could not find a value for 'runs' in config file.")
                sys.exit(1)
            except ValueError:
                print(f"X Value for 'runs' in config file is no valid integer number.")
                sys.exit(1)

    if args.f_all:
        args.f_hops = True
        args.f_distances = True
        args.f_packetloss = True
        args.f_drop_heatmap = True
        args.f_e2e_delay_cdf = True
        args.f_compare_delay = True

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
    print("-> Gen. E2E delay CDF:", "\t", "\t", args.f_e2e_delay_cdf)
    print("-> Gen. delay comparison graph:\t", args.f_compare_delay)

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
        and not args.f_e2e_delay_cdf
        and not args.f_compare_delay
    ):
        print("")
        print("Nothing to do...")
        sys.exit(0)

    stats_config = utils.Config(
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
            preprocess_routes(stats_config)
        except FileNotFoundError as e:
            print("X Failed to preprocess routes. Could not find:", e.filename)
            sys.exit(1)

    if args.f_hops:
        print("")
        print("Run Hops CDF generation...")
        try:
            analyze_hopcounts(stats_config)
        except FileNotFoundError as e:
            print("X Failed to generate hops CDF. Could not find:", e.filename)
            sys.exit(1)

    if args.f_distances:
        print("")
        print("Run Distance CDF generation...")
        try:
            analyze_distances(stats_config)
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
            analyze_packetloss(stats_config)
        except FileNotFoundError as e:
            print("X Failed to generate packetloss graph. Could not find:", e.filename)
            sys.exit(1)

    if args.f_drop_heatmap:
        print("")
        print("Run drop heatmap generation...")
        try:
            create_drop_heatmap(stats_config)
        except FileNotFoundError as e:
            print("X Failed to generate drop heatmap. Could not find:", e.filename)
            print(
                "Are routes preprocessed? This is required once after FLoRaSat simulation runs."
            )
            sys.exit(1)

    if args.f_e2e_delay_cdf:
        print("")
        print("Run E2E delay CDF generation...")
        try:
            analyze_e2edelay(stats_config)
        except FileNotFoundError as e:
            print("X Failed to generate E2E delay CDF. Could not find:", e.filename)
            sys.exit(1)

    if args.f_compare_delay:
        print("")
        print("Run delay comparison graph generation...")
        try:
            compare_delays(stats_config)
        except FileNotFoundError as e:
            print("X Failed to generate delay comparison graph. Could not find:", e.filename)
            sys.exit(1)


def __load_config(path_raw: str | None) -> dict[str, Any]:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    home = os.environ.get("HOME")
    if path_raw is not None:
        print(f"Try to load config from {path_raw}...")
        path = Path(path_raw)
        if not (path.exists() and path.is_file()):
            raise RuntimeError(
                f"Could not load config: {path} does not exists or is no file."
            )
        with open(path, "rb") as file:
            config = tomli.load(file)
            return config
    elif xdg_config_home is not None:
        print("Try to load config from $XDG_CONFIG_HOME...")
        path = Path(xdg_config_home).joinpath(config_name)
        if not (path.exists() and path.is_file()):
            raise RuntimeError(
                f"Could not load config: {path} does not exists or is no file."
            )
        with open(path, "rb") as file:
            config = tomli.load(file)
            return config
    elif home is not None:
        print("Try to load config from $HOME...")
        path = Path(home).joinpath(config_name)
        if not (path.exists() and path.is_file()):
            raise RuntimeError(
                f"Could not load config: {path} does not exists or is no file."
            )
        with open(path, "rb") as file:
            config = tomli.load(file)
            return config
    else:
        raise RuntimeError("Neither $XDG_CONFIG_HOME or $HOME are set")