# Ctrl-Z-Bot
This bot can undo things via a command like channels deletes, role changes and bans.
This will also undo channel overwrites

### How does it work ❓
The bot scanns the audit log of a user and creates button prompts to undo stuff

### Requirements 🪐:
- Python
- Made and tested on Pycord NOT discord.py

### Limitations 😒:
- The audit log can't display everything!
- Things like channel orders will be lost.
- Banned users obviously won't be added back
- Messages aren't backed up and will be lost
- Not all events are supported!

### Uses ⚡:
- Bad channel design needs to be undone
- Accidentally deleted channel/role with lots of permissions
- Server got nuked, all roles and channels gone and lots of spam channels

### Continuing ⏩:
I'm not really sure if I will keep on updating this project, after looking at everything it isn't that useful because of missing items in audit logs.

I will accept pull requests if somebody want to code for me :)

I might fix a issue here and there.
