import asyncio

import discord
from datetime import datetime

from crawler_utilities.utils.functions import discord_trim

from crawler_utilities.handlers import logger
from utils.functions import createNotificationEmbed

log = logger.logger


async def loadScheduler(bot):
    await bot.wait_until_ready()
    while True:
        schedules = await bot.mdb['schedule'].find({"notified": False}).to_list(length=None)
        for schedule in schedules:
            try:
                now = datetime.utcnow()
                dateTime = datetime.fromisoformat(schedule['dateTime'])
                if now.strftime('%D') == dateTime.strftime('%D'):
                    nowM = (int(now.strftime('%H')) * 60) + int(now.strftime('%M'))
                    dateM = (int(dateTime.strftime('%H')) * 60) + int(dateTime.strftime('%M'))
                    if abs(nowM - dateM) <= 5:
                        channel = await bot.mdb['channels'].find_one({"guildId": int(schedule['guildId'])})
                        ch = bot.get_channel(int(channel['channelId']))
                        accepted = []
                        tentatived = []
                        users = await bot.mdb['scheduleSignUp'].find({"id": int(schedule['id'])}).to_list(length=None)
                        guild = bot.get_guild(int(schedule['guildId']))
                        await guild.chunk()
                        for user in users:
                            if user['type'] == 1:
                                guildUser = guild.get_member(int(user['user']))
                                if guildUser is not None:
                                    accepted.append(f"{guildUser.mention}")
                                else:
                                    accepted.append(f"<@{user['user']}>")
                            if user['type'] == 0:
                                guildUser = guild.get_member(int(user['user']))
                                if guildUser is not None:
                                    tentatived.append(f"{guildUser.mention}")
                                else:
                                    tentatived.append(f"{user['user']}")

                        embed = await createNotificationEmbed(schedule, dateTime, accepted, tentatived)

                        msg = await ch.send(f"{' '.join(accepted)}", embed=embed)
                        await msg.edit(content='', embed=embed)

                        schedule['notified'] += True
                        await bot.mdb['schedule'].replace_one({"id": int(schedule['id'])}, schedule)
                        try:
                            message = await ch.fetch_message(int(schedule['msgId']))
                            await message.delete()
                        except discord.errors.NotFound:
                            await ch.send("I tried to delete the corresponding signup message, but can no longer find it.", delete_after=15)
            except Exception as e:
                errorLogging = bot.get_channel(858317984509591562)
                await errorLogging.send(f"<@95486109852631040> - {schedule['name']} Errored - ID: {schedule['id']} - Traceback:\n")
                for o in discord_trim(e):
                    await errorLogging.send(o)
        await asyncio.sleep(60)


def setup(bot):
    log.info("[Event] Scheduling...")
    bot.loop.create_task(loadScheduler(bot))
