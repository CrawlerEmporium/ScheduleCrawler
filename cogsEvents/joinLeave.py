import asyncio

import discord
from discord.ext import commands
from crawler_utilities.handlers import logger

log = logger.logger

TRACKER = 642346478915813423


class JoinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        bots = sum(1 for m in guild.members if m.bot)
        members = len(guild.members)
        ratio = bots / members
        if ratio >= 0.6 and members >= 20:
            log.info("Detected bot collection server ({}), ratio {}. Leaving.".format(guild.id, ratio))
            try:
                await guild.owner.send("Please do not add me to bot collection servers. "
                                       "Your server was flagged for having over 60% bots. "
                                       "If you believe this is an error, please PM the bot author.")
            except:
                pass
            await asyncio.sleep(members / 200)
            await guild.leave()
        else:
            await self.bot.change_presence(
                activity=discord.Game(f"with {len(self.bot.guilds)} servers | %help | v{self.bot.version}"),
                afk=True)

def setup(bot):
    log.info("[Event] Join and Leave Logging...")
    bot.add_cog(JoinLeave(bot))
