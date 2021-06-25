from enum import Enum


class ScheduleState(Enum):
    NEW = 0
    NAME = 1
    DESC = 2
    DATE = 3
    TIME = 4
    DONE = 5


class ScheduleModel:
    def __init__(self, author="", name="", desc="", date="", time=""):
        self.author = author
        self.name = name
        self.desc = desc
        self.date = date
        self.time = time
        self.state = ScheduleState.NEW
