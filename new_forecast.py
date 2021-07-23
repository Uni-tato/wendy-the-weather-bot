
import datetime
import sqlite3 as sl

# from database import Database
DATABASE_FILENAME = "test.db"


class Forecast:
    def __init__(self, id, channel_id, region, run_time, period):
        self.id = id
        self.channel_id = channel_id
        self.region = region
        self.run_time = run_time
        self.period = period

        if self.period == "hourly":
            self.timedelta = datetime.timedelta(hours = 1)
        elif self.period == "daily":
            self.timedelta = datetime.timedelta(days = 1)
        elif self.period == "weekly":
            self.timedelta = datetime.timedelta(weeks = 1)

        self.next_run_time = self.calc_first_run_time()

    def __repr__(self):
        return f"Forecast #{self.id} in {self.channel_id} for {self.region} at {self.run_time}"

    def should_run(self):
        return self.next_run_time <= datetime.datetime.now()

    def calc_first_run_time(self):
        now = datetime.datetime.now()
        # Create a run time with the corret hour and minute:
        runtime = now.replace(hour = self.run_time // 60, minute = self.run_time % 60)

        # Make sure runtime is in the future:
        while runtime < now:
            runtime += self.timedelta

        return runtime
    
    def update_next_run_time(self):
        self.next_run_time += self.timedelta


class DatabaseConnection:
    def __enter__(self):
        self.connection = sl.connect(DATABASE_FILENAME)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.connection.commit()
        self.connection.close() 


def initialize_database():
    with DatabaseConnection() as conn:
        sql_create_forecasts_table = """
            CREATE TABLE IF NOT EXISTS forecast (
                forecast_id INTEGER PRIMARY KEY,
                channel_id BIGINT NOT NULL,
                region TINYTEXT NOT NULL,
                run_time INTEGER NOT NULL,
                period TINYTEXT NOT NULL
            );"""
        conn.execute(sql_create_forecasts_table)


def get_forecasts():
    # Return a list of all forecasts
    with DatabaseConnection() as conn:
        sql_select_all_query = "SELECT * FROM forecast"
        rows = conn.execute(sql_select_all_query).fetchall()
        return [Forecast(*row) for row in rows]


def add_forecast(channel_id, region, time, period):
    data = (
        channel_id,
        region,
        time,
        period
    )
    with DatabaseConnection() as conn:
        sql_insert_forecast = """
            INSERT INTO forecast (
                channel_id,
                region,
                run_time,
                period
            ) VALUES (?, ?, ?, ?);
        """
        conn.execute(sql_insert_forecast, data)


def remove_forecast(forecast_id):
    """Removes the forecast with the forecast id.
    
    Args:
        forecast_id: The ID of the forecast to be removed.

    Raises:
        Something.
    """
    # TODO(anyone): Raise error if it doesn't exist
    with DatabaseConnection() as conn:
        sql_remove_forecast = """
            DELETE FROM forecast WHERE forecast_id=?
        """
        conn.execute(sql_remove_forecast, (forecast_id,))

initialize_database()



print(get_forecasts())

add_forecast(
    channel_id=100,
    region="California",
    time=500,
    period="hourly"
)

remove_forecast(2)

print(get_forecasts())

# TODO: Get individual forecast
