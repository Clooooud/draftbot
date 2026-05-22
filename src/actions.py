from abc import ABC, abstractmethod
from src.lang.i18n import translate as trans

class Action(ABC):

    executed: bool = False
    undone: bool = False

    def execute(self):
        self._do_exec()
        self.executed = True

    def undo(self):
        self._do_undo()
        self.undone = True

    @abstractmethod
    def undo_string(self):
        pass

    @abstractmethod
    def _do_exec(self):
        pass

    @abstractmethod
    def _do_undo(self) -> bool:
        pass


class PickAction(Action):
    def __init__(self, draft, team, player):
        self.draft = draft
        self.team = team
        self.player = player

    def _do_exec(self):
        self.team.players.append(self.player)
        self.player.team = self.team
        self.draft.current_index += 1

    def _do_undo(self):
        self.team.players.remove(self.player)
        self.player.team = None
        self.draft.current_index -= 1

    def undo_string(self):
        return trans("PICK_UNDO_STRING", captain=self.team.captain.display_username(), player=self.player.display_username())


class PushBackAction(Action):
    def __init__(self, draft, team):
        self.draft = draft
        self.team = team
        self.original_index = draft.queue.index(team)

    def _do_exec(self):
        self.draft.queue.insert(((self.draft.old_index // len(self.draft.teams)) + 1) * len(self.draft.teams), self.draft.queue[self.draft.old_index])
        del self.draft.queue[self.draft.old_index]

    def _do_undo(self):
        current_index = self.draft.queue.index(self.team)
        self.draft.queue.insert(self.original_index, self.draft.queue[current_index])
        del self.draft.queue[current_index + 1]

    def undo_string(self):
        return trans("PUSH_BACK_UNDO_STRING", captain=self.team.captain.display_username())

class FinishDraftAction(Action):
    def __init__(self, draft):
        self.draft = draft

    def _do_exec(self):
        self.draft.finished = True

    def _do_undo(self):
        self.draft.finished = False

    def undo_string(self):
        return trans("FINISH_DRAFT_UNDO_STRING")

class AddProxyAction(Action):
    def __init__(self, team, proxy_id):
        self.team = team
        self.proxy_id = proxy_id

    def _do_exec(self):
        self.team.proxy_discord_id = self.proxy_id

    def _do_undo(self):
        self.team.proxy_discord_id = None

    def undo_string(self):
        return trans("ADD_PROXY_UNDO_STRING", captain=self.team.captain.display_username(), proxy_id=self.proxy_id)