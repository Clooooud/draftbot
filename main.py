import discord
from draft import Draft, DraftError, recover_state
import asyncio
import dotenv
import os
import utils
from lang.i18n import translate as trans

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

draft_command = bot.create_group("draft", "Draft-related commands", guild_ids=[GUILD_ID], checks=[lambda ctx: any(role.id in ADMIN_ROLES for role in ctx.author.roles)])

@draft_command.error
async def on_error(ctx, error):
  embed = discord.Embed(
    title=trans("ERROR_TITLE"),
    description=trans("ERROR_DESCRIPTION"),
    color=discord.Color.red()
  )

  if isinstance(error, discord.errors.ApplicationCommandInvokeError):
    error = error.original

  if isinstance(error, DraftError):
    embed.description = str(error)
  else:
    print(error)

  if isinstance(error, discord.errors.CheckFailure):
    embed.description = trans("ERROR_PERMISSION")

  await ctx.respond(embed=embed)

@draft_command.command(description="Starts a draft")
async def start(
  ctx: discord.ApplicationContext, 
  captains_id: discord.Option(str, description="The draft's captains Discord IDs separated by commas, format: USERNAME or USERNAME(PROXY_USERNAME)", required=True),
  team_size: discord.Option(int, description="The size of each team (counting the captain) (min: 2)", required=True, min_value=2),
  timer: discord.Option(int, description="The time in seconds each captain has to pick a player (min: 15 sec)", required=True, min_value=15),
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


@draft_command.command(name="next", description="Starts the timer for the next pick")
async def next_pick(ctx: discord.ApplicationContext):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  next_pick.run_count += 1
  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))

  try:
    result = draft.next_pick()
  except DraftError as error:
    raise error

  if result is None:
    await end_draft(ctx)
    return
  
  captain_id, original_captain_id = result
  await notify_next_pick(ctx, captain_id, original_captain_id)

  current_run = next_pick.run_count
  await start_timer(ctx, captain_id, current_run)


async def end_draft(ctx):
  embed = discord.Embed(
    title=trans("DRAFT_ENDED_TITLE"),
    description=trans("DRAFT_ENDED_DESCRIPTION"),
    color=discord.Color.red()
  )
  await ctx.respond(embed=embed)

  # Delete state file from dir
  if os.path.exists("state.txt"):
    os.remove("state.txt")

  global draft
  draft = None


async def notify_next_pick(ctx, captain_id, original_captain_id):
  proxy = captain_id != original_captain_id

  captain = utils.get_member(members, captain_id) if members else None
  original_captain = utils.get_member(members, original_captain_id) if members else None

  captain_mention = captain.mention if captain else captain_id
  original_captain_mention = original_captain.mention if original_captain else original_captain_id
  proxy_string = trans("NEXT_PICK_PROXY", captain_id=original_captain_mention) if proxy else ""

  embed = discord.Embed(
    title=trans("NEXT_PICK_TITLE"),
    description=trans("NEXT_PICK_DESCRIPTION", captain_mention=captain_mention, proxy_string=proxy_string, draft_timer=draft.timer),
    color=discord.Color.green()
  )
  await ctx.respond(embed=embed)

  if captain:
    message = await ctx.send(captain)
    await asyncio.sleep(1)
    await message.delete()


async def start_timer(ctx, captain_id, current_run):
  old_message = None

  for i in range(draft.timer):
    if next_pick.run_count != current_run:
      return

    current_time = draft.timer - i
    if current_time in TIMER_MILESTONES:
      embed = discord.Embed(
        title=trans("TIME_REMAINING_TITLE"),
        description=trans("TIME_REMAINING_DESCRIPTION", captain_id=utils.get_mention(members, captain_id), current_time=current_time),
        color=discord.Color.blurple()
      )
      message = await ctx.respond(embed=embed)
      if old_message:
        await old_message.delete()
      old_message = message

    await asyncio.sleep(1)

  if next_pick.run_count == current_run:
    await time_up(ctx, captain_id, old_message)


async def time_up(ctx, captain_id, old_message):
  embed = discord.Embed(
    title=trans("TIMES_UP_TITLE"),
    description=trans("TIMES_UP_DESCRIPTION", captain_id=utils.get_mention(members, captain_id)),
    color=discord.Color.red()
  )

  await ctx.respond(embed=embed)

  if old_message:
    await old_message.delete()

@draft_command.command(description="Aborts/Restarts the timer for the current pick")
async def abort(ctx: discord.ApplicationContext):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  draft.abort_timer()

  embed = discord.Embed(
    title = trans("TIMER_ABORTED_TITLE"),
    description = trans("TIMER_ABORTED_DESCRIPTION"),
    color = discord.Color.red()
  )

  next_pick.run_count += 1
  await ctx.respond(embed=embed)

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

  await ctx.respond(embed=embed)


@draft_command.command(description="Cancels the current draft")
async def cancel(ctx):
  if not any(role.id in ADMIN_ROLES for role in ctx.author.roles):
    raise DraftError(trans("ERROR_PERMISSION"))

  global draft
  if draft is None:
    raise DraftError(trans("NO_DRAFT_IN_PROGRESS"))
  
  next_pick.run_count += 1
  draft = None

  await ctx.respond("DRAFT_ENDED_MESSAGE")

for command in draft_command.subcommands:
  command.error(on_error)

next_pick.run_count = -1

if AUTO_RECOVER:
  draft = recover_state()

bot.run(token)