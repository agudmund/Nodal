#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - main.py application launcher
# A minor UI for enjoying
# Built using a single shared braincell by Yours Truly and some intellectual assistance

import sys
from PySide6.QtWidgets import QApplication
from main_window import NodalApp


def main():
    app = QApplication(sys.argv)
    window = NodalApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
