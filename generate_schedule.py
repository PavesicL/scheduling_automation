#!/usr/bin/env python

"""
Generates a schedule for a given month.
"""

import argparse
import random

from schedule_automation import parse_input, generate_day_list, construct_and_optimize

# Parse the command line arguments

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name')
parser.add_argument('month', type=int)
parser.add_argument('year', type=int)

parser.add_argument('NZV_weight', type=int)
parser.add_argument('POPS_weight', type=int)
parser.add_argument('PORODNA_weight', type=int)
parser.add_argument('TX_weight', type=int)

parser.add_argument('weekend_weight', type=int)
args = parser.parse_args()

# These are the weights used in the optimization
workplace_weights = [args.NZV_weight, args.POPS_weight, args.PORODNA_weight, args.TX_weight]

# Parse the data from the .tsv file and generate the list of workers and days
day_list = generate_day_list(month=args.month, year=args.year)
worker_list = parse_input(filename=args.input_file_name)

# Because the optimization is so under-determined, the initial conditions make a big difference.
# These are basically determined by the order in which you loop over the workers.
# Shuffling the list lets you generate multiple different optimal schedules.
random.shuffle(worker_list)

# Construct the model and optimize
construct_and_optimize(worker_list=worker_list,
                       day_list=day_list,
                       workplace_weights=workplace_weights,
                       penalty_weight=args.weekend_weight
                       )

print("DONE")




