import asyncio
import re
import datetime
import random
import typing
from textwrap import wrap

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle
from crawler_utilities.utils.confirmation import BotConfirmation
from datetime import datetime

from models.schedule import ScheduleModel, ScheduleState
from crawler_utilities.handlers import logger
from utils.functions import getDateSuffix, getChannel, getYMD

log = logger.logger


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # listeners
    @commands.Cog.listener()
    async def on_button_click(self, res):
        member = await res.guild.fetch_member(res.user.id)
        if member is not None:
            update = False

            if res.custom_id.startswith("schedule_accept"):
                scheduleId = res.custom_id.split("schedule_accept ")[1]
                schedule = await self.bot.mdb['schedule'].find_one({'id': f'{int(scheduleId)}'})
                await self.bot.mdb['scheduleSignUp'].update_one({'user': f'{res.user.id}', 'id': int(schedule["id"])}, {"$set": {"type": 1}}, upsert=True)
                update = True

            if res.custom_id.startswith("schedule_decline"):
                scheduleId = res.custom_id.split("schedule_decline ")[1]
                schedule = await self.bot.mdb['schedule'].find_one({'id': f'{int(scheduleId)}'})
                await self.bot.mdb['scheduleSignUp'].update_one({'user': f'{res.user.id}', 'id': int(schedule["id"])}, {"$set": {"type": -1}}, upsert=True)
                update = True

            if res.custom_id.startswith("schedule_tentative"):
                scheduleId = res.custom_id.split("schedule_tentative ")[1]
                schedule = await self.bot.mdb['schedule'].find_one({'id': f'{int(scheduleId)}'})
                await self.bot.mdb['scheduleSignUp'].update_one({'user': f'{res.user.id}', 'id': int(schedule["id"])}, {"$set": {"type": 0}}, upsert=True)
                update = True

            if update:
                embed, components = await self.createScheduleEmbed(scheduleId, schedule['author'], schedule['dateTime'], schedule['desc'], schedule['name'])
                channel = await getChannel(self.bot, res.guild)
                message = await channel.fetch_message(int(schedule['msgId']))
                await message.edit(embed=embed, components=components)
                await res.respond(type=6)
                update = False

    # commands
    @commands.group(invoke_without_command=True)
    async def schedule(self, ctx, *, message):
        match = re.search(r"name:(.*) desc:(.*) date:(.*) time:(.*)", message)
        if not match:
            await ctx.send("Correct usage of this command is ``%schedule name:eventName desc:eventDescription date:eventDate time:eventStartTime``")
            return
        name = match.group(1)
        desc = match.group(2)
        date = match.group(3)
        time = match.group(4)

        dateTime, datesplit = await self.getStartingTime(date, time)
        id = await self.get_next_schedule_num()
        embed, components = await self.createScheduleEmbed(id, ctx.author.display_name, dateTime, desc, name)
        channel = await getChannel(self.bot, ctx.message.guild)
        msg = await channel.send(embed=embed, components=components)
        await self.bot.mdb['schedule'].insert_one({"id": f"{int(id)}", "msgId": f"{int(msg.id)}", "guildId": f"{int(ctx.guild.id)}", "author": f"{ctx.author}", "name": f"{name}", "desc": f"{desc}", "dateTime": f"{dateTime}", "notified": False})
        await ctx.message.delete()

    @schedule.command(name='channel')
    async def schedule_channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if channel is not None:
            dbChannel = await self.bot.mdb['channels'].find_one({"guildId": ctx.message.guild.id, "channelId": channel.id})
            print(dbChannel)
            if dbChannel is None:
                await self.bot.mdb['channels'].insert_one({"guildId": ctx.message.guild.id, "channelId": channel.id})
                await ctx.send(f"<#{channel.id}> was assigned as Scheduling channel.")
            else:
                await ctx.send(f"You already have <#{channel.id}> assigned as Scheduling channel.")
        else:
            await ctx.send(f"You need to give me a channel to assign a scheduling channel.")

    @schedule.command(name='author')
    async def schedule_author(self, ctx, author: typing.Optional[discord.Member] = None):
        schedule = ScheduleModel()
        if author is not None:
            schedule.author = author.display_name
        await ctx.message.delete()
        schedule.state = ScheduleState.NAME
        message = await ctx.send(f"This wizard walks your through the steps of creating a scheduled event. You have 60 seconds per step.\n\nFirst, give me the title for the event.")
        await self.waitScheduleMessage(ctx, message, schedule)

    @schedule.command(name='changeauthor')
    async def schedule_changeauthor(self, ctx, id: int = 0, author: typing.Optional[discord.Member] = None):
        if id == 0:
            await ctx.message.delete()
            return
        else:
            msg = await self.bot.mdb['schedule'].find_one({'id': str(id)})
            if msg is not None:
                ch = await getChannel(self.bot, ctx)
                message = await ch.fetch_message(int(msg['msgId']))
                embed = message.embeds[0]
                embed.remove_field(0)
                embed.insert_field_at(0, name='Hosted by', value=f'{author.display_name}', inline=False)
                await message.edit(embed=embed)
                await ctx.message.delete()
            else:
                await ctx.message.delete()
                return

    @schedule.command(name='cancel')
    async def schedule_cancel(self, ctx, id: int = 0):
        if id == 0:
            await ctx.message.delete()
            return
        else:
            schedule = await self.bot.mdb['schedule'].find_one({'id': str(id)})
            if schedule is not None:
                await ctx.message.delete()
                confirmation = BotConfirmation(ctx, 0x012345)
                await confirmation.confirm(f"Are you sure you want to cancel {schedule['name']} ({schedule['id']})?")
                if confirmation.confirmed:
                    ch = await getChannel(self.bot, ctx.message.guild)
                    await ctx.send(f"{schedule['name']} was canceled.")
                    message = await ch.fetch_message(int(schedule['msgId']))
                    await message.delete()
                    schedule['notified'] += True
                    await self.bot.mdb['schedule'].replace_one({"id": f"{str(schedule['id'])}"}, schedule)
                    await asyncio.sleep(8)
                    await confirmation.quit()
                else:
                    await confirmation.quit()
            else:
                await ctx.message.delete()
                return

    @schedule.command(name='create')
    async def schedule_create(self, ctx):
        schedule = ScheduleModel()
        await ctx.message.delete()
        schedule.state = ScheduleState.NAME
        schedule.author = ctx.author.display_name
        message = await ctx.send(f"This wizard walks your through the steps of creating a scheduled event.\n"
                                 f"**You have 2 minutes per step.**\n\n"
                                 f"First, give me the title for the event.")
        await self.waitScheduleMessage(ctx, message, schedule)

    # methods
    async def waitScheduleMessage(self, ctx, message, schedule):
        def check(reply):
            return reply.author == ctx.message.author

        try:
            if schedule.state == ScheduleState.NAME:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DESC
                await message.edit(content=f"Now give me the description you want the event to have. Note that this can not exceed the 2000 characters.")
                schedule.name = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule)

            elif schedule.state == ScheduleState.DESC:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DATE
                await message.edit(content=f"This time I require the date of the event. This should be in the ``DD/MM/YYYY`` format, for example ``23/08/2019``\nNote the `/` between day, month, and year.")
                schedule.desc = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule)

            elif schedule.state == ScheduleState.DATE:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.TIME
                await message.edit(content=f"Now I want the starting time of the event. This is in the 24 hour military notation so anything from 0000 to 2359 will work.\n**Don't** use `:` just use the 4 digits.")
                schedule.date = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule)

            elif schedule.state == ScheduleState.TIME:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DONE
                schedule.endTime = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule)

            elif schedule.state == ScheduleState.DONE:
                await message.delete()
                await self.sendScheduleEmbed(schedule, ctx)

        except asyncio.TimeoutError:
            msg = await ctx.send("Scheduled Event was not completed in time. Please try again.")
            await msg.delete(delay=15)
            await message.delete(delay=15)

    async def sendScheduleEmbed(self, schedule, ctx):
        id = None
        msg = None
        dateTime = None
        try:
            dateTime, datesplit = await self.getStartingTime(schedule.date, schedule.time)
            id = await self.get_next_schedule_num()
            embed, components = await self.createScheduleEmbed(id, schedule.author, dateTime, schedule.desc, schedule.name)
            channel = await getChannel(self.bot, ctx.message.guild)
            msg = await channel.send(embed=msg, components=components)
            upsert = True

        except IndexError:
            upsert = False
            await ctx.send("Failed creating the schedule. Please check your date and/or time input(s).")

        if upsert:
            await self.bot.mdb['schedule'].insert_one({"id": f"{int(id)}", "msgId": f"{int(msg.id)}", "guildId": f"{int(ctx.guild.id)}", "author": f"{schedule.author}", "name": f"{schedule.name}", "desc": f"{schedule.desc}", "dateTime": f"{dateTime}", "notified": False})

    async def createScheduleEmbed(self, id, author, dateTime, desc, name):
        embed = discord.Embed()
        embed.title = f"{name}"
        embed.colour = random.randint(0, 0xffffff)
        embed.description = f"{desc}"
        embed.add_field(name="Hosted by", value=f"{author}", inline=False)
        day, month, year = await getYMD(dateTime)
        daySuffix = getDateSuffix(day)
        try:
            time = dateTime.strftime('%H:%M')
        except AttributeError:
            split = dateTime.split(" ")
            times = split[1].split(":")
            time = f"{times[0]}:{times[1]}"
            dateTime = datetime.strptime(dateTime, '%Y-%m-%d %H:%M:%S')
        embed.add_field(name="When? (UTC)", value=f"{month} {day}{daySuffix}, {year} {time}", inline=False)

        users = await self.bot.mdb['scheduleSignUp'].find({'id': f'{int(id)}'}).to_list(length=None)
        accepted = []
        declines = []
        tentative = []
        for x in users:
            user = await self.bot.fetch_user(int(x['user']))
            if x['type'] == 1:
                accepted.append(user.display_name)
            if x['type'] == -1:
                declines.append(user.display_name)
            if x['type'] == 0:
                tentative.append(user.display_name)

        acceptedString = "**-**"
        declinedString = "**-**"
        tentativeString = "**-**"

        if len(accepted) > 0:
            acceptedString = ">>>\n"
            acceptedString += "\n".join(accepted)
            if len(acceptedString) > 1024:
                acceptedString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."

        if len(declines) > 0:
            declinedString = ">>>\n"
            declinedString += "\n".join(declines)
            if len(declinedString) > 1024:
                declinedString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."

        if len(tentative) > 0:
            tentativeString = ">>>\n"
            tentativeString += "\n".join(tentative)
            if len(tentativeString) > 1024:
                tentativeString = f"A lot of people!\n\nUse %schedule people {id} to get a list of all users."


        embed.add_field(name="Accepted", value=f"{acceptedString}")
        embed.add_field(name="Declined", value=f"{declinedString}")
        embed.add_field(name="Tentative", value=f"{tentativeString}")

        embed.set_footer(text=f"Id: {id} • When? (local time)")
        embed.timestamp = dateTime

        components = [[Button(label="Accept", style=ButtonStyle.green, custom_id=f"schedule_accept {id}"),
                       Button(label="Decline", style=ButtonStyle.red, custom_id=f"schedule_decline {id}"),
                       Button(label="Tentative", style=ButtonStyle.blue, custom_id=f"schedule_tentative {id}")]]

        return embed, components

    async def get_next_schedule_num(self):
        reportNum = await self.bot.mdb['properties'].find_one({'key': 'id'})
        num = reportNum['amount'] + 1
        reportNum['amount'] += 1
        await self.bot.mdb['properties'].replace_one({"key": 'id'}, reportNum)
        return f"{num}"

    async def getStartingTime(self, date, time):
        datesplit = date.split('/')
        datestring = f"{datesplit[2]}-{datesplit[1]}-{datesplit[0]}"
        timewarp = wrap(time, 2)
        datestring += f" {timewarp[0]}:{timewarp[1]}"
        dateTime = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M')
        return dateTime, datesplit


def setup(bot):
    log.info("[Cog] Loading Schedule...")
    bot.add_cog(Schedule(bot))
