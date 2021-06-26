import datetime
from enum import Enum

import discord

from crawler_utilities.utils.functions import fakeField

import utils.globals as GG
from utils.functions import getYMD, getDateSuffix


class ScheduleState(Enum):
    NEW = 0
    NAME = 1
    DESC = 2
    DATE = 3
    TIME = 4
    DONE = 5


class Schedule:
    schedules = GG.MDB['schedule']
    signups = GG.MDB['scheduleSignUp']

    def __init__(self, id: int = -1, msgId: int = -1, guildId: int = -1, author: str = "", name: str = "", desc: str = "", notified: bool = False, dateTime: datetime = ""):
        self.id = id
        self.msgId = msgId
        self.guildId = guildId
        self.author = author
        self.name = name
        self.desc = desc
        self.dateTime = dateTime
        self.notified = notified
        self.state = ScheduleState.NEW

    @classmethod
    async def new(cls, id, msgId, guildId, author, name, desc, dateTime, notified):
        inst = cls(id, msgId, guildId, author, name, desc, dateTime, notified)
        return inst

    @classmethod
    def from_dict(cls, schedule_dict):
        return cls(**schedule_dict)

    def to_dict(self):
        return {"id": self.id, "msgId": self.msgId, "guildId": self.guildId, "author": self.author, "name": self.name,
                "desc": self.desc, "notified": self.notified, "dateTime": self.dateTime}

    @classmethod
    async def from_id(cls, id, guildId):
        schedule = await cls.schedules.find_one({"id": int(id), "guildId": int(guildId)})
        if schedule is not None:
            del schedule['_id']
            try:
                return cls.from_dict(schedule)
            except KeyError:
                raise ScheduleException(f"Schedule `{id}` not found.")
        else:
            raise ScheduleException(f"Schedule `{id}` not found.")

    async def accept(self, user):
        await self.signups.update_one({'user': user.id, 'id': self.id}, {"$set": {"type": 1}}, upsert=True)

    async def deny(self, user):
        await self.signups.update_one({'user': user.id, 'id': self.id}, {"$set": {"type": -1}}, upsert=True)

    async def tentative(self, user):
        await self.signups.update_one({'user': user.id, 'id': self.id}, {"$set": {"type": 0}}, upsert=True)

    async def createNotificationEmbed(self, accepted, tentatived):
        embed = discord.Embed()
        embed.title = f"Event starting soon: {self.name}"
        embed.description = f"{self.desc}"
        embed.set_footer(text=f"People that have signed up to either attend, or be tentatively available are shown above.\nTentative people are not pinged.")
        embed.add_field(name="Hosted by", value=f"{self.author}", inline=False)

        day, month, year = await getYMD(self.dateTime)
        daySuffix = getDateSuffix(day)
        time = self.dateTime.strftime('%H:%M')
        embed.add_field(name="When? (UTC)", value=f"{month} {day}{daySuffix}, {year} {time}", inline=False)

        acceptedString = "**-**"
        if len(accepted) > 0:
            acceptedString = ""
            acceptedString += "\n".join(accepted)
            if len(acceptedString) > 1024:
                acceptedString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."

        tentativeString = "**-**"
        if len(tentatived) > 0:
            tentativeString = ""
            tentativeString += "\n".join(tentatived)
            if len(tentativeString) > 1024:
                tentativeString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."

        embed.add_field(name="Accepted", value=f"{acceptedString}")
        fakeField(embed)
        embed.add_field(name="Tentative", value=f"{tentativeString}")
        return embed


class ScheduleException(Exception):
    pass
