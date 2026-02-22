from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

class TelemetryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Setup Plot
        self.plot_widget = pg.PlotWidget(title="Battery Voltage & RSSI")
        self.plot_widget.showGrid(x=True, y=True)
        self.layout.addWidget(self.plot_widget)
        
        # Data Buffers
        self.x_data = np.arange(0, 50)
        self.y_batt = np.zeros(50)
        self.y_rssi = np.zeros(50)
        
        self.curve_batt = self.plot_widget.plot(self.x_data, self.y_batt, pen=pg.mkPen('b', width=2), name="Battery")
        self.curve_rssi = self.plot_widget.plot(self.x_data, self.y_rssi, pen=pg.mkPen('r', width=2), name="RSSI")
        
        self.plot_widget.addLegend()

        # Timer for simulation/updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(1000) # Update every second

    def update_plots(self):
        # Shift data
        self.y_batt = np.roll(self.y_batt, -1)
        self.y_rssi = np.roll(self.y_rssi, -1)
        
        # Add new random data (Simulated for demo)
        self.y_batt[-1] = np.random.uniform(3.5, 4.2)
        self.y_rssi[-1] = np.random.uniform(-60, -90)
        
        self.curve_batt.setData(self.y_batt)
        self.curve_rssi.setData(self.y_rssi)

