import discord
import motor.motor_asyncio

from os import listdir
from os.path import isfile, join
from discord.ext import commands
from utils import globals as GG

log = GG.log

MDB = motor.motor_asyncio.AsyncIOMotorClient(GG.MONGODB)['schedulecrawler']

SHARD_COUNT = 1
TESTING = True
defaultPrefix = GG.PREFIX if not TESTING else '*'
intents = discord.Intents().default()
intents.members = True
intents.message_content = True


async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or(defaultPrefix)(bot, message)
    guild_id = str(message.guild.id)
    if guild_id in bot.prefixes:
        gp = bot.prefixes.get(guild_id, defaultPrefix)
    else:  # load from db and cache
        gp_obj = await bot.mdb.prefixes.find_one({"guild_id": guild_id})
        if gp_obj is None:
            gp = defaultPrefix
        else:
            gp = gp_obj.get("prefix", defaultPrefix)
        bot.prefixes[guild_id] = gp
    return commands.when_mentioned_or(gp)(bot, message)


class Crawler(commands.AutoShardedBot):
    def __init__(self, prefix, help_command=None, **options):
        super(Crawler, self).__init__(prefix, help_command, **options)
        self.owner = None
        self.testing = TESTING
        self.state = "init"
        self.token = GG.TOKEN
        self.prefixes = dict()
        self.mdb = MDB
        self.version = 0
        self.tracking = 858336354520530984
        self.error = 858317984509591562
        self.defaultPrefix = GG.PREFIX
        self.port = 5003

    async def get_server_prefix(self, msg):
        return (await get_prefix(self, msg))[-1]

    async def launch_shards(self):
        if self.shard_count is None:
            recommended_shards, _ = await self.http.get_bot_gateway()
            if recommended_shards >= 96 and not recommended_shards % 16:
                # half, round up to nearest 16
                self.shard_count = recommended_shards // 2 + (16 - (recommended_shards // 2) % 16)
            else:
                self.shard_count = recommended_shards // 2
        log.info(f"Launching {self.shard_count} shards!")
        await super(Crawler, self).launch_shards()


bot = Crawler(prefix=get_prefix, intents=intents, case_insensitive=True, status=discord.Status.idle,
              description="A bot.", shard_count=SHARD_COUNT, testing=TESTING,
              activity=discord.Game(f"%help | Initializing..."))


@bot.event
async def on_ready():
    bot.version = "1.0.1"
    await bot.change_presence(activity=discord.Game(f"with {len(bot.guilds)} servers | %help | v{bot.version}"))
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


@bot.event
async def on_connect():
    await bot.sync_commands(force=True)
    bot.owner = await bot.fetch_user(GG.OWNER)
    print(f"OWNER: {bot.owner.name}")


@bot.event
async def on_resumed():
    log.info('resumed.')


def loadCogs():
    i = 0
    log.info("Loading Cogs...")
    for extension in [f.removesuffix('.py') for f in listdir(GG.COGS) if isfile(join(GG.COGS, f))]:
        try:
            bot.load_extension(GG.COGS + "." + extension)
        except Exception as e:
            print(e)
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    log.info("Loading Event Cogs...")
    for extension in [f.removesuffix('.py') for f in listdir("cogsEvents") if isfile(join("cogsEvents", f))]:
        try:
            bot.load_extension("cogsEvents" + "." + extension)
        except Exception as e:
            print(e)
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    log.info("Finished Loading All Cogs...")


def loadCrawlerUtilitiesCogs():
    cu_event_extensions = ["errors", "joinLeave"]
    cu_event_folder = "crawler_utilities.events"
    cu_cogs_extensions = ["flare"]
    cu_cogs_folder = "crawler_utilities.cogs"

    i = 0
    log.info("Loading Cogs...")
    for extension in cu_cogs_extensions:
        try:
            bot.load_extension(f"{cu_cogs_folder}.{extension}")
        except Exception as e:
            print(e)
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    log.info("Loading Event Cogs...")
    for extension in cu_event_extensions:
        try:
            bot.load_extension(f"{cu_event_folder}.{extension}")
        except Exception as e:
            print(e)
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    if i == 0:
        log.info("Finished Loading All Utility Cogs...")
    else:
        log.info(f"Finished Loading Utility Cogs with {i} errors...")


if __name__ == "__main__":
    bot.state = "run"
    loadCogs()
    loadCrawlerUtilitiesCogs()
    bot.run(bot.token)
