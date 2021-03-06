import motor.motor_asyncio
from environs import Env

env = Env()
env.read_env()

PREFIX = env('PREFIX')
TOKEN = env('TOKEN')
COGS = env('COGS')
COGSEVENTS = env('COGSEVENTS')
OWNER = int(env('OWNER'))
MONGODB = env('MONGODB')

BOT = 856591849825239090
PM_TRUE = True

MDB = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['schedulecrawler']
HELP = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['lookup']

def get_server_prefix(self, msg):
    return self.get_prefix(self, msg)[-1]
