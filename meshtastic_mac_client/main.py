import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

# Update this to use the full package name
from meshtastic_mac_client.ui.main_window import MainWindow
from meshtastic_mac_client.core.database import DatabaseManager

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(loop)
    window.show()

    try:
        with loop:
            loop.run_forever()
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()