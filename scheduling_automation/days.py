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


def generate_day_list(month : int, year : int, next_month_days : int) -> list[Day]:
    """
    Generates the list of days in a month.

    Arguments:
        month : int
            Which month (1-12) the list is for.
        year : int
            Which year the list is for.
        next_month_days : int
            Sometimes the schedule should include a few
            days of the next month as well (like New Year's).
            We append this many days of the next month to the day_list.

    Returns:
        list[Day]
        A list of Day objects for the given month.
    """

    num_days = calendar.monthrange(year, month)[1]
    day_list = [ Day(year, month, ii + 1) for ii in range(num_days) ]

    if next_month_days > 0:
        # append the next month
        next_month = (month + 1)%12
        next_year = year + 1 if month == 12 else year

        day_list += [ Day(next_year, next_month, ii + 1) for ii in range(next_month_days) ]

    return day_list
