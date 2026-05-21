import discord
from src.draft import Draft, DraftError, recover_state, create_draft
import asyncio
import dotenv
import os
import src.utils.utils as utils
from src.player import Team
from src.lang.i18n import translate as trans
import random

dotenv.load_dotenv()
token = str(os.getenv('DISCORD_TOKEN'))

from settings import *

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)

members = None
draft = None

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user}')
  global members
  members = await bot.get_guild(GUILD_ID).fetch_members().flatten()
  await bot.sync_commands(guild_ids=[GUILD_ID])

draft_command = bot.create_group("draft", "Draft-related commands", guild_ids=[GUILD_ID])

@draft_command.error
async def on_error(ctx, error):
  embed = discord.Embed(
    title=trans("ERROR_TITLE"),
    description=trans("ERROR_DESCRIPTION"),
    color=discord.Color.red()
  )

  if isinstance(error, discord.errors.ApplicationCommandInvokeError):
    error = error.original

  ephemeral = True
  if isinstance(error, DraftError):
    embed.description = str(error)
    ephemeral = error.ephemeral if hasattr(error, "ephemeral") else True
  else:
    print(error)

  if isinstance(error, discord.errors.CheckFailure):
    embed.description = trans("ERROR_PERMISSION")

  await ctx.respond(embed=embed, ephemeral=ephemeral)

@draft_command.command(description="Starts a draft")
async def start(
  ctx: discord.ApplicationContext, 
  # TODO: Unsure, maybe the best way to configure the draft is through csv/json files
  # captains_id: discord.Option(str, description="The draft's captains Discord IDs separated by commas, format: USERNAME or USERNAME(PROXY_USERNAME)", required=True),
  # team_size: discord.Option(int, description="The size of each team (counting the captain) (min: 2)", required=True, min_value=2),
  # timer: discord.Option(int, description="The time in seconds each captain has to pick a player (min: 15 sec)", required=True, min_value=15),
):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  
  if draft is not None:
    raise DraftError(trans("DRAFT_ALREADY_IN_PROGRESS"))
  
  draft = Draft(captains_id.split(','), team_size, timer)

  draft.start()

  embed = utils.get_status_embed(draft)
  embed.title = trans("DRAFT_STARTED")
  embed.color = discord.Color.green()

  await ctx.respond(embed=embed)

@draft_command.command(description="Adds a proxy to a captain")
async def add_proxy(
    ctx, 
    captain_id: discord.Option(str, description="Captain's Discord Tag", required=True), 
    proxy_id: discord.Option(str, description="Proxy's Discord Tag", required=True)
):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  draft.add_proxy(captain_id, proxy_id)

  embed = discord.Embed(
    title = trans("PROXY_ADDED_TITLE"),
    description = trans("PROXY_ADDED_DESCRIPTION", proxy_id=utils.get_mention(members, proxy_id), captain_id=utils.get_mention(members, captain_id)),
    color = discord.Color.green()
  )

  await ctx.respond(embed=embed)


@draft_command.command(name="pick", description="Picks a player for the captain whose turn it is")
async def pick(
  ctx, 
  player_discord: discord.Option(discord.Member, description="The Discord Tag of the player to pick (You must select only one parameter)", required=False),
  player_username: discord.Option(str, description="The osu! username of the player to pick (You must select only one parameter)", required=False)
):
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  current_team = draft.queue[draft.current_index]
  if current_team.captain.discord_id != ctx.author.name and current_team.proxy_discord_id != ctx.author.name:
    return await ctx.respond(trans("NOT_YOUR_TURN"), ephemeral=True)
  
  team, player = draft.pick_player(current_team.captain.discord_id, player_discord.name if player_discord else None, player_username if player_username else None)
  embed = discord.Embed(
    title = trans("DRAFT_JOIN_TEAM_TITLE", team_name=team.captain.display_username()),
    description = trans("DRAFT_JOIN_TEAM_DESCRIPTION", captain_name=team.captain.display_username(), player_name=player.display_username()),
    color = discord.Color.green()
  )
  await ctx.respond(embed=embed)

@draft_command.command(name="team", description="Shows your team")
async def show_team(ctx: discord.ApplicationContext):
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  team = next((team for team in draft.teams if team.captain.discord_id == ctx.author.name or team.proxy_discord_id == ctx.author.name), None)
  if team is None:
    raise DraftError(trans("NOT_A_CAPTAIN_OR_PROXY"))
  
  embed = discord.Embed(
    title = trans("TEAM", team_name=team.captain.display_username()),
    color = discord.Color.blurple()
  )
  embed.add_field(name=trans("CAPTAIN"), value=team.captain.display_username(), inline=True)
  if team.proxy_discord_id:
    embed.add_field(name=trans("PROXY"), value=team.proxy_discord_id, inline=True)
  if team.players:
    embed.add_field(name=trans("PLAYERS"), value="- " + "\n- ".join(player.display_username() for player in team.players), inline=False)
  else:
    embed.add_field(name=trans("PLAYERS"), value=trans("NO_PLAYERS"), inline=False)
  await ctx.respond(embed=embed, ephemeral=True)


@draft_command.command(name="teams", description="Shows all teams")
async def show_teams(ctx: discord.ApplicationContext):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))

  embed = discord.Embed(
    title = trans("TEAMS"),
    color = discord.Color.blurple()
  )
  for team in draft.teams:
    # Show team members without the proxy
    team_description = ", ".join(player.display_username() for player in team.players) if team.players else trans("NO_PLAYERS")
    embed.add_field(name=trans("TEAM", team_name=team.captain.display_username()), value=team_description, inline=False)
  await ctx.respond(embed=embed)

@draft_command.command(name="random_pick", description="Randomly picks a player for the captain whose turn it is")
async def random_pick(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  random_player = random.choice(draft.get_draftable_players())
  team, player = draft.pick_player(draft.queue[draft.current_index].captain.discord_id, random_player.discord_id)
  embed = discord.Embed(
    title = trans("DRAFT_JOIN_TEAM_TITLE", team_name=team.captain.display_username()),
    description = trans("DRAFT_JOIN_TEAM_DESCRIPTION", captain_name=team.captain.display_username(), player_name=player.display_username()),
    color = discord.Color.green()
  )
  await ctx.respond(embed=embed)


@draft_command.command(name="players", description="Shows all draftable players left")
async def list_players(ctx: discord.ApplicationContext):
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))

  draftable_players = draft.get_draftable_players()
  if not draftable_players:
    await ctx.respond(trans("NO_DRAFTABLE_PLAYERS"), ephemeral=True)
    return

  embed = discord.Embed(
    title = trans("DRAFTABLE_PLAYERS"),
    description="- " + ("\n- ".join((f"**{player.display_username()}**" + (f" (#{player.rank})" if player.rank is not None else "")) for player in draftable_players)),
    color = discord.Color.blurple()
  )
  await ctx.respond(embed=embed, ephemeral=True)

@draft_command.command(name="next", description="Starts the timer for the next pick")
async def start_pick(ctx: discord.ApplicationContext):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  start_pick.run_count += 1
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))

  team = draft.start_timer()

  if team is None:
    await end_draft(ctx)
    return
  
  await notify_next_pick(ctx, team)

  current_run = start_pick.run_count
  await start_timer(ctx, team, current_run)

async def end_draft(ctx):
  embed = discord.Embed(
    title=trans("DRAFT_ENDED_TITLE"),
    description=trans("DRAFT_ENDED_DESCRIPTION"),
    color=discord.Color.red()
  )
  await ctx.respond(embed=embed)

  # Delete state file from dir
  if os.path.exists("state.json"):
    os.remove("state.json")

  global draft
  draft = None


async def notify_next_pick(ctx, team: Team):
  proxy = team.proxy_discord_id

  captain = utils.get_member(members, team.captain.discord_id) if members else None
  captain_mention = captain.mention if captain else team.captain.display_username()

  proxy_string = ""
  if proxy:
    proxy_string = trans("NEXT_PICK_PROXY", captain_id=captain_mention)
    captain = utils.get_member(members, proxy) if members else None
    captain_mention = captain.mention if captain else proxy

  embed = discord.Embed(
    title=trans("NEXT_PICK_TITLE"),
    description=trans("NEXT_PICK_DESCRIPTION", captain_mention=captain_mention, proxy_string=proxy_string, draft_timer=draft.timer),
    color=discord.Color.green()
  )
  await ctx.respond(embed=embed)

  if captain:
    message = await ctx.send(captain_mention)
    await asyncio.sleep(1)
    await message.delete()


async def start_timer(ctx, team, current_run):
  old_message = None

  for i in range(draft.timer):
    if start_pick.run_count != current_run:
      return

    current_time = draft.timer - i
    if current_time in TIMER_MILESTONES:
      discord_id = team.captain.discord_id if not team.proxy_discord_id else team.proxy_discord_id
      captain = utils.get_member(members, discord_id) if members else None
      captain_mention = captain.mention if captain else team.captain.display_username()
      embed = discord.Embed(
        title=trans("TIME_REMAINING_TITLE"),
        description=trans("TIME_REMAINING_DESCRIPTION", captain_id=captain_mention, current_time=current_time),
        color=discord.Color.blurple()
      )
      message = await ctx.respond(embed=embed)
      if old_message:
        await old_message.delete()
      old_message = message

    await asyncio.sleep(1)

  if start_pick.run_count == current_run:
    await time_up(ctx, captain_mention, old_message)


async def time_up(ctx, captain_mention, old_message):
  embed = discord.Embed(
    title=trans("TIMES_UP_TITLE"),
    description=trans("TIMES_UP_DESCRIPTION", captain_id=captain_mention),
    color=discord.Color.red()
  )

  await ctx.respond(embed=embed)

  if old_message:
    await old_message.delete()

# @draft_command.command(description="Aborts/Restarts the timer for the current pick")
# async def abort(ctx: discord.ApplicationContext):
#   if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
#     raise DraftError(trans("ERROR_PERMISSION"))

#   global draft
#   if draft is None:
#     raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
#   draft.abort_timer()

#   embed = discord.Embed(
#     title = trans("TIMER_ABORTED_TITLE"),
#     description = trans("TIMER_ABORTED_DESCRIPTION"),
#     color = discord.Color.red()
#   )

#   start_pick.run_count += 1
#   await ctx.respond(embed=embed)

@draft_command.command(description="Shows the current draft status")
async def status(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))
  
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  embed = utils.get_status_embed(draft)
  await ctx.respond(embed=embed)

@draft_command.command(description="Recovers the draft from the last state in case something breaks")
async def recover(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is not None:
    raise DraftError(trans("DRAFT_ALREADY_IN_PROGRESS"))
  try:
    draft = recover_state()
  except FileNotFoundError:
    raise DraftError("No draft to recover!")
  
  embed = discord.Embed(
    title = trans("DRAFT_STATUS_RECOVERED_TITLE"),
    description = trans("DRAFT_STATUS_RECOVERED_DESCRIPTION"),
    color = discord.Color.green()
  )

  await ctx.respond(embed=embed, ephemeral=True)

@draft_command.command(description="Pushes back the current pick to the end of the order of the round")
async def push_back(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))
  
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  captain_id, original_captain_id = draft.push_back()
  
  proxy = captain_id != original_captain_id

  captain = utils.get_member(members, captain_id) if members else None
  original_captain = utils.get_member(members, original_captain_id) if members else None

  print(captain_id, original_captain_id)

  captain_mention = captain.mention if captain else captain_id
  original_captain_mention = original_captain.mention if original_captain else original_captain_id

  proxy_string = trans("NEXT_PICK_PROXY", captain_id=original_captain_mention) if proxy else ""

  embed = discord.Embed(
    title=trans("PUSH_BACK_TITLE"),
    description=trans("PUSH_BACK_DESCRIPTION", captain_mention=captain_mention, proxy_string=proxy_string),
    color=discord.Color.green()
  )

  await ctx.respond(embed=embed)


@draft_command.command(description="Cancels the current draft")
async def cancel(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  start_pick.run_count += 1
  draft = None

  await ctx.respond(trans("DRAFT_ENDED_MESSAGE"))

for command in draft_command.subcommands:
  command.error(on_error)

start_pick.run_count = -1

if AUTO_RECOVER:
  draft = recover_state()

if not draft:
  with open("draft.csv", "r") as file:
    lines = file.readlines()
    player_infos = []
    for line in lines[1:]:
      if line.strip():
        parts = line.strip().split(",")
        osu_id = int(parts[0])
        osu_playername = parts[1]
        discord_id = parts[2]
        is_captain = parts[3].lower() == "true"
        proxy_discord_id = parts[4] if len(parts) > 4 and parts[4].strip() else None
        rank = int(parts[5]) if len(parts) > 5 and parts[5].strip() else None
        player_infos.append((osu_id, osu_playername, discord_id, is_captain, proxy_discord_id, rank))

    draft = create_draft(player_infos, team_size=7, timer=90)
    draft.start()

bot.run(token)
