import datetime
import discord
import time

from discord.ext import commands
from crawler_utilities.handlers import logger

log = logger.logger

def checkDays(date):
    now = date.fromtimestamp(time.time())
    diff = now - date
    days = diff.days
    return f"{days} {'day' if days == 1 else 'days'} ago"


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.monotonic()

    @commands.command(aliases=['stats', 'info'])
    async def botinfo(self, ctx):
        """Shows info about bot"""
        em = discord.Embed(color=discord.Color.green(), description="ScheduleCrawler, a bot for scheduling events and other cool stuff.")
        em.title = 'Bot Info'
        em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        em.add_field(name="Servers", value=str(len(ctx.bot.guilds)))
        total_members = sum(len(s.members) for s in self.bot.guilds)
        unique_members = set(self.bot.get_all_members())
        members = '%s total\n%s unique' % (total_members, len(unique_members))
        em.add_field(name='Members', value=members)
        em.add_field(name='Uptime', value=str(datetime.timedelta(seconds=round(time.monotonic() - self.start_time))))
        em.add_field(name="About",
                     value='A multipurpose bot made by LordDusk#0001.')
        em.set_footer(text=f"ScheduleCrawler {ctx.bot.version} | Powered by discord.py")
        await ctx.send(embed=em)

def setup(bot):
    log.info("[Cog] Loading Info...")
    bot.add_cog(Info(bot))
