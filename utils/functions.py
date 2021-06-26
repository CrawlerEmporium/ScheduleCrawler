import logging
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
    try:
        year = dateTime.strftime('%Y')
        month = dateTime.strftime('%B')
        day = dateTime.strftime('%d')
    except AttributeError:
        split = dateTime.split(" ")
        dates = split[0].split("-")
        year = dates[0]
        month = dates[1]
        day = dates[2]
    return day, month, year


async def createNotificationEmbed(schedule, dateTime, accepted, tentatived):
    embed = discord.Embed()
    embed.title = f"Event starting soon: {schedule['name']}"
    embed.description = f"{schedule['desc']}"
    embed.set_footer(text=f"People that have signed up to either attend, or be tentatively available are shown above.\nTentative people are not pinged.")
    embed.add_field(name="Hosted by", value=f"{schedule['author']}", inline=False)
    day, month, year = await getYMD(schedule['dateTime'])
    daySuffix = getDateSuffix(day)
    try:
        time = dateTime.strftime('%H:%M')
    except AttributeError:
        split = dateTime.split(" ")
        times = split[1].split(":")
        time = f"{times[0]}:{times[1]}"
        dateTime = datetime.strptime(dateTime, '%Y-%m-%d %H:%M:%S')
    embed.add_field(name="When? (UTC)", value=f"{month} {day}{daySuffix}, {year} {time}", inline=False)
    acceptedString = "**-**"
    tentativeString = "**-**"
    if len(accepted) > 0:
        acceptedString = ""
        acceptedString += "\n".join(accepted)
        if len(acceptedString) > 1024:
            acceptedString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."
    if len(tentatived) > 0:
        tentativeString = ""
        tentativeString += "\n".join(tentatived)
        if len(tentativeString) > 1024:
            tentativeString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."
    embed.add_field(name="Accepted", value=f"{acceptedString}")
    fakeField(embed)
    embed.add_field(name="Tentative", value=f"{tentativeString}")
    return embed