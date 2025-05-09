import discord
from settings import *
from lang.i18n import translate as trans

def get_status_embed(draft):
    embed = discord.Embed(
        title = "Draft Status",
        color=discord.Color.blurple()
    )

    captain_ids = list(draft.captain_ids)
    next_to_pick = ""

    def get_formatted_proxy_string(captain, proxy):
        if proxy:
            proxy, captain = captain, proxy
        if draft.current_index < len(draft.queue) and draft.queue[draft.current_index] == captain_id:
            captain = f"__**{captain}**__"
        if proxy:
            proxy, captain = captain, proxy    
        return f"{proxy} (proxy for {captain})" if proxy else captain

    for i in range(len(draft.captain_ids)):
        captain_id = draft.captain_ids[i]
        captain, proxy = draft.get_proxy_username(captain_id)
        if proxy:
            # Replace the captain with: username with proxy_username as proxy
            captain_ids[i] = f"{proxy} (proxy for {captain})"
        
        if draft.current_index < len(draft.queue) and draft.queue[draft.current_index] == captain_id:
            next_to_pick = captain_ids[i]
        
        captain_ids[i] = get_formatted_proxy_string(captain, proxy)

    embed.add_field(name=trans("CAPTAINS"), value=", ".join(captain_ids), inline=False)
    embed.add_field(name=trans("TEAM_SIZE"), value=draft.team_size, inline=True)
    embed.add_field(name=trans("TIMER"), value=f"{draft.timer} sec", inline=True)
    embed.add_field(name=trans("NEXT_TO_PICK"), value=next_to_pick, inline=False)
    embed.set_author(name=f"{TOURNAMENT_NAME} Draft Bot", icon_url=TOURNAMENT_ICON)

    return embed

def get_member(members, discord_id):
    if not members:
        return discord_id
    return discord.utils.get(members, name=discord_id) or None

def get_mention(members, discord_id):
    member = get_member(members, discord_id)
    return member.mention if member else discord_id
