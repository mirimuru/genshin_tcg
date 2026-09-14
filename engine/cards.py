from abc import ABC, abstractmethod


class CardDefinition(ABC):
    name = ""
    cost = {}

    @abstractmethod
    def can_play(self, game, player_id) -> bool:
        pass

    @abstractmethod
    def play(self, game, player_id):
        pass