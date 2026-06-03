"""
Compatibility wrapper for legacy automation gesture imports.
New gesture control lives in the dedicated `gesture` package.
"""

from gesture import GestureController

__all__ = ["GestureController"]
