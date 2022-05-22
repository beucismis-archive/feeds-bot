import time
import json
import feedparser
from pyrogram.errors import FloodWait
from pyrogram import __version__, Client
from src.utils import get_logger, Database
from apscheduler.schedulers.background import BackgroundScheduler


class Bot(Client):
    def __init__(self):
        with open("configs.json") as file:
            configs = json.load(file)

        super().__init__(
            name="feeds-bot",
            api_id=configs["bot"]["api_id"],
            api_hash=configs["bot"]["api_hash"],
            bot_token=configs["bot"]["bot_token"],
        )

        self.chat_id = configs["utils"]["chat_id"]
        self.check_interval = configs["utils"]["check_interval"]
        self.max_instances = configs["utils"]["max_instances"]
        self.feed_urls = configs["feed_urls"]

        self.database = Database()
        self.scheduler = BackgroundScheduler()
        self.logger = get_logger(__name__)

    def create_feed_checker(self, feed_url):
        def check_feed():
            feed = feedparser.parse(feed_url)
            entry = feed.entries[0]

            with self.database as db:
                link, last_post = db.get(feed_url)

            if entry.id != last_post:
                message = f"**{entry.title}**\n{entry.link}"

                try:
                    self.send_message(self.chat_id, message)

                    with self.database as db:
                        db.update(feed_url, entry.id)
                except FloodWait as exception:
                    self.logger.warning(f"Flood wait: {exception.x} seconds.")
                    time.sleep(exception.x)
                except Exception as exception:
                    print(exception)
            else:
                self.logger.info(f"Checked feed: {entry.id}")

        return check_feed

    def start(self):
        for feed_url in self.feed_urls:
            with self.database as db:
                if db.get(feed_url) == None:
                    db.update(feed_url, "*")

                if not len(db.get(feed_url)):
                    db.update(feed_url, "*")

        for feed_url in self.feed_urls:
            feed_checker = self.create_feed_checker(feed_url)

            self.scheduler.add_job(
                feed_checker,
                "interval",
                seconds=self.check_interval,
                max_instances=self.max_instances,
            )

        self.scheduler.start()
        super().start()

        me = self.get_me()
        self.logger.info(f"Bot is running! Pyrogram v{__version__}")

    def stop(self, *args):
        super().stop()
        self.logger.info("Bot is stopped!")
