# ui.modifier_keys
import pygame as py


def get_shift_ctrl():
    """(shift_held, ctrl_held) from the live keyboard modifier state - used
    by every panel that supports Shift/Ctrl+click item transfers."""
    mods = py.key.get_mods()
    return bool(mods & py.KMOD_SHIFT), bool(mods & py.KMOD_CTRL)
