from PyQt5.QtWidgets import QApplication
import sys

from .main_window import ModernMainWindow


def run(argv=None):
    """Run the GUI application.

    Accepts an optional argv list for testing. Returns application exit code.
    """
    if argv is None:
        argv = sys.argv

    app = QApplication(argv)

    window = ModernMainWindow()
    window.show()

    return app.exec_()
