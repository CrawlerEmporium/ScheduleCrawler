import discord
from discord.ext import commands


def _check_permissions(ctx, perms):
    ch = ctx.channel
    author = ctx.author
    try:
        resolved = ch.permissions_for(author)
    except AttributeError:
        resolved = None
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def _role_or_permissions(ctx, role_filter, **perms):
    if _check_permissions(ctx, perms):
        return True

    ch = ctx.message.channel
    author = ctx.message.author
    if isinstance(ch, discord.abc.PrivateChannel):
        return False  # can't have roles in PMs

    try:
        role = discord.utils.find(role_filter, author.roles)
    except:
        return False
    return role is not None


def admin_or_permissions(**perms):
    def predicate(ctx):
        admin_role = "Bot Admin"
        if _role_or_permissions(ctx, lambda r: r.name.lower() == admin_role.lower(), **perms):
            return True
        raise commands.CheckFailure(
            f"You require a role named Bot Admin or these permissions to run this command: {', '.join(perms)}")

    return commands.check(predicate)


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
