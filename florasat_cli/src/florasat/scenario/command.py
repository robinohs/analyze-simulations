import os
from pathlib import Path
import random
from time import gmtime, strftime
from typing import Set, Tuple

from florasat.statistics import utils

config_name = ".florasat_config.toml"


def generate_scenario_subparser(subparsers):
    scenario_parser = subparsers.add_parser(
        "scenario", help="Create config for FLoRaSat CLI"
    )

    config_subparsers = scenario_parser.add_subparsers(
        help="Commands for scenario", dest="subcommand", required=True
    )

    create_parser = config_subparsers.add_parser(
        "create", help="Creates a new scenario."
    )

    create_parser.add_argument("type")
    create_parser.add_argument("satcount", type=int)
    create_parser.add_argument("simtime", type=int)
    create_parser.add_argument("phases", type=int)
    create_parser.add_argument("lfprop", type=float)
    create_parser.add_argument("nfprop", type=float)
    create_parser.add_argument("lrprop", type=float)
    create_parser.add_argument("nrprop", type=float)
    create_parser.add_argument("--name", dest="name", type=str, required=False)
    create_parser.add_argument("--warmup", dest="warmup", type=int, required=False)


def handle_run(args):
    match args.subcommand:
        case "create":
            __create(args)


def __create(args):
    match args.type:
        case "failures":
            __create_failures(args)


def __create_failures(args):
    satcount = args.satcount
    simtime = args.simtime
    phases = args.phases
    lfprop = args.lfprop
    nfprop = args.nfprop
    lrprop = args.lrprop
    nrprop = args.nrprop
    warmup = args.warmup
    if warmup is None:
        warmup = 0
    name = args.name
    if name is None:
        name = strftime("%Y-%m-%d-%H:%M:%S", gmtime())

    phase_length = (simtime - warmup) / phases

    working_links: Set[Tuple[int, str]] = {
        (i, r) for r in ["LEFT", "UP", "RIGHT", "DOWN"] for i in range(0, satcount)
    }
    failed_links: Set[Tuple[int, str]] = set()
    working_nodes = {i for i in range(0, satcount)}
    failed_nodes = set()

    config = utils.load_config()

    print("Generate failures scenario...")

    text = "<scenario>\n"

    for phase in range(0, phases):
        start = phase * phase_length + warmup
        end = (phase + 1) * phase_length + warmup
        # print(f"Generate phase {phase} [{start}-{end}]")

        # links
        new_failed_links = set()
        for i in range(0, len(working_links)):
            wl = working_links.pop()
            if decision(lfprop):
                new_failed_links.add(wl)
            else:
                working_links.add(wl)

        repaired_links: Set[Tuple[int, str]] = set()
        for i in range(0, len(failed_links)):
            fl = failed_links.pop()
            if decision(lrprop):
                repaired_links.add(fl)
            else:
                failed_links.add(fl)
        working_links = working_links.union(repaired_links)
        failed_links = failed_links.union(new_failed_links)

        assert len(working_links) + len(failed_links) == satcount * 4

        new_failed_nodes = set()
        for i in range(0, len(working_nodes)):
            wn = working_nodes.pop()
            if decision(nfprop):
                new_failed_nodes.add(wn)
            else:
                working_nodes.add(wn)

        repaired_nodes = set()
        for i in range(0, len(failed_nodes)):
            fl = failed_nodes.pop()
            if decision(nrprop):
                repaired_nodes.add(fl)
            else:
                failed_nodes.add(fl)
        working_nodes = working_nodes.union(repaired_nodes)
        failed_nodes = failed_nodes.union(new_failed_nodes)

        assert len(working_nodes) + len(failed_nodes) == satcount

        # write as text

        text += f"\t<!-- LinkFailures: {len(failed_links)}; NodeFailures: {len(failed_nodes)} -->\n"
        text += f'\t<at t="{int(round(start))}s">\n'
        for id, dir in repaired_links:
            text += f'\t\t<set-isl-state satid="{id}" dir="{dir}" value="WORKING" />\n'
        for id, dir in new_failed_links:
            text += f'\t\t<set-isl-state satid="{id}" dir="{dir}" value="DISABLED" />\n'
        for repaired_node in repaired_nodes:
            text += f'\t\t<set-isl-state satid="{repaired_node}" value="WORKING" />\n'
        for failed_node in new_failed_nodes:
            text += f'\t\t<set-isl-state satid="{failed_node}" value="DISABLED" />\n'
        text += f"\t</at>\n"

    text = text + "</scenario>\n"

    path = Path(config["results_path"])
    if not path.is_dir():
        os.makedirs(path, exist_ok=True)
    file_path = path.joinpath(f"{name}.xml")
    print(f"Write scenario to {file_path}")
    with open(file_path, "w") as f:
        f.write(text)


def decision(probability: float):
    return random.random() < probability
