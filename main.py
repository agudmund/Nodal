import sys
from PySide6.QtWidgets import QApplication
from main_window import NodalApp


def main():
    app = QApplication(sys.argv)
    window = NodalApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
