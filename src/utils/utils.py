import discord
from settings import *
from src.lang.i18n import translate as trans

def get_status_embed(draft):
    embed = discord.Embed(
        title = "Draft Status",
        color=discord.Color.blurple()
    )

    captains = list([team.captain.player_username for team in draft.teams])
    next_to_pick = ""

    def get_formatted_proxy_string(captain, proxy):
        draft_not_ended = draft.current_index < len(draft.queue)
        current_team = draft.queue[draft.current_index] if draft_not_ended else None
        final_string = f"{proxy} (proxy for {captain})" if proxy else captain

        if current_team and (current_team.captain.player_username == captain):
            final_string = f"__**{final_string}**__"  
        
        return final_string

    for i in range(len(draft.teams)):
        captain_id = draft.teams[i].captain.player_username
        proxy = draft.teams[i].proxy_discord_id
        if proxy:
            # Replace the captain with: username with proxy_username as proxy
            captains[i] = f"{proxy} (proxy for {captain_id})"
        
        if draft.current_index < len(draft.queue) and draft.queue[draft.current_index].captain.player_username == captain_id:
            next_to_pick = captains[i].replace("-", "\-")
        
        captains[i] = get_formatted_proxy_string(captain_id, proxy)

    embed.add_field(name=trans("CAPTAINS"), value=", ".join(captains).replace("-", "\-"), inline=False)
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
