#!/usr/bin/env python3
"""Launch the shared Firebird group GUI with all group sizes visible."""

from six_beetle_firebird_gui import App


if __name__ == '__main__':
    App(profile='all').mainloop()
