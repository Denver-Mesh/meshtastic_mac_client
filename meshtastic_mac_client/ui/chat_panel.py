from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit,
                             QHBoxLayout, QPushButton, QComboBox, QLabel)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor

class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.main = parent
        self.layout = QVBoxLayout(self)

        # Message History
        self.txt_history = QTextEdit()
        self.txt_history.setReadOnly(True)
        self.layout.addWidget(self.txt_history)

        # Input Area
        input_layout = QHBoxLayout()
        
        self.combo_channel = QComboBox()
        self.combo_channel.addItems(["Primary", "Secondary 1", "Secondary 2"])
        input_layout.addWidget(QLabel("Channel:"))
        input_layout.addWidget(self.combo_channel)

        self.txt_input = QTextEdit()
        self.txt_input.setMaximumHeight(80)
        input_layout.addWidget(self.txt_input)

        self.btn_send = QPushButton("Send")
        self.btn_send.clicked.connect(lambda: asyncio.create_task(self.send_message()))        input_layout.addWidget(self.btn_send)

        self.layout.addLayout(input_layout)

    def on_new_message(self, node_id, role, payload, channel):
        # Append message to history
        cursor = self.txt_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        role_color = "blue" if role == "USER" else "black"
        cursor.insertHtml(f"<b style='color:{role_color}'>[{node_id}]</b>: {payload}<br>")
        self.txt_history.setTextCursor(cursor)
        self.txt_history.ensureCursorVisible()

    async def send_message(self):
        text = self.txt_input.toPlainText()
        if not text:
            return
        
        # Determine channel index (0 for Primary, 1 for Sec 1, etc.)
        channel_idx = self.combo_channel.currentIndex()
        
        success = await self.main.manager.send_text(text, channel_idx)
        if success:
            self.txt_input.clear()

