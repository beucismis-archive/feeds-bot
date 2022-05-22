import sqlite3
import logging
from logging import FileHandler


class Database:
    def __init__(self, filename="feeds.db", table_name="Feeds"):
        self.filename = filename
        self.table_name = table_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        if self.filename:
            self._open(self.filename)

        self._create_table(self.table_name)

        return self

    def __exit__(self, *args, **kwargs):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def _open(self, filename):
        try:
            self.conn = sqlite3.connect(filename)
            self.cursor = self.conn.cursor()
        except Exception as exception:
            raise exception

    def _create_table(self, table_name):
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (link TEXT PRIMARY KEY, last_post TEXT)"
        )

    def get(self, link):
        self.cursor.execute(f"SELECT * FROM {self.table_name} WHERE link=?", (link,))
        row = self.cursor.fetchone()

        return row

    def update(self, link, last_post):
        self.cursor.execute(
            f"INSERT OR REPLACE INTO {self.table_name} (link, last_post) VALUES (?, ?)",
            (link, last_post),
        )


class Handler(FileHandler):

    LEVEL = logging.INFO

    def __init__(self):
        FileHandler.__init__(self, "feed-bot.log")
        self.encoding = "UTF-8"

        datefmt = "%Y-%m-%d %H:%M:%S"
        fmt = "[%(asctime)s][%(levelname)s] - %(message)s"
        self.setFormatter(logging.Formatter(fmt, datefmt))


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(Handler.LEVEL)
    logger.addHandler(Handler())

    return logger
