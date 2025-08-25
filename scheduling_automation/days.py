"""
Contains functions used to generate a list of days of the month,
and a class that adds new functionality to datetime.date.
"""

from datetime import date
import calendar
import holidays

class Day(date):
    """
    The class inherits everything from date.
    Adds the check if the date is a holiday.
    """
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


def generate_day_list(month : int, year : int) -> list[Day]:
    """
    Generates the list of days in a month.

    Arguments:
        month : int
            Which month (1-12) the list is for.
        year : int
            Which year the list is for.

    Returns:
        list[Day]
        A list of Day objects for the given month.
    """

    num_days = calendar.monthrange(year, month)[1]
    day_list = [ Day(year, month, ii + 1) for ii in range(num_days) ]
    return day_list
