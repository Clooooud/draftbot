import discord
from settings import *
from lang.i18n import translate as trans

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

    finished_on_next = False
    next_index = 0
    if draft.current_index < len(draft.queue)-1:
        next_index = draft.get_effective_index(draft.current_index)
    else:
        finished_on_next = True
    next_index = max(0, min(next_index, len(captain_ids)-1))
    if not finished_on_next:
        captain_ids[next_index] = f"__**{captain_ids[next_index]}**__"

    embed.add_field(name=trans("CAPTAINS"), value=", ".join(captain_ids), inline=False)
    embed.add_field(name=trans("TEAM_SIZE"), value=draft.team_size, inline=True)
    embed.add_field(name=trans("TIMER"), value=f"{draft.timer} sec", inline=True)
    embed.add_field(name=trans("NEXT_TO_PICK"), value=draft.captain_ids[next_index] if not finished_on_next else "", inline=False)
    embed.set_author(name=f"{TOURNAMENT_NAME} Draft Bot", icon_url=TOURNAMENT_ICON)

    return embed

def get_member(members, discord_id):
    if not members:
        return discord_id
    return discord.utils.get(members, id=discord_id) or None

def get_mention(members, discord_id):
    member = get_member(members, discord_id)
    return member.mention if member else discord_id
