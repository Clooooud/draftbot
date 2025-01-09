import discord
from draft import Draft, DraftError
import asyncio
import dotenv
import os

dotenv.load_dotenv()
token = str(os.getenv('DISCORD_TOKEN'))

GUILD_ID = 1247849595967508511
ADMIN_ROLES = [1247863670948495391, 1247863541998948413]

TIMER_MILESTONES = [60, 30, 10, 5]

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
    title="Error!",
    description="An error occurred while executing the command!",
    color=discord.Color.red()
  )

  if isinstance(error, discord.errors.ApplicationCommandInvokeError):
    error = error.original

  if isinstance(error, DraftError):
    embed.description = str(error)
  else:
    print(error)

  if isinstance(error, discord.errors.CheckFailure):
    embed.description = "You do not have permission to use draft commands!"

  await ctx.respond(embed=embed)

@draft_command.command(description="Starts a draft")
async def start(
  ctx: discord.ApplicationContext, 
  captains_id: discord.Option(str, description="The draft's captains Discord IDs separated by commas", required=True),
  team_size: discord.Option(int, description="The size of each team (counting the captain) (min: 2)", required=True, min_value=2),
  timer: discord.Option(int, description="The time in seconds each captain has to pick a player (min: 15 sec)", required=True, min_value=15),
):
  global draft
  
  if draft is not None:
    raise DraftError("A draft is already in progress!")
  
  draft = Draft(captains_id.split(','), team_size, timer)

  await ctx.respond(embed=draft.start())

@draft_command.command(name="next", description="Starts the timer for the next pick")
async def next_pick(ctx: discord.ApplicationContext):
  next_pick.run_count += 1
  global draft
  if draft is None:
    raise DraftError("No draft in progress!")

  try:
    embed, captain, timer_duration = draft.next_pick(members)
  except DraftError as error:
    raise error
  
  await ctx.respond(embed=embed)

  if timer_duration == -1:
    draft = None
    return

  message = await ctx.send(captain)
  await asyncio.sleep(1)
  await message.delete()

  current_run = next_pick.run_count

  for i in range(timer_duration):
    current_time = timer_duration - i
    if current_time in TIMER_MILESTONES:
      embed = discord.Embed(
        title = "Time Remaining",
        description = f"{captain} has {current_time} seconds left to pick a player!",
        color = discord.Color.blurple()
      )
      await ctx.respond(embed=embed)

    await asyncio.sleep(1)

  # Skip the time's up embed if the next pick was called
  if next_pick.run_count != current_run:
    return

  embed = discord.Embed(
    title = "Time's up!",
    description = f"{captain}'s time to pick is over!",
    color = discord.Color.red()
  )

  await ctx.respond(embed=embed)

@draft_command.command(description="Aborts/Restarts the timer for the current pick")
async def abort(ctx: discord.ApplicationContext):
  global draft
  if draft is None:
    raise DraftError("No draft in progress!")
  
  embed = draft.abort_timer()
  next_pick.run_count += 1
  await ctx.respond(embed=embed)

@draft_command.command(description="Shows the current draft status")
async def status(ctx):
  global draft
  if draft is None:
    raise DraftError("No draft in progress!")
  
  embed = draft.get_status_embed()
  await ctx.respond(embed=embed)

@draft_command.command(description="Cancels the current draft")
async def cancel(ctx):
  global draft
  if draft is None:
    raise DraftError("No draft in progress!")
  
  draft = None

  await ctx.respond("Draft ended!")

for command in draft_command.subcommands:
  command.error(on_error)

next_pick.run_count = -1

bot.run(token)