import time
import json
import feedparser
from pyrogram.errors import FloodWait
from pyrogram import __version__, Client
from src.utils import get_logger, Database
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Bot(Client):
    def __init__(self):
        with open("configs.json") as file:
            configs = json.load(file)

        super().__init__(
            name="bot",
            api_id=configs["bot"]["api_id"],
            api_hash=configs["bot"]["api_hash"],
            bot_token=configs["bot"]["bot_token"],
        )

        self.chat_id = configs["utils"]["chat_id"]
        self.check_interval = configs["utils"]["check_interval"]
        self.feed_urls = configs["feed_urls"]

        self.database = Database()
        self.scheduler = AsyncIOScheduler()
        self.logger = get_logger(__name__)

    async def create_feed_checker(self, feed_url):
        async def check_feed():
            feed = feedparser.parse(feed_url)
            entry = feed.entries[0]
            link, last_post = await self.database.get(feed_url)

            if entry.link != last_post:
                try:
                    message = f"{entry.title}\n{entry.link}"
                except AttributeError:
                    message = f"{entry.link}"

                try:
                    await self.send_message(self.chat_id, message)
                    await self.database.update(feed_url, entry.link)
                    self.logger.info(f"New message: {entry.link}")

                except FloodWait as exception:
                    self.logger.warning(f"Flood wait: {exception.x} seconds")
                    time.sleep(exception.x)

                except Exception as exception:
                    self.logger.error(exception)
            else:
                self.logger.info(f"Checked feed: {feed_url}")

        return check_feed

    async def start(self):
        await self.database.create_table()

        for feed_url in self.feed_urls:
            data = await self.database.get(feed_url)

            # TODO: Check the same links

            if data == None:
                await self.database.update(feed_url, "*")
                self.logger.info(f"Added feed: {feed_url}")

        for feed_url in self.feed_urls:
            feed_checker = await self.create_feed_checker(feed_url)

            self.scheduler.add_job(
                feed_checker,
                "interval",
                misfire_grace_time=300,
                seconds=self.check_interval,
            )

        self.scheduler.start()
        await super().start()

        me = await self.get_me()
        self.logger.info(f"Bot is running! Pyrogram v{__version__}")

    async def stop(self, *args):
        await super().stop()
        self.logger.info("Bot is stopped!")
