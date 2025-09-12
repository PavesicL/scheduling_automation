"""
Contains the construction of the model.
"""
import csv
from ortools.sat.python import cp_model

from .days import Day
from .worker import Worker, ALL_WORKPLACES


def construct_and_optimize(worker_list : list[Worker], day_list : list[Day], workplace_weights : list[int], penalty_weekend_package : int, penalty_equal_distribution : int) -> None:
    """
    Defines the model used for optimization, and optimizes it.

    Hard constraints (must be fulfilled):
    - There is exactly one worker per site. All sites are full every day, excepy
      POPS, which exists only on workdays (not weekends or Holidays).
    - Some workers only work in some workplaces.
    - The worker can be assigned at most one shift per day.
    - After working NZV or PORODNA, the worker gets the next day off.

    Soft constraints (enforced by a penalty):
    - A worker can request a 'weekend_package': to be assigned to any combination
      of PORODNA or NZV or a Friday, and the next Sunday.
    - Each worker should be equally distributed among the workplaces he works at.
      For each workplace, we check where they are assigned the most times, and where
      they are assigned the least. Then, we minimize this imbalance for each worker.

    The model is optimized by minimizing the difference between the smallest and
    largest amount of work assigned. This aims to equally distribute the workload.
    An alternative would be to minimize the variance of the distribution of assigned
    work.
    The assignment to different workplaces is weighed differently. The weights are passed
    though the workplace_weights argument. Must be integers!
    The soft constraints are added into the objective function with a penalty prefactor.

    Arguments:
        worker_list : list[Worker]
            List of Worker objects containing their requests.
        day_list : list[Day]
            List of days in the month.
        workplace_weights : list[int]
            The weights assigned to each workplace when optimizing the
            schedule. Must match the alphabetical order of workplaces in ALL_WORKPLACES.
        penalty_weekend_package : int
            The weight penalising the assignment of the weekend package.
        penalty_equal_distribution : int
            The weight penalising the imbalanced distribution of a worker across workplaces.

    Returns:
        CpModel
            The model with the required constraints.
    """

    # define an empty model
    model = cp_model.CpModel()

    # some useful numbers
    num_workers = len(worker_list)
    num_days = len(day_list)
    num_workplaces = len(ALL_WORKPLACES)

    nzv_index = ALL_WORKPLACES.index("NZV")
    porodna_index = ALL_WORKPLACES.index("PORODNA")
    pops_index = ALL_WORKPLACES.index("POPS")
    tx_index = ALL_WORKPLACES.index("TX")

    # Variables: work[(ww, dd, pp)] = 1 if worker w works site s on day d
    # In for loops: ww - workers, dd - days, pp - places
    work = {}
    for ww in range(num_workers):
            for dd in range(num_days):
                for pp in range(num_workplaces):
                    work[ww, dd, pp] = model.NewBoolVar(f'work_{ww}_{dd}_{pp}')

    # Constraint: exactly one worker per site.
    for dd, day in enumerate(day_list):
        model.add_exactly_one(work[ww, dd, nzv_index] for ww in range(num_workers) )
        model.add_exactly_one(work[ww, dd, porodna_index] for ww in range(num_workers) )
        model.add_exactly_one(work[ww, dd, tx_index] for ww in range(num_workers) )

        # POPS only on workdays
        if day.is_workday:
            model.Add( sum( work[ww, dd, pops_index] for ww in range(num_workers)) == 1)
        else:
            model.Add( sum( work[ww, dd, pops_index] for ww in range(num_workers)) == 0)

    # Constraint: worker works only in certain workplaces
    for ww, worker in enumerate(worker_list):
        for dd in range(num_days):
            for pp, workplace in enumerate(ALL_WORKPLACES):
                if workplace not in worker.workplaces:
                    model.Add( work[ww, dd, pp] == 0 )

    # Constraint: at most one shift per day, if the worker can work.
    for ww, worker in enumerate(worker_list):
        for dd in range(num_days):
            if worker.work_dates[dd]:
                model.Add( sum( work[ww, dd, pp] for pp in range(num_workplaces) ) <= 1 )
            else:
                model.Add( sum( work[ww, dd, pp] for pp in range(num_workplaces) ) == 0 )

    # Constraint: After working NZV or PORODNA or POPS, next day off
    for ww in range(num_workers):
        for dd in range(num_days - 1):
            # If work porodna or nzv or pops on day dd then no work on day dd+1
            model.Add(work[ww, dd, nzv_index] + work[ww, dd, porodna_index] + work[ww, dd, pops_index] + sum(work[ww, dd+1, pp] for pp in range(num_workplaces)) <= 1)


    ####################################################################################################################################
    # Weekend package soft assignment: assign worker to work Fri and Sun (nzv or porodna) up to once per month

    # All Fridays where the ensuing Sunday is included in the month.
    fridays = [ ii for ii, day in enumerate(day_list) if day.isoweekday() == 5 and ii + 2 < len(day_list) ]

    assigned_weekends = []
    weekend_penalties = []
    # Enforce at most one weekend package per worker
    for ww, worker in enumerate(worker_list):
        and_vars = []
        for dd in fridays:
            # For each combination of site assignments on Friday and Sunday
            for (site1, site2) in [
                (porodna_index, porodna_index),
                (nzv_index, nzv_index),
                (nzv_index, porodna_index),
                (porodna_index, nzv_index)
            ]:
                and_var = model.NewBoolVar(f'and_{ww}_{dd}_{site1}_{site2}')
                # and_var is true iff both Friday and Sunday sites are assigned accordingly
                # Model: and_var = work[ww, dd, site1] AND work[ww, dd + 2, site2]
                model.AddBoolAnd([work[ww, dd, site1], work[ww, dd + 2, site2]]).OnlyEnforceIf(and_var)
                model.AddBoolOr([work[ww, dd, site1].Not(), work[ww, dd + 2, site2].Not()]).OnlyEnforceIf(and_var.Not())
                and_vars.append(and_var)


        # At most one such weekend package assignment per worker across all Fridays
        model.Add(sum(and_vars) <= 1)

        # Introduce a worker-level binary var to indicate weekend package assignment
        assigned_weekend_package = model.NewBoolVar(f'assigned_weekend_package_{ww}')
        assigned_weekends.append(assigned_weekend_package)

        # Link assigned_weekend_package to the or of all and_vars
        model.AddBoolOr(and_vars).OnlyEnforceIf(assigned_weekend_package)
        model.AddBoolAnd([var.Not() for var in and_vars]).OnlyEnforceIf(assigned_weekend_package.Not())

        # Add penalty * weight to the objective to soften weekend package assignment
        weekend_penalties.append(assigned_weekend_package * worker.weekend_package * (-1) )

    # Collect the total penalty
    total_weekend_penalty = model.NewIntVar(-num_workers, num_workers, 'total_penalty')
    model.Add(total_weekend_penalty == sum(weekend_penalties))

    ####################################################################################################################################
    # Soft constraint for a balanced assignment across workplaces.

    imbalance_penalties = []

    total_work_site = {}
    max_work_site = []
    min_work_site = []
    imbalances = []
    for ww, worker in enumerate(worker_list):
        works = []

        # Iterate over the workplaces each worker works at and collect the number of times
        # he is assigned to each.
        for pp in range(num_workplaces):
            if ALL_WORKPLACES[pp] in worker.workplaces:
                total = model.NewIntVar(0, num_days, f'total_work_site_{ww}_{pp}')
                model.Add(total == sum(work[ww, dd, pp] for dd in range(num_days)))
                total_work_site[ww, pp] = total
                works.append(total)

        # max_pp and min_pp encode max(works) and min(works) respectively.
        # These is the biggest and smallest number of assignments for each worker.
        max_pp = model.NewIntVar(0, num_days, f'max_work_site_{ww}')
        min_pp = model.NewIntVar(0, num_days, f'min_work_site_{ww}')
        model.AddMaxEquality(max_pp, works)
        model.AddMinEquality(min_pp, works)
        max_work_site.append(max_pp)
        min_work_site.append(min_pp)

        # imb is the imbalance: the difference between the min and max
        imb = model.NewIntVar(0, num_days, f'imbalance_{ww}')
        model.Add(imb == max_pp - min_pp)
        imbalances.append(imb)

    # Collect the total penalty across all workers
    total_imbalance = model.NewIntVar(0, num_workers * num_days, 'total_imbalance')
    model.Add(total_imbalance == sum(imbalances))

    ####################################################################################################################################

    # Optimize for fairness:
    # We minimize the difference between the largest and the smallest amount of work assigned.
    # Not all workplaces are weighed equally.

    total_work = []
    max_possible_work = num_days * max(workplace_weights) # one shift per day is the max
    for ww in range(num_workers):
        total = model.NewIntVar(0, max_possible_work, f'total_work_{ww}')
        model.Add(total == sum(workplace_weights[pp] * work[ww, dd, pp] for dd in range(num_days) for pp in range(num_workplaces)))
        total_work.append(total)

    max_work = model.NewIntVar(0, max_possible_work, 'max_work')
    min_work = model.NewIntVar(0, max_possible_work, 'min_work')
    model.AddMaxEquality(max_work, total_work)
    model.AddMinEquality(min_work, total_work)

    # Objective function:
    model.Minimize((max_work - min_work) + (total_weekend_penalty * penalty_weekend_package) + (total_imbalance * penalty_equal_distribution))

    # Solve model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Write the output.
    schedule_array = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for dd, day in enumerate(day_list):
            #print(dd, day)
            schedule_array.append([])
            for pp, workplace in enumerate(ALL_WORKPLACES):
                for ww in range(num_workers):

                    # handle the POPS weekend separately
                    if workplace == "POPS" and not day.is_workday:
                        schedule_array[dd].append("NONE")
                        break

                    elif solver.Value(work[ww, dd, pp]) == 1:
                        schedule_array[dd].append(worker_list[ww])

        # Add the workplaces as the header
        schedule_array.insert(0, ALL_WORKPLACES.copy())
    else:
        raise Exception(f"The optimization was not successful. The solver status is {status}.")

    ########################################################################
    # Collect and print some stats.

    number_of_shifts = {
        worker : sum( solver.Value(work[ww, dd, pp]) for dd in range(num_days) for pp in range(num_workplaces) )
        for ww, worker in enumerate(worker_list)
    }
    number_of_shifts_per_workplace = {
        (worker, ALL_WORKPLACES[pp]) : sum( solver.Value(work[ww, dd, pp]) for dd in range(num_days))
        for pp in range(num_workplaces)
        for ww, worker in enumerate(worker_list)
    }
    number_of_weighted_shifts = {
        worker : sum( workplace_weights[pp] * solver.Value(work[ww, dd, pp]) for dd in range(num_days) for pp in range(num_workplaces) )
        for ww, worker in enumerate(worker_list)
    }

    max_shifts_worker, max_shifts = max( number_of_shifts.items(), key = lambda x : x[1] )
    min_shifts_worker, min_shifts = min( number_of_shifts.items(), key = lambda x : x[1] )
    max_weighted_shifts_worker, max_weighted_shifts = max( number_of_weighted_shifts.items(), key = lambda x : x[1] )
    min_weighted_shifts_worker, min_weighted_shifts = min( number_of_weighted_shifts.items(), key = lambda x : x[1] )

    assigned_weekend_packages = [ str(worker) for ww, worker in enumerate(worker_list) if solver.Value(assigned_weekends[ww])]

    print(f"The worker with the largest number of shifts is {max_shifts_worker} with {max_shifts}.")
    print(f"The worker with the smallest number of shifts is {min_shifts_worker} with {min_shifts}.")
    print(f"The worker with the largest workload is {max_weighted_shifts_worker} with {max_weighted_shifts}. " +
          f"They get: {[ str(val) + 'x ' + key[1] for  key, val in number_of_shifts_per_workplace.items() if key[0] == max_weighted_shifts_worker]}")
    print(f"The worker with the smallest workload is {min_weighted_shifts_worker} with {min_weighted_shifts}. " +
          f"They get: {[ str(val) + 'x ' + key[1] for  key, val in number_of_shifts_per_workplace.items() if key[0] == min_weighted_shifts_worker]}")


    print("###########################")
    print(f"The total imbalance is {solver.Value(total_imbalance)}.")
    print(f"All imbalances are: {[solver.Value(imbalances[ww]) for ww in range(num_workers) ]}")

    print(f"The weekend packages were assigned to: {', '.join(assigned_weekend_packages)}.")

    ########################################################################
    # Write the output as a csv file.

    print(f"Writing output to schedule.csv...")
    with open('schedule.csv', 'w') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        for row in schedule_array:
            wr.writerow(row)

    ########################################################################


