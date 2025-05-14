# Discord Tourney Draft Bot

I quickly made a simple Tourney Draft Bot that can be used to draft teams for a tournament.

You can use it for snake order drafts (reversing the order each round).
If you ever need a different order, you can just create an issue or send me a DM on Discord @nunuage

The bot is purely manual, you need to type the `/draft next` command for each team pick 

## Usage

1. Create a Discord Bot and get the token
2. In the Bot settings, enable the `MESSAGE CONTENT INTENT` and `SERVER MEMBERS INTENT`
3. Invite the bot to your server
4. Rename the `example.env` file to `.env` and fill in the token
5. Rename the `settings.example.py` file to `settings.py` and fill in the settings
6. Install the requirements with `pip install -r requirements.txt`
7. Run the bot with `python main.py`
8. `/draft` !!!
