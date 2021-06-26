import logging
import datetime
from textwrap import wrap
from datetime import datetime

import discord
from crawler_utilities.utils.functions import fakeField

log = logging.getLogger(__name__)


def getDateSuffix(day):
    day = int(day)
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return suffix


async def getChannel(bot, guild):
    guild = await bot.mdb['channels'].find_one({"guildId": guild.id})
    channel = await bot.fetch_channel(guild['channelId'])
    return channel


async def getYMD(dateTime):
    year = dateTime.strftime('%Y')
    month = dateTime.strftime('%B')
    day = dateTime.strftime('%d')
    return day, month, year


async def convertDateAndTimeToDateTime(date, time):
    datesplit = date.split('/')
    datestring = f"{datesplit[2]}-{datesplit[1]}-{datesplit[0]}"
    timewarp = wrap(time, 2)
    datestring += f" {timewarp[0]}:{timewarp[1]}"
    dateTime = datetime.strptime(datestring, '%Y-%m-%d %H:%M')
    return dateTime
