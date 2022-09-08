import typing
import discord
from discord import message_command

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

    @commands.command()
    async def remindme(self, ctx, message: typing.Optional[discord.Message] = None, *, remindText):
        if message is not None:
            message = message.id
        await ctx.message.delete()
        timeString = find_reminder_time(remindText)
        dateTimeString = ctx.message.created_at
        reminder, result_message = Reminder.build_reminder(message, ctx.channel.id, ctx.guild.id, ctx.author.id, dateTimeString, timeString)
        if reminder is None:
            log.debug("Reminder not valid, returning")
            return await ctx.send(result_message)

        await GG.MDB['reminders'].update_one({"requested_date": reminder.requested_date, "authorId": reminder.authorId}, {"$set": reminder.to_dict()}, upsert=True)

        log.info(f"Reminder created for {reminder.message} by {reminder.authorId} on {get_datetime_string(reminder.target_date)}")
        bldr = await reminder.render_message_confirmation(self.bot, result_message)
        embed = EmbedWithAuthor(ctx)
        embed.description = ''.join(bldr)
        await ctx.send(embed=embed)

    @message_command(name="Remind me")
    async def remindme_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        await ctx.respond("When do you want to be reminded?", view=ReminderView(ctx.bot, message), ephemeral=True)


def setup(bot):
    log.info("[Cog] Reminder")
    bot.add_cog(ReminderCog(bot))
