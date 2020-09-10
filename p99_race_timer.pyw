#!python3
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QAction,
                             QFileDialog, QVBoxLayout, QWidget, QHBoxLayout,
                             QPushButton)
from PyQt5.QtCore import QThread, pyqtSignal
import pathlib
from datetime import datetime, timezone
import re
import winsound

class ParserThread(QThread):
    roll_signal = pyqtSignal(int, datetime)
    fte_signal = pyqtSignal(str, str, datetime)

    def __init__(self):
        super().__init__()
        self.fp = None

    def run(self):
        roll_pattern = r'\[.+?(?=\])] \*\*It could have been any number from 0 to 1000, but this time it turned up a (\d{1,4}).'
        fte_pattern = r'\[.+?(?=\])] (.+?(?=engages))engages ([a-zA-Z]+)'
        while True:
            line = self.fp.readline()
            if line:
                roll_match = re.match(roll_pattern, line)
                if roll_match:
                    valid_start = int(roll_match.group(1))
                    if valid_start >= 900:
                        now = datetime.now(timezone.utc)
                        self.roll_signal.emit(valid_start, now)
                fte_match = re.match(fte_pattern, line)
                if fte_match:
                    now = datetime.now(timezone.utc)
                    self.fte_signal.emit(fte_match.group(1), fte_match.group(2), now)
            else:
                continue

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        menu = self.menuBar()
        file_menu = menu.addMenu('&File')
        select_file = QAction('Select Log', parent=file_menu)
        select_file.triggered.connect(self.select_log)
        file_menu.addAction(select_file)

        self.selected_file = None

        self.parser_thread = ParserThread()
        self.parser_thread.roll_signal.connect(self.valid_roll)
        self.parser_thread.fte_signal.connect(self.valid_fte)

        roll_label = QLabel("Roll:")
        self.roll = QLabel('-')
        self.roll_time = QLabel('-')

        fte_label = QLabel("FTE:")
        self.fter = QLabel("-")
        self.fte_target = QLabel('-')
        self.fte_time = QLabel('-')

        self.overall_time = QLabel('Time:')
        self.overall_time_value = QLabel('-')

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.on_reset_click)

        self.started = False
        self.fted = False
        self.started_time = None

        first_row = QHBoxLayout()
        first_row.addWidget(roll_label)
        first_row.addWidget(self.roll)
        first_row.addWidget(self.roll_time)

        second_row = QHBoxLayout()
        second_row.addWidget(fte_label)
        second_row.addWidget(self.fter)
        second_row.addWidget(self.fte_target)
        second_row.addWidget(self.fte_time)

        third_row = QHBoxLayout()
        third_row.addWidget(self.overall_time)
        third_row.addWidget(self.overall_time_value)

        fourth_row = QHBoxLayout()
        fourth_row.addWidget(self.reset_button)

        layout = QVBoxLayout()
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        layout.addLayout(third_row)
        layout.addLayout(fourth_row)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def valid_roll(self, roll_value, roll_date):
        if not self.started:
            self.roll.setText(str(roll_value))
            self.roll_time.setText(roll_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            self.started_time = roll_date
            winsound.Beep(1000, 1000)
            self.started = True
        
    def valid_fte(self, fter, fte_target, fte_time):
        if self.started:
            self.fter.setText(fter)
            self.fte_target.setText(fte_target)
            self.fte_time.setText(fte_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            time_diff = fte_time - self.started_time
            self.overall_time_value.setText(str(time_diff))

    def on_reset_click(self):
        self.fted = False
        self.started = False
        self.roll.setText('-')
        self.roll_time.setText('-')
        self.fter.setText('-')
        self.fte_target.setText('-')
        self.fte_time.setText('-')
        self.overall_time_value.setText('-')
        self.started_time = None
    
    def select_log(self):
        dialog_file = QFileDialog.getOpenFileName(self, 'Open Log', '.', '*.txt')
        self.selected_file = pathlib.Path(dialog_file[0])
        if self.selected_file:
            fp = open(self.selected_file, 'r')
            while True:
                line = fp.readline()
                if line:
                    continue
                else:
                    print('done reading file')
                    break
        self.parser_thread.fp = fp
        self.parser_thread.start()

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
