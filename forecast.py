"""Manage and send forecasts at their scheduled times.

Yes there are much better ways to do this, but I don't care.
"""

# TODO(alex): need to create a load function, and make save/load functionality automatic

import asyncio
import datetime
import json
from typing import Dict

forecasts = {} # channel_id: {forecast_id: forecast}

class UnknownFrequencyError(Exception):
    pass

class Forecast:
    """Represents a scheduled forecast message.

    Attributes:
        freq: frequency of the message
        run_time: the time when the message should be sent
    """

    def __init__(self, freq: str, time_str: str, *args):
        self.freq = freq
        self.run_time = time_str_to_tuple(time_str)
        self.command_args = args

        self.next_run_time = self.calc_first_run_time()

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
        runtime = now.replace(hour = self.run_time[0], minute = self.run_time[1])

        # Make sure runtime is in the future
        timedelta = self.get_timedelta()
        while runtime < now:
            runtime += timedelta

        return runtime

    def update_next_run_time(self):
        """Sets the next run time of the forecast."""

        self.next_run_time += self.get_timedelta()

    def get_timedelta(self) -> datetime.timedelta:
        """Calculates the time delta from the frequency string of the forecast.
        
        Returns:
            A timedelta object of the set length.
        """

        if self.freq == "hourly":
            timedelta = datetime.timedelta(hours = 1)
        elif self.freq == "daily":
            timedelta = datetime.timedelta(days = 1)
        elif self.freq == "weekly":
            timedelta = datetime.timedelta(weeks = 1)

        return timedelta

    def get_save_data(self) -> Dict:
        """Returns a dict that fully describes the forecast.
        
        The purpose of this method is for saving the returned dict.
        
        Returns:
            A saveable dict.
        """

        return {
                "freq": self.freq,
                "run_time": self.run_time,
                "command_args": self.command_args
            }


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


def time_str_to_tuple(time_str):
    """Converts a time string in the form X:Y to a tuple (X, Y)"""

    return tuple(int(n) for n in time_str.split(':'))


def add_forecast(channel_id, freq, time_str, *args):
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

    if channel_id in forecasts:
        # If the channel exists in the forecast dict, reserve a unique forecast ID for the new forecast.
        # Checks with all other forecasts in the same channel.
        int_keys = set(filter(lambda key: type(key) == int, forecasts[channel_id].keys()))
        forecast_id = (max(int_keys)+1) if len(int_keys) else 1
    else:
        # If the channel does not exist in the forecasts dict, create it and assign a forecast ID of 1.
        forecasts[channel_id] = dict()
        forecast_id = 1

    # Add the new forecast to forecasts dict
    forecasts[channel_id][forecast_id] = Forecast(freq, time_str, *args)

    return forecast_id


async def send_forecast(channel, forecast, forecast_id):
    """Sends a scheduled forcast message.

    Args:
        channel: The discord channel object where to send the message to.
        forecast: The forecast object.
        forecast_id: The ID of the forecast.
    """

    # TODO(anyone): just no.
    from main import weather
    
    ctx = FakeContext(channel)
    await weather(ctx, *forecast.command_args)

    forecast.update_next_run_time()


def save():
    """Saves the forecast dict to disk."""

    data = dict()
    for channel_id, channel_forecasts in forecasts.items():
        channel_data = dict()
        for forecast_id, forecast in channel_forecasts.items():
            channel_data[forecast_id] = forecast.get_save_data()
        data[channel_id] = channel_data
        
    time_str = datetime.datetime.now().strftime("%d-%m-%Y %H-%M")
    with open(f"saved_forecasts\\{time_str}.json", 'w') as file:
        save_data = json.dump(data, file)


def load(file_name = None):
    """Loads a forecast dict from disk."""

    print("Loading forecasts")
    if file_name == None:
        file_name = input("Please input name of file:")
    with open(f"saved_forecasts\\{file_name}.json", 'r') as file:
        data = json.load(file)
    for channel_id, channel_forecasts in data.items():
        forecasts[channel_id] = dict()
        for forecast_id, forecast_data in channel_forecasts.items():
            forecasts[channel_id][forecast_id] = Forecast(forecast_data['freq'],
                                                          forecast_data['run_time'],
                                                          *forecast_data['command_args'])


async def forecast_loop(client):
    """Constantly running loop that checks if a forecast needs to be sent."""
    
    await client.wait_until_ready()
    #add_forecast(400016596476887040, 'hourly', '15:41',  "today") # bot testing
    #add_forecast(829634118651478016, 'hourly', '15:41',  "today") # dm
    while not client.is_closed():
        await asyncio.sleep(30)

        for channel_id, channel_forecasts in forecasts.items():
            for forecast_id, forecast in channel_forecasts.items():

                if forecast.should_run():
                    channel = client.get_channel(channel_id)
                    if channel == None:
                        channel = await client.fetch_channel(channel_id)
                    await send_forecast(channel, forecast, forecast_id)
