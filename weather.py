import requests
import json


def today_summary_generator():
    reply = requests.request("GET","http://wttr.in/Auckland?format=j1")
    weather = json.loads(reply.content)
    today = weather["weather"][0]
    hourly = today["hourly"]

    data = dict()

    data['morning'] = hour_summary_from_raw(hourly[3])
    data['noon'] = hour_summary_from_raw(hourly[4])
    data['evening'] = hour_summary_from_raw(hourly[6])
    data['night'] = hour_summary_from_raw(hourly[7])

    yield from data.items()

def now_summary():
    reply = requests.request("GET","http://wttr.in/Auckland?format=j1")
    weather = json.loads(reply.content)
    now = weather['current_condition'][0]

    return (f"As of: {now['observation_time']}", now_summary_from_raw(now))
    
    

def hour_summary_from_raw(hour):
    DEGREE_SIGN= u'\N{DEGREE SIGN}'
    return f"{hour['weatherDesc'][0]['value']}\nTemp: {hour['tempC']}{DEGREE_SIGN}C (feels like: {hour['FeelsLikeC']}{DEGREE_SIGN}C)\nChance of rain: {hour['chanceofrain']}%"


def now_summary_from_raw(data):
    ''' Can't just reuse hour_summary_from_raw because some of the god damn keys
        are named differently!
        Also there are different keys/values, eg we don't have a chance of rain pair,
        which kinda makes sence, but it would be easier if we did and I could just use
        the same function lol.
    '''
    DEGREE_SIGN= u'\N{DEGREE SIGN}'
    return f"{data['weatherDesc'][0]['value']}\nTemp: {data['temp_C']}{DEGREE_SIGN}C (feels like: {data['FeelsLikeC']}{DEGREE_SIGN}C)"

