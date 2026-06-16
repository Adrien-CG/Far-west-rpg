"""Compatibilite temporaire.

Le code reel de l'interface vit maintenant dans `ui.app`.
"""

from ui.app import GameApp, launch_app

__all__ = ["GameApp", "launch_app"]