#!/usr/bin/env python3
"""Launch the shared Firebird GUI filtered to two-beetle sessions."""

from six_beetle_firebird_gui import App


if __name__ == '__main__':
    App(profile='dyadic').mainloop()
