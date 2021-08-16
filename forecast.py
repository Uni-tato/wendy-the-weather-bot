"""Manage and send forecasts at their scheduled times.
Yes there are much better ways to do this, but I don't care.
"""

import asyncio
import datetime
import json
import pathlib
import sqlite3 as sl
from typing import Dict

import weather

DATABASE_FILENAME = "test_forecasts.db"


class UnknownFrequencyError(Exception):
    pass


class ForecastNotFoundError(Exception):
    """Rasied when the forecast is not found."""


class Forecast:
    """Represents a scheduled forecast message.

    Attributes:
        id: Forecast ID of the forecast.
        server_id: The Discord server ID that the forecast is sent in.
        channel_id: The Discord channel ID where the forecast needs to be sent.
        region: The region of the forecast (Cities).
        frequency: How often the forecast should be sent, one of hourly, daily, or weekly.
        period: what period of time to show the weather for. One of now, today or triday.
        run_time: Time when the forecast will be sent in minutes since midnight.
        readout: how much information to give. One of standard, full, or quick.
        unit: Units to display the data in, one of metric or imperial.
        last_run_time: datetime object representing the last time the forecast was sent.
    """

    def __init__(self, id, server_id, channel_id, region, frequency, period, run_time, readout, unit, last_run_time):
        self.id = id
        self.server_id = server_id
        self.channel_id = channel_id
        self.region = region
        self.frequency = frequency
        self.period = period
        self.run_time = run_time
        self.readout = readout
        self.unit = unit
        self.last_run_time = last_run_time

        # If they're none, we're working with a temporary Forecast that doesn't have a scheduled time.
        # Therefore these literally don't matter (and would throw errors)
        if None not in (self.frequency, self.run_time, self.last_run_time):
            self.timedelta = Forecast.parse_frequency(self.frequency)
            self.next_run_time = self.last_run_time + self.timedelta

    @staticmethod
    def parse_frequency(frequency):
        if frequency == "hourly":
            return datetime.timedelta(hours = 1)
        elif frequency == "daily":
            return datetime.timedelta(days = 1)
        elif frequency == "weekly":
            return datetime.timedelta(weeks = 1)
        
        # TODO: probably should return something other than none

    def __repr__(self):
        return f"Forecast #{self.id} in {self.channel_id} for {self.region} at {self.run_time} (ran at {self.last_run_time})"

    def should_run(self) -> bool:
        """Checks if the forecast should be ran.
        
        Returns:
            A boolean if the forecast should have been ran or not, based on
            the calculated next run time of the message.
        """

        return self.next_run_time <= datetime.datetime.now()
    
    def update_run_time(self):
        """Sets the next run time of the forecast."""

        # TODO: If the period is hours, shouldn't this NOT replace hours?
        # Or... has incrementing the correction as we've done prevent that?
        corrected_last_run_time = self.last_run_time.replace(hour = self.run_time // 60, minute = self.run_time % 60)
        
        # Make sure runtime is in the future
        now = datetime.datetime.now()
        while corrected_last_run_time < now:
            corrected_last_run_time += self.timedelta
        
        # Aaaaand now make sure it's exactly one in the past
        while corrected_last_run_time > now:
            corrected_last_run_time -= self.timedelta

        edit_forecast(self.id, "lastRunTime", corrected_last_run_time)
        self.last_run_time = corrected_last_run_time
        self.next_run_time = self.last_run_time + self.timedelta


class DatabaseConnection:
    def __enter__(self):
        self.connection = sl.connect(
            DATABASE_FILENAME,
            detect_types=sl.PARSE_DECLTYPES | sl.PARSE_COLNAMES
        )
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
                server_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                region TINYTEXT NOT NULL,
                frequency TINYTEXT NOT NULL,
                period TINYTEXT NOT NULL,
                run_time INTEGER NOT NULL,
                readout TINYTEXT NOT NULL,
                unit TINYTEXT NOT NULL,
                lastRunTime timestamp NOT NULL
            );"""
        conn.execute(sql_create_forecasts_table)


def get_forecasts(server_id=None, channel_id=None):
    """Returns a list of all forecasts.
    
    Optionally, you can filter by all forecasts in a server
    or all forecasts in a certain channel.
    
    Optional Args:
        server_id: The discord server ID to filter by.
        channel_id: The discord channel ID to filter by.
    
    Returns:
        A list of forecasts.
    """

    if channel_id is not None:
        where_clause = " WHERE channel_id=?"
        data = (channel_id,)
    elif server_id is not None:
        where_clause = " WHERE server_id=?"
        data = (server_id,)
    else:
        where_clause = ""
        data = ()

    with DatabaseConnection() as conn:
        sql_select_all_query = "SELECT * FROM forecast" + where_clause
        rows = conn.execute(sql_select_all_query, data).fetchall()
        return [Forecast(*row) for row in rows]


def get_forecast(forecast_id):
    """Gets a single forecast object.
    
    Args:
        forecast_id: The ID of the forecast.

    Raises:
        ForecastNotFoundError: If there exists no forecast with the given ID.
        
    Returns:
        The forecast object with the same ID.
    """
    
    with DatabaseConnection() as conn:
        sql_get_query = "SELECT * FROM forecast WHERE forecast_id=?"
        row = conn.execute(sql_get_query, (forecast_id,)).fetchone()
        if row is None:
            raise ForecastNotFoundError(f"Forecast with ID {forecast_id} does not exist.")
        else:
            return Forecast(*row)


def add_forecast(server_id, channel_id, region, frequency, period, time, readout, unit):
    """Adds a forecast to the schedule.
    
    Args:
        server_id: The Discord server ID that the forecast is sent in.
        channel_id: The Discord channel ID where the forecast needs to be sent.
        region: The region of the forecast (Cities).
        frequency: How often the forecast should be sent, one of hourly, daily, or weekly.
        period: what period of time to show the weather for. One of now, today or triday.
        time: Time when the forecast will be sent in minutes since midnight.
        readout: how much information to give. One of standard, full, or quick.
        unit: Units to display the data in, one of metric or imperial.

    Returns:
        The integer ID of the new forecast.
    """

    data = (
        server_id,
        channel_id,
        region,
        frequency,
        period,
        time,
        readout,
        unit,
        datetime.datetime.now()
    )
    with DatabaseConnection() as conn:
        sql_insert_forecast = """
            INSERT INTO forecast (
                server_id,
                channel_id,
                region,
                frequency,
                period,
                run_time,
                readout,
                unit,
                lastRunTime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        conn.execute(sql_insert_forecast, data)

        return conn.lastrowid


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


async def forecast_loop(client):
    """Constantly running loop that checks if a forecast needs to be sent."""

    await client.wait_until_ready()

    while not client.is_closed():
        await asyncio.sleep(30)

        for forecast in get_forecasts():
            if forecast.should_run():
                await weather.send_weather(client, forecast)
                forecast.update_run_time()


initialize_database()
