from typing import List
import re
from lang.i18n import translate as trans

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
      draft.queue = state["queue"]
      draft.old_index = state["old_index"]
      draft.finished = state["finished"]
      return draft
  except FileNotFoundError:
    return None


class Draft:
  captain_ids: List[str]
  team_size: int
  timer: int

  queue: List[str]

  current_index = 0
  old_index = 0

  finished = False

  def __init__(self, captain_ids: List[str], team_size: int, timer: int):
    self.captain_ids = captain_ids
    self.team_size = team_size
    self.timer = timer

  def save_state(self):
    with open("state.txt", "+w") as file:
      state = {
        "captain_ids": self.captain_ids,
        "queue": self.queue,
        "team_size": self.team_size,
        "timer": self.timer,
        "current_index": self.current_index,
        "old_index": self.old_index,
        "finished": self.finished
      }
      file.write(str(state))

  def get_proxy_username(self, username):
    regex = r"(.+)\((.+)\)"
    match = re.match(regex, username)
    if match:
      return match.group(1), match.group(2)
    return username, None

  def get_effective_index(self, index):
    if (index // len(self.captain_ids)) % 2 == 0:
      return index % len(self.captain_ids)
    else:
      return len(self.captain_ids) - (index % len(self.captain_ids)) - 1

  def start(self):
    self.current_index = 0
    self.old_index = 0
    
    self.queue = []
    for i in range(self.team_size-1):
      reverse = 1
      if i % 2 == 1:
        reverse = -1
      self.queue += self.captain_ids[::reverse]

    self.save_state()

  def push_back(self):
    # the current index is pushed to the back of the current part of the queue
    original_captain_id = self.queue[self.old_index]
    original_captain_id, proxy_id = self.get_proxy_username(original_captain_id)
    captain_id = original_captain_id
    if proxy_id:
      captain_id = proxy_id

    self.queue.insert(((self.old_index // len(self.captain_ids)) + 1) * len(self.captain_ids), self.queue[self.old_index])
    del self.queue[self.old_index]
    self.current_index = self.old_index
    self.save_state()

    return captain_id, original_captain_id
  
  def next_pick(self):
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))
    
    self.old_index = self.current_index

    if self.current_index > len(self.queue) - 1:
      self.finished = True
      self.save_state()
      return None

    original_captain_id = self.queue[self.current_index]
    original_captain_id, proxy_id = self.get_proxy_username(original_captain_id)
    captain_id = original_captain_id
    if proxy_id:
      captain_id = proxy_id

    self.current_index += 1
    self.save_state()
    
    return captain_id, original_captain_id
  
  def abort_timer(self):
    self.current_index = self.old_index
    self.save_state()
  
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