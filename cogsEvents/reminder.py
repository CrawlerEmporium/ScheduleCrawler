import asyncio
import discord
import random
import utils.globals as GG

from datetime import datetime
from crawler_utilities.utils.functions import discord_trim
from utils.reminder.reminder import Reminder

log = GG.log


async def ReminderCycler(bot):
    await bot.wait_until_ready()
    while True:
        try:
            now = datetime.utcnow()

            reminders = await GG.MDB['reminders'].find({"reminded": False}).to_list(length=None)
            for reminder in reminders:
                _id = reminder['_id']
                del reminder['_id']
                reminder = Reminder.from_dict(reminder)
                dateTime = datetime.fromisoformat(str(reminder.target_date))
                if now.strftime('%D') == dateTime.strftime('%D'):
                    nowM = (int(now.strftime('%H')) * 60) + int(now.strftime('%M'))
                    dateM = (int(dateTime.strftime('%H')) * 60) + int(dateTime.strftime('%M'))
                    if abs(nowM - dateM) <= 1:
                        bldr = await reminder.render_notification(bot)
                        guild = await bot.fetch_guild(reminder.guildId)
                        channel = await bot.fetch_channel(reminder.channelId)
                        user = await guild.fetch_member(reminder.authorId)

                        embed = discord.Embed()
                        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
                        embed.colour = random.randint(0, 0xffffff)
                        embed.description = ''.join(bldr)
                        embed.title = f"Reminder here for {str(user)}!"
                        await user.send(content=user.mention, embed=embed)

                        reminder.reminded = True
                        await GG.MDB['reminders'].replace_one({"_id": _id}, reminder.to_dict())
        except Exception as e:
            errorLogging = await bot.fetch_channel(bot.error)
            await errorLogging.send(f"<@95486109852631040> - A Reminder for {reminder.authorId} failed. - Traceback:\n")
            tb = discord_trim(e)
            for x in tb:
                await errorLogging.send(x)
        await asyncio.sleep(60)


def setup(bot):
    log.info("[Event] Reminder Cycling...")
    bot.loop.create_task(ReminderCycler(bot))
