"""
Contains the Worker class.
"""

# These are the workplaces that a Worker can be assigned to.
# The code assumes that they are ordered alphabetically, and all uppercase.
ALL_WORKPLACES = [ "NZV", "POPS", "PORODNA", "TX" ]

class Worker:
    """
    A worker is an object containing the information
    about each person: their name, work date preferences,
    etc.
    """

    def __init__(self, name, surname):
        self.name = name
        self.surname = surname

    @property
    def workplaces(self):
        """
        A list of workplaces this Worker can work at.
        """
        return self._workplaces

    @workplaces.setter
    def workplaces(self, value : list[str]):
        # enforce the workplaces to be upper case
        value = [ x.upper() for x in value ]

        # Check if the workplaces are recognized.
        if any([ x not in ALL_WORKPLACES for x in value ]):
            raise Exception(f"Unrecognized workplace in {value}.")
        self._workplaces = value


    @property
    def work_dates(self):
        """
        A boolean list, False means that the Worker cannnot work on that day.
        """
        return self._work_dates

    @work_dates.setter
    def work_dates(self, value : list[bool]):
        self._work_dates = value


    @property
    def weekend_package(self):
        """
        Whether the Worker wants to work a weekend_package.
        Can be +1 (wants), 0 (does not care), -1 (does not want).
        """
        return self._weekend_package

    @weekend_package.setter
    def weekend_package(self, value : int):
        self._weekend_package = value


    @property
    def special_request(self):
        """
        A special request is a string they can type into the google doc.
        Currently ignored.
        """
        return self._special_request

    @special_request.setter
    def special_request(self, value : str):
        self._special_request = value


    def __repr__(self):
        return self.name + " " + self.surname
