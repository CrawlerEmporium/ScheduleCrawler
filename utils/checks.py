from discord.ext import commands


def is_coordinator():
    async def predicate(ctx):
        server = await ctx.bot.mdb['init'].find_one({"guildId": ctx.message.guild.id})
        roleId = server['channelId']
        try:
            if ctx.author.roles is not None:
                if roleId in ctx.author.roles:
                    return True

            if ctx.author.id == ctx.guild.owner_id:
                return True

            if ctx.guild.get_member(ctx.author.id).guild_permissions.administrator:
                return True

        except Exception:
            pass

        return False

    return commands.check(predicate)
