########## CONFIG ##########
algorithms = [("Random", "random"), ("DSPA", "dspr"), ("DDRA", "ddra")]
cstl = "iridium"
sim_name = "normal"
runs_per_sim = 4
##############################

import argparse
import sys
from analyze_distances import analyze_distances

from analyze_hopcount import analyze_hopcounts
from analyze_packetloss import analyze_packetloss
from preprocess_routes import preprocess_routes
from create_drop_heatmap import create_drop_heatmap

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
    "--runs", help="Number of simulation repeats", dest="runs", type=int, default=4
)

parser.add_argument(
    "--preprocess-routes",
    help="Preprocess routes",
    dest="f_preprocess_routes",
    action="store_true",
)

parser.add_argument(
    "--hops",
    help="Generate hops CDF",
    dest="f_hops",
    action="store_true",
)

parser.add_argument(
    "--distances",
    help="Generate distances CDF",
    dest="f_distances",
    action="store_true",
)

parser.add_argument(
    "--packetloss",
    help="Generate packetloss graph",
    dest="f_packetloss",
    action="store_true",
)

parser.add_argument(
    "--drop-heatmap",
    help="Create packet drop heatmap",
    dest="f_drop_heatmap",
    action="store_true",
)

args = parser.parse_args()


print("")

print("Run with configuration:")
print("-> cstl:", "\t", "\t", "\t", args.cstl)
print("-> sim_name:", "\t", "\t", "\t", args.sim_name)
print("-> algorithms:", "\t", "\t", "\t", args.algs)
print("-> runs:", "\t", "\t", "\t", args.runs)
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

if args.f_preprocess_routes:
    print("")
    print("Preprocess routes...")
    try:
        preprocess_routes(args.algs, args.cstl, args.sim_name, args.runs)
    except FileNotFoundError as e:
        print("X Failed to preprocess routes. Could not find:", e.filename)
        sys.exit(1)

if args.f_hops:
    print("")
    print("Run Hops CDF generation...")
    try:
        analyze_hopcounts(args.algs, args.cstl, args.sim_name, args.runs)
    except FileNotFoundError as e:
        print("X Failed to generate hops CDF. Could not find:", e.filename)
        sys.exit(1)

if args.f_distances:
    print("")
    print("Run Distance CDF generation...")
    try:
        analyze_distances(args.algs, args.cstl, args.sim_name, args.runs)
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
        analyze_packetloss(args.algs, args.cstl, args.sim_name, args.runs)
    except FileNotFoundError as e:
        print("X Failed to generate packetloss graph. Could not find:", e.filename)
        sys.exit(1)

if args.f_drop_heatmap:
    print("")
    print("Run drop heatmap generation...")
    try:
        create_drop_heatmap(args.algs, args.cstl, args.sim_name, args.runs)
    except FileNotFoundError as e:
        print("X Failed to generate drop heatmap. Could not find:", e.filename)
        print(
            "Are routes preprocessed? This is required once after FLoRaSat simulation runs."
        )
        sys.exit(1)
