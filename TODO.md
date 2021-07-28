
## forecast schema

### REQUIRED ARGS
- region: place name where to get the weather

### OPTIONAL ARGS
1. frequency: how often to send the message. One of hourly, daily, or weekly (default: daily)
2. period: what period of time to show the weather for. One of now, today or triday (default: today)
2. time: time when to send the message, in X:Y 24h format (default: 8AM)
3. readout: how much information to give. One of standard, full, quick (default: standard)
4. unit: Units to display data in. One of metric or imperial (default: metric)
