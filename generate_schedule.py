#!/usr/bin/env python

"""
Generates a schedule for a given month.
"""

import argparse
import random

from scheduling_automation import parse_input, generate_day_list, construct_and_optimize

# Parse the command line arguments

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name')
parser.add_argument('month', type=int)
parser.add_argument('year', type=int)

parser.add_argument('NZV_weight', type=int)
parser.add_argument('POPS_weight', type=int)
parser.add_argument('PORODNA_weight', type=int)
parser.add_argument('TX_weight', type=int)

parser.add_argument('penalty_weekend_package', type=int)
parser.add_argument('penalty_equal_distribution', type=int)

parser.add_argument('--next_month_days', type=int, default=0)

args = parser.parse_args()

# These are the weights used in the optimization
workplace_weights = [args.NZV_weight, args.POPS_weight, args.PORODNA_weight, args.TX_weight]

# Parse the data from the .tsv file and generate the list of workers and days
day_list = generate_day_list(month=args.month, year=args.year, next_month_days=args.next_month_days)
worker_list = parse_input(filename=args.input_file_name)

print("Generating the schedule for:")
print(day_list)

# Check that the number of days matches the schedule requests.
if any( len(w.work_dates) != len(day_list) for w in worker_list ):
    raise Exception(f"The number of work dates does not match the calendar!\n We have {len(day_list)} days, but got {len(w.work_dates) for w in worker_list}.")

# Because the optimization is so under-determined, the initial conditions make a big difference.
# These are basically determined by the order in which you loop over the workers.
# Shuffling the list lets you generate multiple different optimal schedules.
random.shuffle(worker_list)

# Construct the model and optimize
construct_and_optimize(worker_list=worker_list,
                       day_list=day_list,
                       workplace_weights=workplace_weights,
                       penalty_weekend_package=args.penalty_weekend_package,
                       penalty_equal_distribution=args.penalty_equal_distribution
                       )

print("DONE")




