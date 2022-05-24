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

        self.logger = get_logger(__name__)

        super().__init__(
            name="bot",
            api_id=configs["bot"]["api_id"],
            api_hash=configs["bot"]["api_hash"],
            bot_token=configs["bot"]["bot_token"],
        )

        self.chat_id = configs["utils"]["chat_id"]
        self.check_interval = configs["utils"]["check_interval"]
        self.misfire_grace_time = configs["utils"]["misfire_grace_time"]
        self.feed_urls = configs["feed_urls"]

        self.database = Database()

        self.jobs = []
        self.scheduler = AsyncIOScheduler()

    async def create_feed_checker(self, feed_url):
        async def check_feed():
            global link, last_entry

            feed = feedparser.parse(feed_url)
            entry = feed.entries[0]

            try:
                link, last_entry = await self.database.get(feed_url)
            except TypeError:
                last_entry = entry.link
                self.logger.error(f"Database not unpack...")

            if entry.link != last_entry:
                try:
                    message = f"{entry.title}\n{entry.link}"
                except AttributeError:
                    message = f"{entry.link}"

                try:
                    if last_entry != "?":
                        await self.send_message(self.chat_id, message)
                        self.logger.info(f"New message: {entry.link}")

                    await self.database.update(feed_url, entry.link)

                except FloodWait as exception:
                    self.logger.warning(f"Flood wait: {exception.value} seconds")
                    await asyncio.sleep(exception.value)

                except Exception as exception:
                    self.logger.error(exception)
            else:
                self.logger.info(f"Checked feed: {feed_url}")

        return check_feed

    async def start(self):
        await self.database.create_table()

        for feed_url in self.feed_urls:
            data = await self.database.get(feed_url)

            if data == None or not feed_url in data:
                feed = feedparser.parse(feed_url)

                if len(feed.entries):
                    await self.database.update(feed_url, "?")
                    self.logger.info(f"Added feed: {feed_url}")
                else:
                    self.feed_urls.remove(feed_url)
                    self.logger.error(f"Feed invalid: {feed_url}")

        for feed_url in self.feed_urls:
            feed_checker = await self.create_feed_checker(feed_url)

            self.scheduler.add_job(
                feed_checker,
                "interval",
                minutes=self.check_interval,
                misfire_grace_time=self.misfire_grace_time * 60,
            )

        self.scheduler.start()
        self.logger.info("Scheduler running...")
        await super().start()
        self.logger.info(f"Bot running! Pyrogram v{__version__}")

    async def stop(self, *args):
        await super().stop()
        self.logger.info("Bot stopped!")
