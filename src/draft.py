from typing import List
from src.lang.i18n import translate as trans
from settings import ORDERING_METHOD, SPREADSHEET_PUSH, SPREADSHEET_SHEET_NAME, SPREADSHEET_START_COL, SPREADSHEET_START_ROW
from src.player import Player, Team
from src.actions import Action, FinishDraftAction, PickAction, PushBackAction, AddProxyAction
from src.utils.google import writeCells

class DraftError(Exception):
  def __init__(self, message, ephemeral=True):
    super().__init__(message)
    self.ephemeral = ephemeral


def recover_state():
  try:
    with open("state.json", "r") as file:
      state = eval(file.read())

      players = []
      for player_state in state["players"]:
        player = Player(discord_id=player_state["discord_id"])
        player.player_username = player_state["player_username"]
        player.is_captain = player_state["is_captain"]
        player.rank = player_state["rank"]
        players.append(player)
      
      teams = []
      for team_state in state["teams"]:
        captain = next(player for player in players if player.discord_id == team_state["captain"])
        team = Team(captain=captain)
        team.proxy_discord_id = team_state["proxy_discord_id"]
        team.players = [next(player for player in players if player.discord_id == discord_id) for discord_id in team_state["players"]]

        for player in team.players:
          player.team = team

        teams.append(team)

      draft = Draft(teams, players, state["team_size"], state["timer"])
      draft.queue = [next(team for team in teams if team.captain.discord_id == discord_id) for discord_id in state["queue"]]
      draft.current_index = state["current_index"]
      draft.finished = state["finished"]
      
      draft.push_to_spreadsheet()

      return draft
  except FileNotFoundError:
    return None


def create_draft(player_infos: List[tuple], team_size: int, timer: int):
  teams = []
  players = []
  for player_info in player_infos:
    osu_playername, discord_id, is_captain, proxy_discord_id, rank = player_info
    player = Player(discord_id=discord_id)
    player.player_username = osu_playername
    player.rank = rank
    players.append(player)
    if is_captain:
      team = Team(captain=player)
      teams.append(team)
      if proxy_discord_id:
        team.proxy_discord_id = proxy_discord_id

  draft = Draft(teams, players, team_size, timer)
  return draft


class Draft:
  teams: List[Team]
  players: List[Player]
  team_size: int
  timer: int

  queue: List[Team] = []
  history: List[Action] = []

  current_index = 0

  finished = False

  def __init__(self, teams: List[Team], players: List[Player], team_size: int, timer: int):
    self.teams = teams
    self.players = players
    self.team_size = team_size
    self.timer = timer

  def push_to_spreadsheet(self):
    if SPREADSHEET_PUSH:
      from src.utils.google import writeCell
      teams = []
      for team in self.teams:
        players = team.players + [None] * (self.team_size - len(team.players))
        teams.append([player.player_username if player else "" for player in players])
      writeCells(SPREADSHEET_SHEET_NAME, f"{SPREADSHEET_START_COL}{SPREADSHEET_START_ROW}", teams)

  def save_state(self):
    self.push_to_spreadsheet()
    with open("state.json", "+w") as file:
      state = self.to_json()
      file.write(str(state))

  def to_json(self):
    return {
      "teams": [team.to_json() for team in self.teams],
      "players": [player.to_json() for player in self.players],
      "team_size": self.team_size,
      "timer": self.timer,
      "queue": [team.captain.discord_id for team in self.queue],
      "current_index": self.current_index,
      "finished": self.finished
    }

  def get_effective_index(self, index):
    if (index // len(self.teams)) % 2 == 0:
      return index % len(self.teams)
    else:
      return len(self.teams) - (index % len(self.teams)) - 1
    
  def _generate_queue_snake(self):
    for i in range(self.team_size-1):
      reverse = -1 if i % 2 == 1 else 1
      self.queue += self.teams[::reverse]

  def _generate_queue_repeated(self):
    for i in range(self.team_size-1):
      self.queue += self.teams
    
  def _generate_queue(self):
    self.queue = []
    if ORDERING_METHOD == "snake":
      self._generate_queue_snake()
    elif ORDERING_METHOD == "repeated":
      self._generate_queue_repeated()
    else:
      raise DraftError(trans("INVALID_ORDERING_METHOD", method=ORDERING_METHOD))

  def start(self):
    self.current_index = 0
    
    self._generate_queue()
    self.save_state()

  def execute_action(self, action: Action):
    action.execute()
    self.history.insert(0, action)
    self.save_state()

  def undo_action(self, action: Action):
    action.undo()
    self.history.remove(action)
    self.save_state()

  def push_back(self) -> Team:
    # the current index is pushed to the back of the current part of the queue

    team = self.queue[self.current_index]
    self.execute_action(PushBackAction(self, team))

    return self.queue[self.current_index]

  def get_draftable_players(self):
    return [player for player in self.players if player.team is None]
  
  def start_timer(self) -> Team | None:
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))
    
    if self.current_index > len(self.queue) - 1:
      self.execute_action(FinishDraftAction(self))
      return None
    
    return self.queue[self.current_index]

  def pick_player(self, captain_id, discord_id=None, player_username=None) -> tuple[Team, Player]:
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))
    
    team = next(team for team in self.teams if team.captain.discord_id == captain_id)
    player = next(player for player in self.players if (discord_id and player.discord_id == discord_id) or (player_username and player.player_username.lower() == player_username.lower()))

    if player is None:
      raise DraftError(trans("PLAYER_NOT_FOUND", player=discord_id), ephemeral=False)
    
    if player.is_captain:
      raise DraftError(trans("CANNOT_PICK_CAPTAIN", player=player.player_username), ephemeral=False)

    if player.team is not None:
      raise DraftError(trans("PLAYER_ALREADY_PICKED", player=player.player_username), ephemeral=False)

    if len(team.players) >= self.team_size:
      raise DraftError(trans("ERROR_DESCRIPTION"))
    
    self.execute_action(PickAction(self, team, player))

    return team, player
  
  def add_proxy(self, captain_id, proxy_id):
    if self.finished:
      raise DraftError(trans("DRAFT_ALREADY_OVER"))

    if not any(
      team.captain.discord_id == captain_id
      for team in self.teams
    ):
      raise DraftError(trans("CAPTAIN_NOT_FOUND"))

    if any(
      team.captain.discord_id == proxy_id 
      for team in self.teams
    ):
      raise DraftError(trans("ALREADY_CAPTAIN", proxy_id=proxy_id))
    
    if any(
      team.proxy_discord_id == proxy_id
      for team in self.teams
    ):
      raise DraftError(trans("ALREADY_PROXY", proxy_id=proxy_id))

    team = next(team for team in self.teams if team.captain.discord_id == captain_id)
    self.execute_action(AddProxyAction(team, proxy_id))