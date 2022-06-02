import logging
import threading
import time
import requests
from db import Database
from config import Config
from opensea import OpenseaAPI

logging.basicConfig(
            format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                level=logging.DEBUG
                )
LOGGER = logging.getLogger('statsScrapper')

file_log = logging.FileHandler('/root/CGC/WorkieTemp/api/stats_scrapper.log')
file_log.setLevel(logging.DEBUG)
LOGGER.addHandler(file_log)

CONF=Config()

DB = Database(CONF.postgres())
OS_API = OpenseaAPI(CONF.opensea_api())


class Scrapper:
    def __init__(self, interval: float, db, opensea_api) -> None:
        self._running_guard: threading.Condition = threading.Condition()
        self._running: bool = True
        self._interval: float = interval
        self._db = db
        self._os_api = opensea_api

        self.do_thing()
        self._thread: threading.Thread = threading.Thread(target=self._run)

    def do_thing(self) -> None:
        """This method will be called periodically."""
        LOGGER.info("Starting scrapping")
        query = "SELECT project_id, name, opensea FROM collections;"
        records = self._db.get_rows(query)
        LOGGER.info(f'{records}')
        for row in records:
            LOGGER.info(f'Getting -> {row["name"]}')
            status_ok, stats = self._os_api.get_collection_stats(row['opensea'])

            if status_ok:
                if stats["floor_price"] is None:
                    floor = 'NULL'
                else:
                    floor = stats["floor_price"]
                get_last = f'''SELECT total_sales, total_volume FROM stats WHERE collection = {row["project_id"]} ORDER BY date DESC LIMIT 1;'''
                last_stats = self._db.get_rows(get_last)
                diff_volume = stats['total_volume'] - float(last_stats[0]['total_volume'])
                diff_sales = stats['total_sales'] - float(last_stats[0]['total_sales'])

                query = f'''INSERT INTO stats (collection, supply, sales, total_sales, owners, count, reports, floor, volume, total_volume, date) 
                VALUES ({row["project_id"]}, {stats["total_supply"]}, {diff_sales}, {stats["total_sales"]}, {stats["num_owners"]}, {stats["count"]}, {stats["num_reports"]}, {floor}, {diff_volume}, {stats["total_volume"]} ,current_timestamp)
                RETURNING stat_id;'''
                records = self._db.insert(query)
            #LOGGER.info(f"{query}")
            else:
                LOGGER.info("Not 200 :c")

        LOGGER.info("Scrapping finished")

    def trigger(self) -> None:
        """Force `do_thing` to be called immiedietely."""
        with self._running_guard:
            self._running_guard.notify_all()

    def is_running(self) -> None:
        with self._running_guard:
            return self._running

    def start(self) -> None:
        LOGGER.info('Scrapper started')
        self._thread.start()

    def stop(self) -> None:
        with self._running_guard:
            self._running = False
            self._running_guard.notify_all()
        self._thread.join(timeout=10.0)

    def _run(self) -> None:
        while True:
            try:
                with self._running_guard:
                    if not self._running:
                        break
                    self._running_guard.wait(timeout=self._interval)
                    if not self._running:
                        break
                self.do_thing()
            except:
                LOGGER.exception("do_thing failed")


def main() -> None:
    SCRAPPER: Scrapper = Scrapper(interval=60.0, db=DB, opensea_api=OS_API)
    SCRAPPER.start()

if __name__ == "__main__":
    main()


