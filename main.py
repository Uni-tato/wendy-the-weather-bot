#!/usr/bin/env python3
"""Main wendy the weather bot script.

This script shouldn't be executed with any arguments, however
config.py needs to be correctly setup for it to function properly.
Check the README for more info on the propper configuration.
"""

import asyncio
import requests

import discord
from discord.ext import commands

import config
import forecast as forecast_manager
import weather as weather_info

client = commands.Bot(command_prefix=config.PREFIX)


@client.command()
async def test(ctx):
    forecast_manager.save()


@client.command()
async def ping(ctx):
    """Pong!"""
    await ctx.send("Pong!")


@client.command()
async def weather(ctx, *args):
    """Summarizes the weather for you

    Defaults to the current weather, but can also tell you
    the weather at a different time, eg: `weather today`
    will give you a simple summary of the weather over the day.
    """

    when = args[0] if len(args) else "now"
    if when == 'now':
        w_data = [weather_info.now_summary()]
    elif when == 'today':
        w_data = weather_info.today_summary_generator()
    else:
        await ctx.send("Sorry, I don't know when that is.")
        return
    
    e = discord.Embed(colour = 0x87CEEB)
    for time, info in w_data:
        e.add_field(name = time, value = info)
    await ctx.send(embed = e)


@client.command()
async def forecast(ctx, *args):
    """Schedules the weather command to be run at set intervals

    An id will be assigned to the forecast, this id will be used to edit/delete/control
    the forecast. This id can be changed with the changeforecastid command.

    Usage: forecast [frequency] [time] [arguments]
    
    Args:
        period: One of hourly, daily, or weekly.
        time: Time that the command will be ran at in 24 hour format
            with a colon seperating the hours from the minutes.
        arguments: Any arguments to pass to the weather command
        
    Example:
        forecast daily 6:30 today
            This command would result in "weather today" being run every day at 6:30.
    """
    # TODO: update this docstring

    # TODO(anyone): make changeforecastid command

    # TODO(anyone): This throws an error if there aren't enough arguments supplied
    frequency = args[0]
    time_string = args[1]
    command_args = args[2:]

    # Convert time_str to minutes since midnight
    # TODO: Validate this
    time_tuple = tuple(int(n) for n in time_string.split(':'))
    time = time_tuple[0] * 60 + time_tuple[1]

    # TODO: Accept a region argument, and validate it
    region = "Auckland"

    # Validate the period parameter
    if frequency not in ('hourly', 'daily', 'weekly'):
        raise forecast_manager.UnknownFrequencyError(f"The frequency: '{frequency}' is unknown, should be 'hourly', 'daily' or 'weekly'.")

    period = "now"
    readout = "standard"
    unit = "metric"

    data = (
        ctx.guild.id,
        ctx.channel.id,
        region,
        frequency,
        period,
        time,
        readout,
        unit
    )

    # TODO: This will never throw an exception anyway lol
    try:
        forecast_id = forecast_manager.add_forecast(*data)
                                                    # *command_args)
    except Exception as e:
        # TODO(anyone): catching all exceptions like this is very dangerous
        await ctx.send("I couldn't do that, sorry.")
        print("Someone made a boo boo in their forecast command, here's the error:", e)
    else:
        await ctx.send(f"Forecast successfully made, the id of this forecast is: {forecast_id}\nYou can use this id at any time to edit the forecast.")


@client.command()
async def editforecast(ctx, *args):
    """Edits a prior forecast command

    If you wish for a paramater to stay the same you can use None instead.
    eg: 

    Usage: editforecast [forecast id] [frequency] [time] [arguments]

    Args:
        frequency: One of hourly, daily, or weekly.
        time: Time that the command will be ran at in 24 hour format
            with a colon seperating the hours from the minutes.
        arguments: Any arguments to pass to the weather command.
            Omitting this clears all prior arguments.

    Examples:
        editforecast 1 daily None None
            changes the forecast with ID #1 to daily, while keeping
            all other values constant.
    """

    pass


@client.event
async def on_ready():
    print("Ready!")


# async def test_loop():
#    await client.wait_until_ready()
#    while not client.is_closed():
#        print("foobar")
#        await asyncio.sleep(10)


if __name__ == "__main__":
    client.loop.create_task(forecast_manager.forecast_loop(client))
    client.run(config.TOKEN)
