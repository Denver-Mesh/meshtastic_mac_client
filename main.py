import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # 1. Create the QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Native macOS feel

    # 2. Create the Event Loop
    # qasync bridges the asyncio event loop with Qt's event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Create and Show the Main Window
    window = MainWindow()
    window.show()

    # 4. Run the application
    # We use 'with loop' to ensure the loop runs until the app closes
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()

