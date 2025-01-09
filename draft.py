from typing import List
import discord


class DraftError(Exception):
  pass


class Draft:
  captain_ids: List[str]
  team_size: int
  timer: int

  current_index = 0
  delta = 1
  rotation_count = 0

  old_index = 0
  old_delta = 1
  old_rotation_count = 0

  finished = False

  def __init__(self, captain_ids: List[str], team_size: int, timer: int):
    self.captain_ids = captain_ids
    self.team_size = team_size
    self.timer = timer

  def get_status_embed(self):
    embed = discord.Embed(
      title = "Draft Status",
      color=discord.Color.blurple()
    )

    next_index = self.current_index+self.delta
    captain_ids = list(self.captain_ids)
    captain_ids[next_index] = f"__**{captain_ids[next_index]}**__"

    embed.add_field(name="Captains", value=", ".join(captain_ids), inline=False)
    embed.add_field(name="Team Size", value=self.team_size, inline=True)
    embed.add_field(name="Timer", value=f"{self.timer} sec", inline=True)
    embed.add_field(name="Next to pick", value=self.captain_ids[next_index], inline=False)
    embed.set_author(name="RAWR Draft Bot", icon_url="https://cdn.discordapp.com/icons/1247849595967508511/a45ca9553a36c44140c610b5721b462f.webp")

    return embed

  def start(self):
    self.current_index = -1

    embed = self.get_status_embed()
    embed.title = "Draft started!"
    embed.color = discord.Color.green()

    return embed
  
  def next_pick(self, members):
    if self.finished:
      raise DraftError("The draft is already over!")
    
    self.old_index = self.current_index
    self.old_delta = self.delta
    self.old_rotation_count = self.rotation_count

    if self.current_index == (len(self.captain_ids)-1 if self.delta == 1 else 0):
      self.delta *= -1
      self.rotation_count += 1
      self.current_index -= self.delta

    if self.rotation_count == self.team_size-1:
      self.finished = True

      embed = discord.Embed(
        title = "Draft Ended",
        description = "The draft is now over!",
        color = discord.Color.red()
      )
      return embed, None, -1 # -1 is the timer code for the end of the draft

    self.current_index += self.delta

    captain = discord.utils.get(members, name=self.captain_ids[self.current_index])
    mention = captain.mention if captain else self.captain_ids[self.current_index]

    embed = discord.Embed(
      title = "Next Pick",
      description = f"{mention} is up next! He has {self.timer} seconds to pick a player!",
      color = discord.Color.green()
    )

    return embed, mention, self.timer 
  
  def abort_timer(self):
    self.delta = self.old_delta
    self.current_index = self.old_index
    self.rotation_count = self.old_rotation_count

    embed = discord.Embed(
      title = "Timer Aborted",
      description = "The timer has been aborted!",
      color = discord.Color.red()
    )

    return embed