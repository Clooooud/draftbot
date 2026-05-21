# tests/test_draft.py

import pytest
from unittest.mock import patch, MagicMock

from src.draft import Draft, DraftError
from src.player import Player, Team


# =========================================================
# Fixtures
# =========================================================

@pytest.fixture
def players():
    captain1 = Player("captain1")
    captain2 = Player("captain2")

    player1 = Player("player1")
    player2 = Player("player2")
    player3 = Player("player3")

    captain1.player_username = "Captain1"
    captain2.player_username = "Captain2"
    player1.player_username = "Player1"
    player2.player_username = "Player2"
    player3.player_username = "Player3"

    return captain1, captain2, player1, player2, player3


@pytest.fixture
def draft(players):
    captain1, captain2, player1, player2, player3 = players

    team1 = Team(captain1)
    team2 = Team(captain2)

    return Draft(
        teams=[team1, team2],
        players=[captain1, captain2, player1, player2, player3],
        team_size=3,
        timer=60
    )


# =========================================================
# Initialization
# =========================================================

def test_draft_initialization(draft):
    assert len(draft.teams) == 2
    assert len(draft.players) == 5
    assert draft.team_size == 3
    assert draft.timer == 60
    assert draft.finished is False


# =========================================================
# JSON serialization
# =========================================================

def test_to_json(draft):
    data = draft.to_json()

    assert "teams" in data
    assert "players" in data
    assert data["team_size"] == 3
    assert data["timer"] == 60


# =========================================================
# Effective index
# =========================================================

def test_get_effective_index_forward(draft):
    assert draft.get_effective_index(0) == 0
    assert draft.get_effective_index(1) == 1


def test_get_effective_index_reverse(draft):
    assert draft.get_effective_index(2) == 1
    assert draft.get_effective_index(3) == 0


# =========================================================
# Queue generation
# =========================================================

@patch("src.draft.ORDERING_METHOD", "snake")
def test_generate_queue_snake(draft):
    draft._generate_queue()

    assert len(draft.queue) == 4

    assert draft.queue[0] == draft.teams[0]
    assert draft.queue[1] == draft.teams[1]

    assert draft.queue[2] == draft.teams[1]
    assert draft.queue[3] == draft.teams[0]


@patch("src.draft.ORDERING_METHOD", "repeated")
def test_generate_queue_repeated(draft):
    draft._generate_queue()

    assert len(draft.queue) == 4

    assert draft.queue[0] == draft.teams[0]
    assert draft.queue[1] == draft.teams[1]

    assert draft.queue[2] == draft.teams[0]
    assert draft.queue[3] == draft.teams[1]


@patch("src.draft.ORDERING_METHOD", "invalid")
def test_generate_queue_invalid_method(draft):
    with pytest.raises(DraftError):
        draft._generate_queue()


# =========================================================
# Start draft
# =========================================================

@patch.object(Draft, "save_state")
@patch("src.draft.ORDERING_METHOD", "snake")
def test_start(mock_save, draft):
    draft.start()

    assert draft.current_index == 0
    assert len(draft.queue) > 0

    mock_save.assert_called_once()


# =========================================================
# Execute / Undo action
# =========================================================

def test_execute_action(draft):
    action = MagicMock()

    with patch.object(draft, "save_state"):
        draft.execute_action(action)

    action.execute.assert_called_once()
    assert action in draft.history


def test_undo_action(draft):
    action = MagicMock()

    draft.history.append(action)

    with patch.object(draft, "save_state"):
        draft.undo_action(action)

    action.undo.assert_called_once()
    assert action not in draft.history


# =========================================================
# Start timer
# =========================================================

def test_start_timer_returns_team(draft):
    draft.queue = draft.teams.copy()

    team = draft.start_timer()

    assert team == draft.teams[0]


def test_start_timer_when_finished(draft):
    draft.finished = True

    with pytest.raises(DraftError):
        draft.start_timer()


@patch("src.draft.FinishDraftAction")
def test_start_timer_finishes_draft(mock_finish_action, draft):
    draft.queue = []
    draft.current_index = 1

    with patch.object(draft, "execute_action") as execute_mock:
        result = draft.start_timer()

    assert result is None
    execute_mock.assert_called_once()


# =========================================================
# Pick player
# =========================================================

@patch("src.draft.PickAction")
def test_pick_player_success(mock_pick_action, draft):
    with patch.object(draft, "execute_action") as execute_mock:
        team, player = draft.pick_player("captain1", "player1")

    assert team == draft.teams[0]
    assert player.discord_id == "player1"

    execute_mock.assert_called_once()


def test_pick_player_when_finished(draft):
    draft.finished = True

    with pytest.raises(DraftError):
        draft.pick_player("captain1", "player1")


def test_pick_player_cannot_pick_captain(draft):
    with pytest.raises(DraftError):
        draft.pick_player("captain1", "captain2")


def test_pick_player_already_picked(draft):
    player = next(p for p in draft.players if p.discord_id == "player1")

    player.team = draft.teams[0]

    with pytest.raises(DraftError):
        draft.pick_player("captain1", "player1")


def test_pick_player_team_full(draft):
    team = draft.teams[0]

    extra1 = Player("extra1")
    extra2 = Player("extra2")

    team.players.extend([extra1, extra2])

    with pytest.raises(DraftError):
        draft.pick_player("captain1", "player1")


# =========================================================
# Push back
# =========================================================

@patch("src.draft.PushBackAction")
def test_push_back(mock_push_back_action, draft):
    draft.queue = draft.teams.copy()

    with patch.object(draft, "execute_action") as execute_mock:
        result = draft.push_back()

    execute_mock.assert_called_once()
    assert result == draft.queue[draft.current_index]


# =========================================================
# Add proxy
# =========================================================

@patch("src.draft.AddProxyAction")
def test_add_proxy_success(mock_action, draft):
    with patch.object(draft, "execute_action") as execute_mock:
        draft.add_proxy("captain1", "proxy1")

    execute_mock.assert_called_once()


def test_add_proxy_finished(draft):
    draft.finished = True

    with pytest.raises(DraftError):
        draft.add_proxy("captain1", "proxy1")


def test_add_proxy_captain_not_found(draft):
    with pytest.raises(DraftError):
        draft.add_proxy("unknown", "proxy1")


def test_add_proxy_already_captain(draft):
    with pytest.raises(DraftError):
        draft.add_proxy("captain1", "captain2")


def test_add_proxy_already_proxy(draft):
    draft.teams[0].proxy_discord_id = "proxy1"

    with pytest.raises(DraftError):
        draft.add_proxy("captain2", "proxy1")