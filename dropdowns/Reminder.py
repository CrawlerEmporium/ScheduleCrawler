import random
import discord
import utils.globals as GG

from discord import SelectOption, Interaction

from utils.reminder.reminder import Reminder
from utils.reminder.utils import find_reminder_time, get_datetime_string

log = GG.log


class ReminderDropdown(discord.ui.Select):
    def __init__(self, bot: discord.Bot, message):
        self.bot = bot
        self.message = message

        options = [
            SelectOption(label="15 minutes"),
            SelectOption(label="30 minutes"),
            SelectOption(label="1 hour"),
            SelectOption(label="2 hours"),
            SelectOption(label="4 hours"),
            SelectOption(label="12 hours"),
            SelectOption(label="1 day")
        ]

        super().__init__(
            placeholder="Select a time below",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        timeString = find_reminder_time(self.values[0])
        dateTimeString = interaction.message.created_at
        messageId = self.message.id
        channelId = interaction.channel_id
        guildId = interaction.guild_id
        userId = interaction.user.id
        reminder, result_message = Reminder.build_reminder(messageId, channelId, guildId, userId, dateTimeString, timeString)
        if reminder is None:
            log.debug("Reminder not valid, returning")
            return await interaction.response.send_message(result_message, ephemeral=True)

        await GG.MDB['reminders'].update_one({"requested_date": reminder.requested_date, "authorId": reminder.authorId}, {"$set": reminder.to_dict()}, upsert=True)

        log.info(f"Reminder created for {reminder.message} by {reminder.authorId} on {get_datetime_string(reminder.target_date)}")
        bldr = await reminder.render_message_confirmation(self.bot, result_message)
        embed = discord.Embed()
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.colour = random.randint(0, 0xffffff)
        embed.description = ''.join(bldr)

        return await interaction.response.send_message(embed=embed, ephemeral=True)


class ReminderView(discord.ui.View):
    def __init__(self, bot: discord.Bot, message):
        self.bot = bot
        self.message = message
        super().__init__()
        self.add_item(ReminderDropdown(self.bot, message))
