import discord
from settings import *

def get_status_embed(draft):
    embed = discord.Embed(
      title = "Draft Status",
      color=discord.Color.blurple()
    )

    captain_ids = list(draft.captain_ids)

    for i in range(len(draft.captain_ids)):
      captain = draft.captain_ids[i]
      captain, proxy = draft.get_proxy_username(captain)
      if proxy:
        # Replace the captain with: username with proxy_username as proxy
        captain_ids[i] = f"{proxy} (proxy for {captain})"

    next_index = draft.current_index + draft.delta
    next_index = max(0, min(next_index, len(captain_ids)-1))
    captain_ids[next_index] = f"__**{captain_ids[next_index]}**__"

    embed.add_field(name="Captains", value=", ".join(captain_ids), inline=False)
    embed.add_field(name="Team Size", value=draft.team_size, inline=True)
    embed.add_field(name="Timer", value=f"{draft.timer} sec", inline=True)
    embed.add_field(name="Next to pick", value=draft.captain_ids[next_index], inline=False)
    embed.set_author(name=f"{TOURNAMENT_NAME} Draft Bot", icon_url=TOURNAMENT_ICON)

    return embed