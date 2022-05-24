import logging
import aiosqlite
from logging import FileHandler


class Database:
    def __init__(self, filename="feeds.db", table_name="Feeds"):
        self.filename = filename
        self.table_name = table_name

    async def create_table(self):
        async with aiosqlite.connect(self.filename) as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table_name} (link TEXT PRIMARY KEY, last_entry TEXT)"
            )
            await db.commit()

    async def get(self, link):
        async with aiosqlite.connect(self.filename) as db:
            cursor = await db.execute(
                f"SELECT * FROM {self.table_name} WHERE link=?", (link,)
            )
            row = await cursor.fetchone()

        return row

    async def update(self, link, last_entry):
        async with aiosqlite.connect(self.filename) as db:
            await db.execute(
                f"INSERT OR REPLACE INTO {self.table_name} (link, last_entry) VALUES (?, ?)",
                (link, last_entry),
            )
            await db.commit()


class Handler(FileHandler):

    LEVEL = logging.INFO

    def __init__(self):
        FileHandler.__init__(self, "bot.log")
        self.encoding = "UTF-8"

        datefmt = "%Y-%m-%d %H:%M:%S"
        fmt = "[%(asctime)s][%(levelname)s] - %(message)s"
        self.setFormatter(logging.Formatter(fmt, datefmt))


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(Handler.LEVEL)
    logger.addHandler(Handler())

    return logger
