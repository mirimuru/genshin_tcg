from engine.game import Game
from engine.effect_api import install as _install_effect_api

_install_effect_api(Game)

__all__ = ["Game"]
