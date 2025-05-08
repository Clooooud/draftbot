from typing import List
import discord
import re


class DraftError(Exception):
  pass


def recover_state():
  try:
    with open("state.txt", "r") as file:
      state = eval(file.read())
      draft = Draft(
        captain_ids=state["captain_ids"],
        team_size=state["team_size"],
        timer=state["timer"]
      )
      draft.current_index = state["current_index"]
      draft.delta = state["delta"]
      draft.rotation_count = state["rotation_count"]
      draft.old_index = state["old_index"]
      draft.old_delta = state["old_delta"]
      draft.old_rotation_count = state["old_rotation_count"]
      draft.finished = state["finished"]
      return draft
  except FileNotFoundError:
    return None


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

  def save_state(self):
    with open("state.txt", "+w") as file:
      state = {
        "captain_ids": self.captain_ids,
        "team_size": self.team_size,
        "timer": self.timer,
        "current_index": self.current_index,
        "delta": self.delta,
        "rotation_count": self.rotation_count,
        "old_index": self.old_index,
        "old_delta": self.old_delta,
        "old_rotation_count": self.old_rotation_count,
        "finished": self.finished
      }
      file.write(str(state))

  def get_proxy_username(self, username):
    regex = r"(.+)\((.+)\)"
    match = re.match(regex, username)
    if match:
      return match.group(1), match.group(2)
    return username, None

  def get_status_embed(self):
    embed = discord.Embed(
      title = "Draft Status",
      color=discord.Color.blurple()
    )

    captain_ids = list(self.captain_ids)

    for i in range(len(self.captain_ids)):
      captain = self.captain_ids[i]
      captain, proxy = self.get_proxy_username(captain)
      if proxy:
        # Replace the captain with: username with proxy_username as proxy
        captain_ids[i] = f"{proxy} (proxy for {captain})"

    next_index = self.current_index+self.delta
    next_index = max(0, min(next_index, len(captain_ids)-1))
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

    self.save_state()

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

      # Delete state file from dir
      import os
      os.remove("state.txt")

      return embed, None, -1 # -1 is the timer code for the end of the draft

    self.current_index += self.delta

    original_captain_id = self.captain_ids[self.current_index]
    original_captain_id, proxy = self.get_proxy_username(original_captain_id)
    captain_id = original_captain_id
    if proxy:
      captain_id = proxy
    print(captain_id)

    captain = None
    if members:
      captain = discord.utils.get(members, name=captain_id)
      original_captain = discord.utils.get(members, name=original_captain_id)
    captain_mention = captain.mention if captain else captain_id
    original_captain_mention = original_captain.mention if original_captain else original_captain_id

    proxy_string = "(proxy for " + original_captain_mention + ") " if proxy else ""

    embed = discord.Embed(
      title = "Next Pick",
      description = f"{captain_mention} {proxy_string}is up next! He has {self.timer} seconds to pick a player!",
      color = discord.Color.green()
    )

    self.save_state()

    return embed, captain_mention, self.timer 
  
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
  
  def add_proxy(self, captain_id, proxy_id):
    if self.finished:
      raise DraftError("The draft is already over!")

    if captain_id not in self.captain_ids:
      raise DraftError("Captain not found!")

    if proxy_id in self.captain_ids:
      raise DraftError(f"{proxy_id} is already a captain!")
    
    if f"{captain_id}({proxy_id})" in self.captain_ids:
      raise DraftError(f"{proxy_id} is already a proxy for this captain!")

    self.captain_ids[self.captain_ids.index(captain_id)] = f"{captain_id}({proxy_id})"

    embed = discord.Embed(
      title = "Proxy Added",
      description = f"{proxy_id} has been added as a proxy for {captain_id}!",
      color = discord.Color.green()
    )

    self.save_state()

    return embed