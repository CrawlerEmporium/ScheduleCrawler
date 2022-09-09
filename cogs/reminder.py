import datetime
import typing
import discord
from discord import message_command, Option, slash_command

from discord.ext import commands
from crawler_utilities.utils.embeds import EmbedWithAuthor
from dropdowns.Reminder import ReminderView
from utils.reminder.reminder import Reminder
from utils.reminder.utils import find_reminder_time, get_datetime_string

from utils import globals as GG

log = GG.log


class ReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="remindme")
    async def remindme(self, ctx, reminder: Option(str, "When do you want to be reminded?")):
        timeString = find_reminder_time(reminder)
        dateTimeString = datetime.datetime.utcnow()
        reminder, result_message = Reminder.build_reminder(None, ctx.interaction.channel_id, ctx.interaction.guild_id, ctx.interaction.user.id, dateTimeString, timeString)
        if reminder is None:
            log.debug("Reminder not valid, returning")
            return await ctx.respond(result_message)

        await GG.MDB['reminders'].update_one({"requested_date": reminder.requested_date, "authorId": reminder.authorId}, {"$set": reminder.to_dict()}, upsert=True)

        log.info(f"Reminder created by {reminder.authorId} on {get_datetime_string(reminder.target_date)}")
        bldr = await reminder.render_message_confirmation(self.bot, result_message)
        embed = EmbedWithAuthor(ctx)
        embed.description = ''.join(bldr)
        await ctx.respond(embed=embed)

    @message_command(name="Remind me")
    async def remindme_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.respond("When do you want to be reminded?", view=ReminderView(ctx.bot, message), ephemeral=True)


def setup(bot):
    log.info("[Cog] Reminder")
    bot.add_cog(ReminderCog(bot))
