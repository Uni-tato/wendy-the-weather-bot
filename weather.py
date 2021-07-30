"""Collection of functions for gathering data from the weather API.

Wendy depends on the amazing wttr.in project. Without it, she wouldn't
know a thing about the weather!
Check out the project here: https://github.com/chubin/wttr.in
"""

import json
import requests

import discord

def today_summary_generator():
    """Generates a summary of today's weather at various points throughout the day."""

    reply = requests.request("GET","http://wttr.in/Auckland?format=j1")
    weather = json.loads(reply.content)
    today = weather["weather"][0]
    hourly = today["hourly"]

    # Interpret the data
    # TODO(anyone): Why specifically at these indexes?
    data = dict()
    data['morning'] = hour_summary_from_raw(hourly[3])
    data['noon'] = hour_summary_from_raw(hourly[4])
    data['evening'] = hour_summary_from_raw(hourly[6])
    data['night'] = hour_summary_from_raw(hourly[7])

    yield from data.items()


def now_summary():
    """Gets a summary of the current weather."""
    
    reply = requests.request("GET","http://wttr.in/Auckland?format=j1")
    weather = json.loads(reply.content)
    now = weather['current_condition'][0]

    return (f"As of: {now['observation_time']}", now_summary_from_raw(now))    
    

def hour_summary_from_raw(hour):
    """Generates a string of the weather from the raw wttr hour data."""

    DEGREE_SIGN= u'\N{DEGREE SIGN}'
    return f"{hour['weatherDesc'][0]['value']}\nTemp: {hour['tempC']}{DEGREE_SIGN}C (feels like: {hour['FeelsLikeC']}{DEGREE_SIGN}C)\nChance of rain: {hour['chanceofrain']}%"


def now_summary_from_raw(data):
    """Generates a string for the current weather from the raw wttr data.
    
    Can't just reuse hour_summary_from_raw because some of the god damn keys
    are named differently! Also there are different keys/values, eg we don't
    have a chance of rain pair, which kinda makes sense, but it would be
    easier if we did and I could just use the same function lol.
    """
    DEGREE_SIGN= u'\N{DEGREE SIGN}'
    return f"{data['weatherDesc'][0]['value']}\nTemp: {data['temp_C']}{DEGREE_SIGN}C (feels like: {data['FeelsLikeC']}{DEGREE_SIGN}C)"


def find_options(location, *args):
    """Takes a bunch of arguments and returns them in a dict.
    
    The first arg must be the location as we can't validate this against a list.
    The other args will be placed into a dict where the key is the option they correspond to.
    The keys and possible values of the returned dict will be:
    - period: now, today, triday
    - readout: standard, full, quick
    - units: both, c, f
    If an argument is left out, eg args does not contain "now", "today" or "triday" then
    the first possible option listed will be returned in the dict, eg in the example dict["period"]
    would be "now".
    """
    # TODO: Warn the user if an argument they supplied is unknown?

    options = {"location":location, "period": "now", "readout": "standard", "units": "both"}
    
    all_options = {
        "period": ("today", "triday"),
        "readout": ("full", "quick"),
        "units": ("c", "f")
        }# We can ignore the default options.
    
    for arg in args:
        for option_name, option_choices in all_options.items():
            if arg.lower() in option_choices:
                options[option_name] = arg.lower()
    
    return options


async def send_weather(client, forecast):
    """Sends the weather.
    
    This can either be the result of manually calling "weather",
    or because of a scheduled forecast.
    
    Args:
        client: The active discord client.
        forecast: The forecast to send.
    """

    when = forecast.period

    if when == 'now':
        w_data = [now_summary()]
    elif when == 'today':
        w_data = today_summary_generator()
    else:
        # when == 'triday'
        # TODO: needs a generator
        # for now just get the now
        w_data = [now_summary()]

    e = discord.Embed(colour = 0x87CEEB)
    for time, info in w_data:
        e.add_field(name = time, value = info)

    # Get the channel that we need to send too
    channel = client.get_channel(forecast.channel_id)
    if channel == None:
        channel = await client.fetch_channel(forecast.channel_id)

    await forecast.channel.send(embed = e)
