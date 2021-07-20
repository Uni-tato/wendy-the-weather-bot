import requests
import asyncio

import discord
from discord.ext import commands

import config
import weather as weather_info
import forecast as forecast_manager

client = commands.Bot(command_prefix='W ')

@client.command()
async def test(ctx):
    forecast_manager.save()

@client.command()
async def ping(ctx):
    await ctx.send("Pong!")

@client.command()
async def weather(ctx, *args):
    ''' Summarizes the weather for you.
        Defaults to the current weather,
        but can also tell you the weather at a different time, eg: weather today
        will give you a simple summary of the weather over the day.
    '''
    when = args[0] if len(args) else "now"

    e = discord.Embed(colour = int("87CEEB", 16))

    if when == 'now':
        w_data = weather_info.now_summary()
        e.add_field(name = w_data[0], value = w_data[1])
        
    elif when == 'today':
        w_data = weather_info.today_summary_generator()
        for time, info in w_data:
            e.add_field(name = time, value = info)

    else:
        await ctx.send("Sorry, I don't know when that is.")
        return
        
    await ctx.send(embed = e)


@client.command()
async def forecast(ctx, *args):
    ''' Schedules the weather command to be run at set intervals.
        Usage: forecast [frequency] [time] [arguments]
        eg: forecast daily 6:30 today
        This command would result in "weather today" being run every day at 6:30.
        Note: the time must be entered in 24 hour format with a colon seperating the hours
        from the minutes.
        An id will be assigned to the forecast, this id will be used to edit/delete/control
        the forecast. This id can be changed with the changeforecastid command. (TODO)
        Frequency can be set to: hourly, daily, weekly.
    '''
    frequency = args[0]
    time_string = args[1]
    command_args = args[2:]

    try:
        forecast_id = forecast_manager.add_forecast(ctx.channel.id,
                                                    frequency,
                                                    time_string,
                                                    *command_args)
    except Exception as e:
        await ctx.send("I couldn't do that, sorry.")
        print("Someone made a boo boo in their forecast command, here's the error:", e)
    else:
        await ctx.send(f"Forecast successfully made, the id of this forecast is: {forecast_id}\nYou can use this id at any time to edit the forecast.")

@client.command()
async def editforecast(ctx, *args):
    ''' Edits a prior forecast command.
        Usage: edit forecast [forecast id] [frequency] [time] [arguments]
        If you wish for a paramater to stay the same you can use None instead.
        eg: edit forecast 1 daily None None
        If you leave the [arguments] empty then it will erase the prior arguments
    '''

@client.command()
async def save(ctx):
    ''' Saves data to file, can only be run by certain users'''
    if ctx.author.id not in config.ADMIN_USERS_ID:
        await ctx.send("You do not have permission to run this command.")
    else:
        m = await ctx.send("Saving...")
        forecast_manager.save()
        await m.edit(content = "Saved.")

@client.command()
async def load(ctx, *args):
    ''' Loads data from file, can only be run by certain users,
        If you're reading then then you're probably not one of the people who can use it.
    '''
    if ctx.author.id not in config.ADMIN_USERS_ID:
        await ctx.send("You do not have permission to run this command.")
    else:
        m = await ctx.send("Loading...")
        forecast_manager.load(' '.join(args))
        await m.edit(content = "Loaded")


@client.event
async def on_ready():
    print("Ready!")


##async def test_loop():
##    await client.wait_until_ready()
##    while not client.is_closed():
##        print("foobar")
##        await asyncio.sleep(10)
    
if __name__ == "__main__":
    client.loop.create_task(forecast_manager.forecast_loop(client))
    client.run(config.TOKEN)
