"""Manage and send forecasts at their scheduled times.
Yes there are much better ways to do this, but I don't care.
"""

import asyncio
import datetime
import json
import pathlib
import sqlite3 as sl
from typing import Dict

# forecasts = {} # channel_id: {forecast_id: forecast}

DATABASE_FILENAME = "test.db"

# TODO(anyone): The Forecasts also need a TYPE / maybe just all args?
# But how would that be stored in the database...

# TODO: Get individual forecasts by id
# TODO: Get forecasts by server? channel? so they need a server id column as well?

class UnknownFrequencyError(Exception):
    pass

class Forecast:
    """Represents a scheduled forecast message.

    Attributes:
        freq: frequency of the message
        run_time: the time when the message should be sent
    """

    def __init__(self, id, channel_id, region, run_time, period):
        self.id = id
        self.channel_id = channel_id
        self.region = region
        # TODO: Convert run_time in minutes from database to tuple?
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

    def should_run(self) -> bool:
        """Checks if the forecast should be ran.
        
        Returns:
            A boolean if the forecast should have been ran or not, based on
            the calculated next run time of the message.
        """

        return self.next_run_time <= datetime.datetime.now()
    
    def calc_first_run_time(self) -> datetime.datetime:
        """Calculate when the forecast should next run.

        This calculates the first next time that matches
        the hours and minutes set from the forecast's run_time.

        Returns:
            A datetime object representing the datetime of the
            next run
        """

        # Create a run time with the corret hour and minute
        now = datetime.datetime.now()
        runtime = now.replace(hour = self.run_time // 60, minute = self.run_time % 60)

        # Make sure runtime is in the future
        while runtime < now:
            runtime += self.timedelta

        return runtime

    def update_next_run_time(self):
        """Sets the next run time of the forecast."""

        self.next_run_time += self.timedelta


class FakeContext:
    """Fake Discord message context object.
    
    The only method this object has is the send method,
    for use in triggering the weather command manually
    for the forecasts.
    """

    def __init__(self, channel):
        self.channel = channel

    async def send(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)


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


# def time_str_to_tuple(time_str):
#     """Converts a time string in the form X:Y to a tuple (X, Y)"""

#     return tuple(int(n) for n in time_str.split(':'))


def get_forecasts():
    # Return a list of all forecasts
    with DatabaseConnection() as conn:
        sql_select_all_query = "SELECT * FROM forecast"
        rows = conn.execute(sql_select_all_query).fetchall()
        return [Forecast(*row) for row in rows]


def add_forecast(channel_id, region, time, period):
    """Adds a forecast to the schedule.
    
    Args:
        channel_id: The discord channel ID to send the message too.
        freq: How often to send the message - one of hourly, daily, or weekly.
        time_str: Time string when to schedule the forecast, format X:Y.
        *args: All other arguments to pass to the weather command.
    Returns:
        The integer ID of the new forecast.    
    """

    # Validate the freq parameter
    # TODO(anyone): Do this in the discord command instead of here, and assume at this point it's already been validated?
    if freq not in ('hourly', 'daily', 'weekly'):
        raise UnknownFrequencyError(f"The frequency: '{freq}' is unknown, should be 'hourly', 'daily' or 'weekly'.")

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

    # TODO: Return forecast_id?
    # return forecast_id


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


# TODO: This
# async def send_forecast(channel, forecast, forecast_id):
#     """Sends a scheduled forcast message.

#     Args:
#         channel: The discord channel object where to send the message to.
#         forecast: The forecast object.
#         forecast_id: The ID of the forecast.
#     """

#     # TODO(anyone): just no.
#     from main import weather
    
#     ctx = FakeContext(channel)
#     await weather(ctx, *forecast.command_args)

#     forecast.update_next_run_time()


async def forecast_loop(client):
    """Constantly running loop that checks if a forecast needs to be sent."""
    
    await client.wait_until_ready()
    #add_forecast(400016596476887040, 'hourly', '15:41',  "today") # bot testing
    #add_forecast(829634118651478016, 'hourly', '15:41',  "today") # dm
    while not client.is_closed():
        await asyncio.sleep(30)

        # TODO: This
        # for channel_id, channel_forecasts in forecasts.items():
        #     for forecast_id, forecast in channel_forecasts.items():

        #         if forecast.should_run():
        #             channel = client.get_channel(channel_id)
        #             if channel == None:
        #                 channel = await client.fetch_channel(channel_id)
        #             await send_forecast(channel, forecast, forecast_id)

initialize_database()
