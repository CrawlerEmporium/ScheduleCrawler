import datetime
import discord
import time
from discord import ButtonStyle

from discord.ext import commands
from discord.ui import Button

from crawler_utilities.utils.embeds import EmbedWithAuthor
from crawler_utilities.utils.functions import try_delete
from utils import checks
from utils import globals as GG

log = GG.log

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
        em.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
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

    @commands.command()
    async def support(self, ctx):
        em = EmbedWithAuthor(ctx)
        em.title = 'Support Server'
        em.description = "For technical support for ScheduleCrawler, join the Crawler Emporium discord [here](https://discord.gg/HEY6BWj)!\n" \
                         "There you can ask questions about the bot, make feature requests, report issues and/or bugs (please include any error messages), learn about my other Crawler bots, and share with other crawler bot users!\n\n" \
                         "[Check the Website](https://crawleremporium.com) for even more information.\n\n" \
                         "To add premium features to the bot, [<:Patreon:855754853153505280> Join the Patreon](https://www.patreon.com/LordDusk), or if you'd rather show just appreciation [tip the Developer a <:Kofi:855758703772958751> here](https://ko-fi.com/5ecrawler)."
        serverEmoji = self.bot.get_emoji(int("<:5e:603932658820448267>".split(":")[2].replace(">", "")))
        patreonEmoji = self.bot.get_emoji(int("<:Patreon:855754853153505280>".split(":")[2].replace(">", "")))
        kofiEmoji = self.bot.get_emoji(int("<:Kofi:855758703772958751>".split(":")[2].replace(">", "")))
        components = [[Button(label="Discord", style=ButtonStyle.url, emoji=serverEmoji, url="https://discord.gg/HEY6BWj"),
                       Button(label="Website", style=ButtonStyle.url, url="https://www.crawleremporium.com"),
                       Button(label="Patreon", style=ButtonStyle.url, emoji=patreonEmoji, url="https://www.patreon.com/LordDusk"),
                       Button(label="Buy me a coffee", style=ButtonStyle.url, emoji=kofiEmoji, url="https://ko-fi.com/5ecrawler")]]
        await ctx.send(embed=em, components=components)

    @commands.command()
    async def invite(self, ctx):
        em = EmbedWithAuthor(ctx)
        em.title = 'Invite Me!'
        em.description = "Hi, you can easily invite me to your own server by following [this link](https://discordapp.com/oauth2/authorize?client_id=856591849825239090&scope=bot&permissions=268774400)!\n\n" \
                         "Of the 6 permissions asked, 3 are optional and 3 mandatory for optimal usage of the capabilities of the bot.\n\n" \
                         "" \
                         "**Mandatory:**\n" \
                         "__Manage Messages__ - This allows the bot to remove messages from other users.\n" \
                         "__Manage Roles__ - On initialization it creates a special role, you can remove this permission afterwards.\n" \
                         "__Send Messages__ - Obvious enough, it needs to be able to send messages, so it can post the events.\n\n" \
                         "" \
                         "**Optional:**\n" \
                         "__View Channels__ - To be able to post to channels, it has to see the channels. But I guess you can take it off.\n" \
                         "__Read Message History__ - Otherwise it can't react to your commands.\n" \
                         "__Use External Emojis__ - Some features use emojis that come from the support server.\n"
        await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def prefix(self, ctx, prefix: str = None):
        """Sets the bot's prefix for this server.

        You must have Manage Server permissions or a role called "Bot Admin" to use this command.

        Forgot the prefix? Reset it with "@5eCrawler#2771 prefix !".
        """
        await try_delete(ctx.message)
        guild_id = str(ctx.guild.id)
        if prefix is None:
            current_prefix = await self.bot.get_server_prefix(ctx.message)
            return await ctx.send(f"My current prefix is: `{current_prefix}`")

        self.bot.prefixes[guild_id] = prefix

        await self.bot.mdb.prefixes.update_one(
            {"guild_id": guild_id},
            {"$set": {"prefix": prefix}},
            upsert=True
        )

        await ctx.send("Prefix set to `{}` for this server.".format(prefix))

def setup(bot):
    log.info("[Cog] Loading Info...")
    bot.add_cog(Info(bot))
