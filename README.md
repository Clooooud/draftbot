# Discord Tourney Draft Bot

I quickly made a simple Tourney Draft Bot that can be used to draft teams for a tournament.

There are two types of ordering methods for the draft: snake and repeated:
- Snake: the order of picks is 1-2-3-4-4-3-2-1
- Repeated: the order of picks is 1-2-3-4-1

## Usage

1. Create a Discord Bot and get the token
2. In the Bot settings, enable the `MESSAGE CONTENT INTENT` and `SERVER MEMBERS INTENT`
3. Invite the bot to your server
4. Rename the `example.env` file to `.env` and fill in the token
5. Rename the `settings.example.py` file to `settings.py` and fill in the settings
6. Create a virtual environment with `python -m venv venv`
7. Activate the virtual environment
8. Install the requirements with `pip install -r requirements.txt`
9. Run the bot with `python main.py`
10. `/draft` !!!

## How to set up the draft

You need to create a csv file with the players you want to draft. The csv file should have the following format:

```
osu_username,discord_id,is_captain,proxy_discord_id,rank
ManiaP,maniap,TRUE,,14025
shibenz,shibenz,TRUE,,12751
MiniShaawn,zayren0,TRUE,,13796
...
```

I recommend creating a Google Sheet, filling it with the players and their information, and then exporting it as a csv file. This way, if you ever need to update the list of players, you can just update the Google Sheet and export it again.


## Google Sheets sync


I also added a Google Sheets sync feature, which allows you to sync the draft data with a Google Sheet. This way, you can easily share the draft data with other people and update it in real time.

To set up the Google Sheets sync, you need to create a Google Cloud project and enable the Google Sheets API. Then, you need to create a service account and download the credentials json file (put it in the root directory as `service_account.json`). Finally, you need to share the Google Sheet with the service account email.

The sheet will be filled automatically starting at the B2 cell, with the following format:

```
,Captain,P1, P2, P3, ...
Team1,ManiaP,Player1,Player2,Player3,...
Team2,shibenz,Player1,Player2,Player3,...
Team3,MiniShaawn,Player1,Player2,Player3,...
...
```

This is useful for streaming the draft, as you can just capture the Google Sheet window and it will update in real time as the draft progresses. I recommend making another tab in the same sheet with better formatting and capturing that one instead of the raw data tab.

## Tournaments that used this bot

- [Ryshult's Archived Waste Recycling (RAWR)](https://osu.ppy.sh/community/forums/topics/2010215?n=1)
- [5 Digits French Cup 2025 (5DFC25)](https://osu.ppy.sh/community/forums/topics/2067539?n=1)
- [5 Digits French Cup 2026 (5DFC26)](https://osu.ppy.sh/community/forums/topics/2200826?n=1)