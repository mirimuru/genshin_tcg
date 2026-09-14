from abc import ABC, abstractmethod


class CharacterDefinition(ABC):
    name = ""
    element = None
    max_hp = 10
    max_energy = 2

    @abstractmethod
    def normal_attack(self, game, player_id):
        pass

    @abstractmethod
    def elemental_skill(self, game, player_id):
        pass

    @abstractmethod
    def elemental_burst(self, game, player_id):
        pass