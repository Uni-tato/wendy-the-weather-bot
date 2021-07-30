
## forecast schema

### REQUIRED ARGS
- region: place name where to get the weather

### OPTIONAL ARGS
1. frequency: how often to send the message. One of hourly, daily, or weekly (default: daily)
2. period: what period of time to show the weather for. One of now, today or triday (default: today)
2. time: time when to send the message, in X:Y 24h format (default: 8AM)
3. readout: how much information to give. One of standard, full, quick (default: standard)
4. unit: Units to display data in. One of metric or imperial (default: metric)


## Issues

I forsee a very big problem here that needs to be resolved. Basically, since we're constantly fetching *new* forecast objects
from the database instead of keeping a constant "cache" of objects, we aren't saving when it has last ran. Therefore,
every time the database is loaded and a forecast is checked, it will *always* want to send!

SOLUTION: Adding a "last sent time" column to the database should solve this



When we create a temporary forecast object from the "weather" command, we don't have the frequency or time parameters,
so they're just left as None. However, the forecast object immedietly does some post-processing on these which will
throw an error.

SOLUTION: Either first test if they're None before doing the post-processing, OR pass a `scheduled=False` parameter to
forecast that tells it it's a temporary forecast.
