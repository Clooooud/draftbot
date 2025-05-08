from typing import List
import re
from lang.i18n import translate as trans
import utils

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

  def start(self):
    self.current_index = -1
    self.save_state()
  
  def next_pick(self):
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))
    
    self.old_index = self.current_index
    self.old_delta = self.delta
    self.old_rotation_count = self.rotation_count

    if self.current_index == (len(self.captain_ids)-1 if self.delta == 1 else 0):
      self.delta *= -1
      self.rotation_count += 1
      self.current_index -= self.delta

    if self.rotation_count == self.team_size-1:
      self.finished = True
      return None

    self.current_index += self.delta

    original_captain_id = self.captain_ids[self.current_index]
    original_captain_id, proxy_id = self.get_proxy_username(original_captain_id)
    captain_id = original_captain_id
    if proxy_id:
      captain_id = proxy_id
    
    return captain_id, original_captain_id
  
  def abort_timer(self):
    self.delta = self.old_delta
    self.current_index = self.old_index
    self.rotation_count = self.old_rotation_count
  
  def add_proxy(self, captain_id, proxy_id):
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))

    if captain_id not in self.captain_ids:
      raise DraftError(trans("CAPTAIN_NOT_FOUND"))

    if proxy_id in self.captain_ids:
      raise DraftError(trans("ALREADY_CAPTAIN", proxy_id=proxy_id))
    
    if f"{captain_id}({proxy_id})" in self.captain_ids:
      raise DraftError(trans("ALREADY_PROXY", proxy_id=proxy_id))

    self.captain_ids[self.captain_ids.index(captain_id)] = f"{captain_id}({proxy_id})"
    self.save_state()