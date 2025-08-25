"""
The parsing functions to collect the date from the excell file.
The file should be a tab-separated format (.tsv).
We assume the following format:
- The first line is a header, and is skipped.
- Each row has the following entries (in this order):
    - date      : datestamp, ignored, not parsed.
    - surname   : string
    - name      : string
    - workplaces : string, specifies at which workplaces the worker can work.
        Is a string of comma separated words, like: "POPs, Tx, NZV"
    - work dates : columns 4:-4 are strings indicating which dates the worker
        can work. Can be "" for yes, and "Ne" if they cannot work on that date.
    - weekend_package : whether they prefer or not the weekend package. Can be
        "Ne" if they do not want it, "Da" if they do, or "" or "Vseeno mi je" if
        they do not care.
    - weekend_12h : ignored, not parsed.
    - current_workplace : ignored, not parsed.
    - special request : a string asking for special accommodations.
        Parsed, but not used anywhere.
"""

import csv
from .worker import Worker

def parse_input(filename : str):
    """
    Parses the input file.
    Has to be a tab-separated file (.tsv), exported from google docs.
    Makes assumptions on the input order.

    Arguments
        filename : str
            The path to the file.

    Return
        list[Worker]
            A list of worker objects. These contain the info about the workers,
            including their wishes.
    """

    with open(filename, newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter='\t', quotechar='|')

        # skip the first line
        next(filereader, None)

        worker_list = []
        for row in filereader:

            date = row[0] # ignored
            surname = row[1]
            name = row[2]
            workplaces = row[3]
            work_dates = row[4:-4]
            weekend_package = row[-4]
            weekend_12h = row[-3] # this is irrelevant and ignored
            current_workplace = row[-2] # this is irrelevant and ignored
            special_requests = row[-1]

            worker = Worker(name=name, surname=surname)
            worker.workplaces = parse_workplaces(workplaces)
            worker.work_dates = parse_work_dates(work_dates)
            worker.weekend_package = parse_weekend_package(weekend_package)
            worker.special_request = special_requests

            worker_list.append(worker)

    return worker_list

def parse_workplaces(workplaces : str) -> list[str]:
    """
    Workplaces are given as one string seprated by commas: "POPs, Porodna".
    Split the string and enforce upper case.

    Input:
        workplaces : str
            The string of workplaces from the google doc.

    Returns:
        list[str]
            Alphabetically ordered list of workplaces.
    """
    return sorted([ x.strip().upper() for x in workplaces.split(",") ])

def parse_work_dates(work_dates : list[str]) -> list[bool]:
    """
    Parses the work dates into a boolean list.

    Input:
        work_dates : list[str]
            The list of work dates.
            "Ne" means cannot work, empty string means can work.

    Returns:
        list[bool]
            Boolean list of work dates.
    """
    return [ x != "Ne" for x in work_dates]

def parse_weekend_package(weekend_package : str) -> int:
    """
    Input:
        weekend_package : str
            Can be "Ne", "Da", "Vseeno mi je" or empty.
            Empty is the same as "Vseeno"
    Returns:
        int
            -1 if does not want, +1 for wants, 0 if they do not care.
    """
    if weekend_package == "Ne":
        return -1
    elif weekend_package == "Da":
        return 1
    elif weekend_package in ["Vseeno mi je", ""]:
        return 0
    else:
        raise Exception(f"Unknown weekend package: {weekend_package}.")
