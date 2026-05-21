from typing import List


class Team:
  captain: "Player"
  proxy_discord_id: str | None
  players: List["Player"]

  def __init__(self, captain: "Player"):
    self.captain = captain
    self.proxy_discord_id = None
    self.players = [captain]
    captain.is_captain = True
    captain.team = self

  def to_json(self):
    return {
      "captain": self.captain.discord_id,
      "proxy_discord_id": self.proxy_discord_id,
      "players": [player.discord_id for player in self.players]
    }

class Player:
  is_captain: bool
  player_id: str | None
  player_username: str | None
  discord_id: str
  team: Team | None
  rank: int | None

  def __init__(self, discord_id: str):
    self.player_id = None
    self.discord_id = discord_id
    self.team = None
    self.rank = None
    self.is_captain = False

  def display_username(self):
    return self.player_username.replace("-", "\-").replace("_", "\_") if self.player_username else self.discord_id

  def to_json(self):
    return {
      "player_id": self.player_id,
      "player_username": self.player_username,
      "discord_id": self.discord_id,
      "team": self.team.captain.discord_id if self.team else None,
      "is_captain": self.is_captain,
      "rank": self.rank
    }