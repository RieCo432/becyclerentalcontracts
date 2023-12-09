from datetime import datetime


class concurrencyEntry:
    def __init__(self, id, entry_datetime: datetime, concurrency_limit: int):
        self.id = id
        self.afterTime = entry_datetime.time()
        self.limit = concurrency_limit

    def get_mongodb_filter_and_data(self):
        afterTime_datetime = datetime(year=1, month=1, day=1, hour=self.afterTime.hour, minute=self.afterTime.minute)
        return {"_id": self.id}, {"afterTime": afterTime_datetime, "limit": self.limit}