from __future__ import annotations

import logging
import subprocess

from gi.repository import Gdk, GdkX11, Gio  # type: ignore[attr-defined]

from ulauncher.utils.environment import IS_X11

logger = logging.getLogger()


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    display = Gdk.Display.get_default()
    assert display

    if use_mouse_position:
        try:
            x11_display = GdkX11.X11Display.get_default()
            seat = x11_display.get_default_seat()
            (_, x, y) = seat.get_pointer().get_position()
            return display.get_monitor_at_point(x, y)
        except Exception:
            logger.exception("Could not get monitor with X11. Defaulting to first or primary monitor")

    return display.get_primary_monitor() or display.get_monitor(0)


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling
    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")


def try_raise_app(desktop_entry: str) -> bool:
    """
    Try to raise an app by id (str) and return whether successful
    Currently only supports X11 via EWMH/Xlib
    """
    logger.info("trying to raise %s", desktop_entry)
    try:
        p = subprocess.run(
            ["kdotool", "search", "--limit", "1", "--class", desktop_entry],
            check=True,
            stdout=subprocess.PIPE,
        )
        # if nothing shows up, return code is still 0
        if len(p.stdout) == 0:
            return False
        subprocess.run(["kdotool", "windowactivate", p.stdout.strip()], check=True)
        return True  # noqa: TRY300
    except subprocess.CalledProcessError:
            logger.exception("Exception while trying to activate window with kdotool")

    return False
