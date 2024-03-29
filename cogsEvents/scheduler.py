import asyncio

import discord
from datetime import datetime

from crawler_utilities.utils.functions import discord_trim

import utils.globals as GG
from models.schedule import Schedule

log = GG.log


async def loadScheduler(bot):
    await bot.wait_until_ready()
    while True:
        schedules = await bot.mdb['schedule'].find({"notified": False}).to_list(length=None)
        for schedule in schedules:
            schedule = await Schedule.from_id(schedule['id'], schedule['guildId'])
            try:
                now = datetime.utcnow()
                dateTime = datetime.fromisoformat(schedule.dateTime)
                if now.strftime('%D') == dateTime.strftime('%D'):
                    nowM = (int(now.strftime('%H')) * 60) + int(now.strftime('%M'))
                    dateM = (int(dateTime.strftime('%H')) * 60) + int(dateTime.strftime('%M'))
                    if abs(nowM - dateM) <= 5:
                        channel = await bot.mdb['init'].find_one({"guildId": schedule.guildId})
                        ch = bot.get_channel(int(channel['channelId']))
                        accepted = []
                        tentatived = []
                        users = await bot.mdb['scheduleSignUp'].find({"id": schedule.id}).to_list(length=None)
                        guild = bot.get_guild(schedule.guildId)
                        await guild.chunk()
                        for user in users:
                            if user['type'] == 1:
                                guildUser = guild.get_member(user['user'])
                                if guildUser is not None:
                                    accepted.append(f"{guildUser.mention}")
                                else:
                                    accepted.append(f"<@{user['user']}>")
                            if user['type'] == 0:
                                guildUser = guild.get_member(user['user'])
                                if guildUser is not None:
                                    tentatived.append(f"{guildUser.mention}")
                                else:
                                    tentatived.append(f"{user['user']}")

                        embed = await schedule.createNotificationEmbed(accepted, tentatived)

                        msg = await ch.send(f"{' '.join(accepted)}", embed=embed)
                        await msg.edit(content='', embed=embed)

                        schedule.notified = True
                        await bot.mdb['schedule'].replace_one({"id": schedule.id}, schedule.to_dict())
                        try:
                            message = await ch.fetch_message(schedule.msgId)
                            await message.delete()
                        except discord.errors.NotFound:
                            await ch.send("I tried deleting the corresponding signup message, but it appears to be already deleted.", delete_after=15)
            except Exception as e:
                errorLogging = await bot.fetch_channel(bot.error)
                await errorLogging.send(f"<@95486109852631040> - {schedule.title} Errored - ID: {schedule.id} - Traceback:\n")
                tb = discord_trim(e)
                for x in tb:
                    await errorLogging.send(x)
        await asyncio.sleep(60)


def setup(bot):
    log.info("[Event] Scheduling...")
    bot.loop.create_task(loadScheduler(bot))
