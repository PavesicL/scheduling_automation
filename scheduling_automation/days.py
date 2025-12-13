"""
Contains functions used to generate a list of days of the month,
and a class that adds new functionality to datetime.date.
"""

from datetime import date, timedelta
import calendar
import holidays

class Day(date):
    """
    The class inherits everything from date.
    Adds the check if the date is a holiday.
    """

    _month_repr ={
        1 : "JAN",
        2 : "FEB",
        3 : "MAR",
        4 : "APR",
        5 : "MAY",
        6 : "JUN",
        7 : "JUL",
        8 : "AUG",
        9 : "SEP",
        10 : "OCT",
        11 : "NOV",
        12 : "DEC",
    }

    def __new__(cls, year, month, day):
        return super().__new__(cls, year, month, day)

    @property
    def is_holiday(self):
        return self in holidays.Slovenia(years=self.year)

    @property
    def is_weekend(self):
        return self.isoweekday() in [ 6, 7 ]

    @property
    def is_workday(self):
        return not (self.is_holiday or self.is_weekend)

    def __str__(self) -> str:
        """
        Should be 22.DEC for the 22nd of December,
        and 25.dec for the 25th of December and non-working days.
        """
        if self.is_workday:
            month_str = _month_repr[self.month].upper()
        else:
            month_str = _month_repr[self.month].lower()
        return f"{self.day}.{month_str}"


def generate_day_list(start_date : date, end_date : date) -> list[Day]:
    """
    Generates the list of days between the start and end dates.

    Arguments:
        start_date : date
            The starting date.
        end_date : date
            The end date. Is included in the interval.
    Returns:
        list[Day]
        A list of Day objects for the given month.
    """

    all_dates = [start_date + timedelta(days=ii) for ii in range((end_date - start_date).days + 1)]
    day_list = [ Day(dd.year, dd.month, dd.day) for dd in all_dates ]

    return day_list
