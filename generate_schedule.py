#!/usr/bin/env python

"""
Generates a schedule for a given month.
"""

import argparse
import random
import json

from datetime import date

from scheduling_automation import parse_input, generate_day_list, construct_and_optimize

# Parse the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('config_file')
parser.add_argument('requests_file')
args = parser.parse_args()

with open(args.config_file) as f:
    config = json.load(f)

# These are the weights used in the optimization
workplace_weights = [
    config["NZV_weight"],
    config["POPS_weight"],
    config["PORODNA_weight"],
    config["TX_weight"],
]

# parse the dates
start_date = date.fromisoformat(config["start_date"])
end_date = date.fromisoformat(config["end_date"])
day_list = generate_day_list(start_date=start_date, end_date=end_date)

# Parse the data from the .tsv file and generate the list of workers and days
worker_list = parse_input(filename=args.requests_file)

print("Generating the schedule for:")
print(day_list)

# Check that the number of days matches the schedule requests.
if any( [len(w.work_dates) != len(day_list) for w in worker_list] ):
    raise Exception(f"The number of work dates does not match the calendar!\n We have {len(day_list)} days, but got {[len(w.work_dates) for w in worker_list]}.")

# Because the optimization is so under-determined, the initial conditions make a big difference.
# These are basically determined by the order in which you loop over the workers.
# Shuffling the list lets you generate multiple different optimal schedules.
random.shuffle(worker_list)

# Construct the model and optimize
construct_and_optimize(worker_list=worker_list,
                       day_list=day_list,
                       workplace_weights=workplace_weights,
                       penalty_weekend_package=config["penalty_weekend_package"],
                       penalty_equal_distribution=config["penalty_equal_distribution"]
                       )

print("DONE")




