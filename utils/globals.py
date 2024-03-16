import motor.motor_asyncio
import os
from crawler_utilities.handlers.logger import Logger

log = Logger("logs", "ScheduleCrawler", "ScheduleCrawler").logger

PREFIX = os.environ['PREFIX']
TOKEN = os.environ['TOKEN']
COGS = os.environ['COGS']
COGSEVENTS = os.environ['COGSEVENTS']
OWNER = int(os.environ['OWNER'])
MONGODB = os.environ['MONGODB']

BOT = 856591849825239090
PM_TRUE = True

MDB = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['schedulecrawler']
HELP = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['lookup']

def get_server_prefix(self, msg):
    return self.get_prefix(self, msg)[-1]
