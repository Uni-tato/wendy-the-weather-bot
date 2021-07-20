"""The main configuration file for wendy.

This file is actually a python script that the main script imports
to use the options from as normal python variables. Remember to
set all the variables below and to rename the file to just config.py
(with no '_template'). In bash, this can be done with the `mv` command:
```
mv config_template.py config.py
```
On Windows the file can be simply renamed.
"""

# Token for the discord bot, obtained from your bot application in the discord developer portal
TOKEN = "<YOUR TOKEN HERE>"

# The URL to invite the bot, also from the discord developer portal
INVITE_URL = "<YOUR INVITE URL HERE>"

# A list of Discord User ID's that have full admin access to the bot.
# The values must be in the form of INTEGERS. You can also have as
# many comma-seperated users as you wish.
ADMIN_USERS_ID = [123]

# The prefix the bot listens for messages with
PREFIX = "<YOUR PREFIX HERE> "
