"""Manage and send forecasts at their scheduled times.
Yes there are much better ways to do this, but I don't care.
"""

import asyncio
import datetime
import json
import pathlib
import sqlite3 as sl
from typing import Dict

DATABASE_FILENAME = "test_forecasts.db"

# TODO: Get individual forecasts by id
# TODO: Get forecasts by server? channel? so they need a server id column as well?

class UnknownFrequencyError(Exception):
    pass

class Forecast:
    """Represents a scheduled forecast message.

    Attributes:
        id: Forecast ID of the forecast.
        channel_id: The Discord channel ID where the forecast needs to be sent.
        region: The region of the forecast (Cities).
        run_time: The time when the message should be sent in minutes since midnight.
        period: How often the forecast should be sent, one of hourly, daily, or weekly.
    """

    def __init__(self, id, channel_id, region, frequency, period, run_time, readout, unit):
        self.id = id
        self.channel_id = channel_id
        self.region = region
        self.frequency = frequency
        self.period = period
        self.run_time = run_time
        self.readout = readout
        self.unit = unit

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
                frequency TINYTEXT NOT NULL,
                period TINYTEXT NOT NULL,
                run_time INTEGER NOT NULL,
                readout TINYTEXT NOT NULL,
                unit TINYTEXT NOT NULL
            );"""
        conn.execute(sql_create_forecasts_table)


def get_forecasts():
    """Returns a list of all forecasts."""

    with DatabaseConnection() as conn:
        sql_select_all_query = "SELECT * FROM forecast"
        rows = conn.execute(sql_select_all_query).fetchall()
        return [Forecast(*row) for row in rows]


def add_forecast(channel_id, region, frequency, period, time, readout, unit):
    """Adds a forecast to the schedule.
    
    Args:
        channel_id: The Discord channel ID where the forecast needs to be sent.
        region: The region of the forecast (Cities).
        frequency: How often the forecast should be sent, one of hourly, daily, or weekly.
        period: what period of time to show the weather for. One of now, today or triday.
        time: Time when the forecast will be sent in minutes since midnight.
        readout: how much information to give. One of standard, full, or quick.
        unit: Units to display the data in, one of metric or imperial.

    # Returns:
    #    The integer ID of the new forecast.
    """

    data = (
        channel_id,
        region,
        frequency,
        period,
        time,
        readout,
        unit,
    )
    with DatabaseConnection() as conn:
        sql_insert_forecast = """
            INSERT INTO forecast (
                channel_id,
                region,
                frequency,
                period,
                run_time,
                readout,
                unit
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        conn.execute(sql_insert_forecast, data)

    # TODO: Return forecast_id? A bit tricky because we don't actually have it...
    # return forecast_id


def edit_forecast(forecast_id, argument, value):
    """Changes a forecast argument.
    
    Args:
        forecast_id: The ID of the forecast whos argument to edit.
        argument: The argument name
        value: The new argument value
    """
    # TODO: This is very sketch and very sql injection prone, but
    # It just will not work any other way. idk where I can ask
    # for a better way to do this
    with DatabaseConnection() as conn:
        sql_edit_forecast = """
            UPDATE forecast SET {arg}=? WHERE forecast_id=?
        """.format(arg=argument)
        conn.execute(sql_edit_forecast, (value, forecast_id))


def remove_forecast(forecast_id):
    """Removes the forecast with the forecast id.
    
    Args:
        forecast_id: The ID of the forecast to be removed.

    Raises:
        Something.
    """

    with DatabaseConnection() as conn:
        sql_remove_forecast = """
            DELETE FROM forecast WHERE forecast_id=?
        """
        conn.execute(sql_remove_forecast, (forecast_id,))


async def send_forecast(client, forecast: Forecast):
    """Sends a scheduled forcast message.

    Args:
        client: The main Discord client.
        forecast: The forecast object.
    """

    # TODO(anyone): just no.
    from main import weather

    channel = client.get_channel(forecast.channel_id)
    if channel == None:
        channel = await client.fetch_channel(forecast.channel_id)
    ctx = FakeContext(channel)

    # TODO: different forecast type arguments
    # await weather(ctx, *forecast.command_args)
    # or alternatively:
    # await actual_send_forecast(Forecast)
    await weather(ctx)


async def forecast_loop(client):
    """Constantly running loop that checks if a forecast needs to be sent."""
    
    await client.wait_until_ready()
    #add_forecast(400016596476887040, 'hourly', '15:41',  "today") # bot testing
    #add_forecast(829634118651478016, 'hourly', '15:41',  "today") # dm
    while not client.is_closed():
        await asyncio.sleep(30)

        for forecast in get_forecasts():
            if forecast.should_run():
                await send_forecast(client, forecast)


initialize_database()
