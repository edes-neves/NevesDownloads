#!/usr/bin/env python3

"""
Neves Downloads - Ponto de entrada principal.
"""

import sys

from app.ui.main_window import NevesDownloadsApp

if __name__ == "__main__":
    app = NevesDownloadsApp()
    app.mainloop()
    sys.exit(0)
