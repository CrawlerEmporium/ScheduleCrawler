import asyncio
import re
import random
import typing

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle
from crawler_utilities.utils.confirmation import BotConfirmation

from crawler_utilities.utils.functions import get_next_num, try_delete
from models.schedule import Schedule, ScheduleState, ScheduleException
from crawler_utilities.handlers import logger
from utils.functions import getDateSuffix, getChannel, getYMD, convertDateAndTimeToDateTime

log = logger.logger


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # listeners
    @commands.Cog.listener()
    async def on_button_click(self, res):
        member = await res.guild.fetch_member(res.user.id)
        scheduleId = -1
        if member is not None:
            update = False

            if res.custom_id.startswith("schedule_accept"):
                scheduleId = int(res.custom_id.split("schedule_accept ")[1])
                schedule = await Schedule.from_id(int(scheduleId), res.guild.id)
                await schedule.accept(res.user)
                update = True

            if res.custom_id.startswith("schedule_decline"):
                scheduleId = int(res.custom_id.split("schedule_decline ")[1])
                schedule = await Schedule.from_id(int(scheduleId), res.guild.id)
                await schedule.deny(res.user)
                update = True

            if res.custom_id.startswith("schedule_tentative"):
                scheduleId = int(res.custom_id.split("schedule_tentative ")[1])
                schedule = await Schedule.from_id(int(scheduleId), res.guild.id)
                await schedule.tentative(res.user)
                update = True

            if update:
                embed, components = await self.createScheduleEmbed(schedule)
                channel = await getChannel(self.bot, res.guild)
                message = await channel.fetch_message(schedule.msgId)
                await message.edit(embed=embed, components=components)
                await res.respond(type=6)
                update = False

    # commands
    @commands.group(invoke_without_command=True)
    async def schedule(self, ctx, *, message):
        await try_delete(ctx.message)
        try:
            dbChannel = await self.bot.mdb['channels'].find_one({"guildId": ctx.message.guild.id})
            if dbChannel is None:
                return await ctx.send(f"This server lacks a scheduling channel. Ask a staff member to run the ``%schedule channel`` command, to assign a channel to this server.")
            match = re.search(r"name:(.*) desc:(.*) date:(.*) time:(.*)", message)
            if not match:
                await ctx.send("Correct usage of this command is ``%schedule name:eventName desc:eventDescription date:DD/MM/YYYY time:0000-2359``\n\nIf you instead want to follow a wizard that leads you through step-by-step, use ``%schedule create``")
                return

            convertedDateTime = await convertDateAndTimeToDateTime(match.group(3), match.group(4))
            id = await get_next_num(self.bot.mdb['properties'], 'id')
            schedule = Schedule(int(id), -1, ctx.guild.id, ctx.message.author.display_name, match.group(1), match.group(2), False, convertedDateTime)

            embed, components = await self.createScheduleEmbed(schedule)
            channel = await getChannel(self.bot, ctx.message.guild)
            msg = await channel.send(embed=embed, components=components)
            schedule.msgId = msg.id
            upsert = True

        except IndexError:
            upsert = False
            await ctx.send("Failed creating the schedule. Please check your date and/or time input(s).")

        if upsert:
            await self.bot.mdb['schedule'].insert_one(schedule.to_dict())

    @schedule.command(name='channel')
    async def schedule_channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        await try_delete(ctx.message)
        if channel is not None:
            dbChannel = await self.bot.mdb['channels'].find_one({"guildId": ctx.message.guild.id, "channelId": channel.id})
            if dbChannel is None:
                await self.bot.mdb['channels'].insert_one({"guildId": ctx.message.guild.id, "channelId": channel.id})
                await ctx.send(f"<#{channel.id}> was assigned as Scheduling channel.")
            else:
                await ctx.send(f"You already have <#{channel.id}> assigned as Scheduling channel.")
        else:
            await ctx.send(f"You need to give me a channel to assign a scheduling channel.")

    @schedule.command(name='changeauthor')
    async def schedule_changeauthor(self, ctx, id: int = 0, author: typing.Optional[discord.Member] = None):
        await try_delete(ctx.message)
        if id == 0:
            await ctx.message.delete()
            return
        else:
            try:
                schedule = await Schedule.from_id(int(id), int(ctx.guild.id))
                ch = await getChannel(self.bot, ctx.guild)
                message = await ch.fetch_message(schedule.msgId)
                embed = message.embeds[0]
                embed.remove_field(0)
                embed.insert_field_at(0, name='Hosted by', value=f'{author.display_name}', inline=False)
                await message.edit(embed=embed)
                schedule.author = author.display_name
                await self.bot.mdb['schedule'].replace_one({"id": schedule.id}, schedule.to_dict())
            except ScheduleException as e:
                await ctx.send(e)

    @schedule.command(name='cancel')
    async def schedule_cancel(self, ctx, id: int = 0):
        await try_delete(ctx.message)
        if id == 0:
            return
        else:
            try:
                schedule = await Schedule.from_id(int(id), int(ctx.guild.id))
                confirmation = BotConfirmation(ctx, 0x012345)
                await confirmation.confirm(f"Are you sure you want to cancel {schedule.name} ({schedule.id})?")
                if confirmation.confirmed:
                    ch = await getChannel(self.bot, ctx.message.guild)
                    await ctx.send(f"{schedule.name} was canceled.")
                    message = await ch.fetch_message(schedule.msgId)
                    await message.delete()
                    schedule.notified = True
                    await self.bot.mdb['schedule'].replace_one({"id": schedule.id}, schedule.to_dict())
                    await asyncio.sleep(8)
                    await confirmation.quit()
                else:
                    await confirmation.quit()
            except ScheduleException as e:
                await ctx.send(e)

    @schedule.command(name='create')
    async def schedule_create(self, ctx):
        await try_delete(ctx.message)
        dbChannel = await self.bot.mdb['channels'].find_one({"guildId": ctx.message.guild.id})
        if dbChannel is None:
            return await ctx.send(f"This server lacks a scheduling channel. Ask a staff member to run the ``%schedule channel`` command, to assign a channel to this server.")

        schedule = Schedule()
        schedule.state = ScheduleState.NAME
        schedule.author = ctx.author.display_name
        schedule.guildId = ctx.guild.id
        schedule.notified = False

        date = None
        time = None
        message = await ctx.send(f"This wizard walks your through the steps of creating a scheduled event.\n"
                                 f"**You have 2 minutes per step.**\n\n"
                                 f"First, give me the title for the event.")
        await self.waitScheduleMessage(ctx, message, schedule, date, time)

    # methods
    async def waitScheduleMessage(self, ctx, message, schedule, date, time):
        def check(reply):
            return reply.author == ctx.message.author

        try:
            if schedule.state == ScheduleState.NAME:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DESC
                await message.edit(content=f"Now give me the description you want the event to have. Note that this can not exceed the 2000 characters.")
                schedule.name = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule, date, time)

            elif schedule.state == ScheduleState.DESC:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DATE
                await message.edit(content=f"This time I require the date of the event. This should be in the ``DD/MM/YYYY`` format, for example ``23/08/2019``\nNote the `/` between day, month, and year.")
                schedule.desc = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule, date, time)

            elif schedule.state == ScheduleState.DATE:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.TIME
                await message.edit(content=f"Now I want the starting time of the event. This is in the 24 hour military notation so anything from 0000 to 2359 will work.\n**Don't** use `:` just use the 4 digits.")
                date = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule, date, time)

            elif schedule.state == ScheduleState.TIME:
                reply = await ctx.bot.wait_for('message', timeout=120.0, check=check)
                schedule.state = ScheduleState.DONE
                time = reply.content
                await reply.delete()
                await self.waitScheduleMessage(ctx, message, schedule, date, time)

            elif schedule.state == ScheduleState.DONE:
                await message.delete()
                await self.sendScheduleEmbed(ctx, schedule, date, time)

        except asyncio.TimeoutError:
            msg = await ctx.send("Scheduled Event was not completed in time. Please try again.")
            await msg.delete(delay=15)
            await message.delete(delay=15)

    async def sendScheduleEmbed(self, ctx, schedule, date, time):
        try:
            convertedDateTime = await convertDateAndTimeToDateTime(date, time)
            id = await get_next_num(self.bot.mdb['properties'], 'id')
            schedule.id = int(id)
            schedule.dateTime = convertedDateTime

            embed, components = await self.createScheduleEmbed(schedule)
            channel = await getChannel(self.bot, ctx.message.guild)
            msg = await channel.send(embed=embed, components=components)
            schedule.msgId = msg.id
            upsert = True

        except IndexError:
            upsert = False
            await ctx.send("Failed creating the schedule. Please check your date and/or time input(s).")

        if upsert:
            await self.bot.mdb['schedule'].insert_one(schedule.to_dict())

    async def createScheduleEmbed(self, schedule: Schedule):
        embed = discord.Embed()
        embed.title = f"{schedule.name}"
        embed.description = f"{schedule.desc}"
        embed.add_field(name="Hosted by", value=f"{schedule.author}", inline=False)
        day, month, year = await getYMD(schedule.dateTime)
        daySuffix = getDateSuffix(day)
        time = schedule.dateTime.strftime('%H:%M')
        embed.add_field(name="When? (UTC)", value=f"{month} {day}{daySuffix}, {year} {time}", inline=False)

        users = await self.bot.mdb['scheduleSignUp'].find({'id': schedule.id}).to_list(length=None)
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
            acceptedString = ""
            acceptedString += "\n".join(accepted)
            if len(acceptedString) > 1024:
                acceptedString = f"A lot of people!\n\nUse %schedule people {schedule.id} to get a list of all users."

        if len(declines) > 0:
            declinedString = ""
            declinedString += "\n".join(declines)
            if len(declinedString) > 1024:
                declinedString = f"A lot of people!\n\nUse %schedule people {schedule.id} to get a list of all users."

        if len(tentative) > 0:
            tentativeString = ""
            tentativeString += "\n".join(tentative)
            if len(tentativeString) > 1024:
                tentativeString = f"A lot of people!\n\nUse %schedule people {schedule.id} to get a list of all users."

        embed.add_field(name="Accepted", value=f"{acceptedString}")
        embed.add_field(name="Declined", value=f"{declinedString}")
        embed.add_field(name="Tentative", value=f"{tentativeString}")

        embed.set_footer(text=f"Id: {schedule.id} • When? (local time)")
        embed.timestamp = schedule.dateTime

        components = [[Button(label="Accept", style=ButtonStyle.green, custom_id=f"schedule_accept {schedule.id}"),
                       Button(label="Decline", style=ButtonStyle.red, custom_id=f"schedule_decline {schedule.id}"),
                       Button(label="Tentative", style=ButtonStyle.blue, custom_id=f"schedule_tentative {schedule.id}")]]

        return embed, components


def setup(bot):
    log.info("[Cog] Loading Schedule...")
    bot.add_cog(ScheduleCog(bot))
