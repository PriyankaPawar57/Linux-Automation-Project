import sys
import os
import csv
import re
from datetime import datetime

import paramiko
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QHeaderView
)

from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter


# ============================================================
# FILE SETTINGS
# ============================================================

REPORT_FOLDER = "reports"

CSV_FILE = os.path.join(
    REPORT_FOLDER,
    "system_report.csv"
)


# ============================================================
# MAIN DASHBOARD
# ============================================================

class LinuxDashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        # SSH object
        self.ssh = None

        # DataFrames
        self.df = pd.DataFrame()
        self.previous_filtered_df = pd.DataFrame()
        self.visualization_filtered_df = pd.DataFrame()

        # Window settings
        self.setWindowTitle(
            "Linux System Monitoring Dashboard"
        )

        self.resize(
            1400,
            900
        )

        self.setMinimumSize(
            1100,
            750
        )

        # Create reports folder
        os.makedirs(
            REPORT_FOLDER,
            exist_ok=True
        )

        # Create UI
        self.setup_ui()

        # Load records
        self.load_old_records()


    # ========================================================
    # SETUP UI
    # ========================================================

    def setup_ui(self):

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #eef3f8;")

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            20,
            15,
            20,
            20
        )

        main_layout.setSpacing(
            10
        )


        # ====================================================
        # MAIN TITLE
        # ====================================================

        title = QLabel(
            "Linux System Monitoring Dashboard"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 32px;
                font-weight: bold;
                padding: 15px;
            }
            """
        )

        main_layout.addWidget(
            title
        )


        # ====================================================
        # SSH CONNECTION
        # ====================================================

        connection_group = QGroupBox(
            "SSH Connection"
        )

        connection_group.setStyleSheet(
            """
            QGroupBox {
                font-size: 20px;
                font-weight: bold;
                margin-top: 10px;
                padding-top: 15px;
            }

            QGroupBox::title {
                left: 10px;
                padding: 0 5px;
            }
            """
        )

        connection_layout = QVBoxLayout()


        # ---------------- IP ADDRESS ----------------

        ip_layout = QHBoxLayout()

        ip_label = QLabel(
            "IP Address:"
        )

        ip_label.setFixedWidth(
            150
        )

        ip_label.setStyleSheet(
            "font-size: 18px;"
        )

        self.ip_input = QLineEdit()

        self.ip_input.setPlaceholderText(
            "Example: 192.168.1.10"
        )

        self.ip_input.setMinimumHeight(
            38
        )

        self.ip_input.setStyleSheet(
            "font-size: 17px;"
        )

        ip_layout.addWidget(
            ip_label
        )

        ip_layout.addWidget(
            self.ip_input
        )


        # ---------------- USERNAME ----------------

        username_layout = QHBoxLayout()

        username_label = QLabel(
            "Username:"
        )

        username_label.setFixedWidth(
            150
        )

        username_label.setStyleSheet(
            "font-size: 18px;"
        )

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Enter Username"
        )

        self.username_input.setMinimumHeight(
            38
        )

        self.username_input.setStyleSheet(
            "font-size: 17px;"
        )

        username_layout.addWidget(
            username_label
        )

        username_layout.addWidget(
            self.username_input
        )


        # ---------------- PASSWORD ----------------

        password_layout = QHBoxLayout()

        password_label = QLabel(
            "Password:"
        )

        password_label.setFixedWidth(
            150
        )

        password_label.setStyleSheet(
            "font-size: 18px;"
        )

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Enter Password"
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.password_input.setMinimumHeight(
            38
        )

        self.password_input.setStyleSheet(
            "font-size: 17px;"
        )

        password_layout.addWidget(
            password_label
        )

        password_layout.addWidget(
            self.password_input
        )


        # ---------------- CONNECT BUTTON ----------------

        self.connect_button = QPushButton(
            "Submit"
        )

        self.connect_button.setFixedSize(
            160,
            42
        )

        self.connect_button.setStyleSheet(
            """
            QPushButton {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.connect_button.clicked.connect(
            self.connect_ssh
        )


        # Add layouts

        connection_layout.addLayout(
            ip_layout
        )

        connection_layout.addLayout(
            username_layout
        )

        connection_layout.addLayout(
            password_layout
        )

        connection_layout.addWidget(
            self.connect_button,
            alignment=Qt.AlignCenter
        )

        connection_group.setLayout(
            connection_layout
        )

        main_layout.addWidget(
            connection_group
        )


        # ====================================================
        # SSH STATUS
        # ====================================================

        self.session_status = QLabel(
            "⚪ No SSH Session"
        )

        self.session_status.setAlignment(
            Qt.AlignCenter
        )

        self.session_status.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: gray;
                padding: 8px;
            }
            """
        )

        main_layout.addWidget(
            self.session_status
        )


        # ====================================================
        # LINUX COMMANDS
        # ====================================================

        command_group = QGroupBox(
            "Linux Commands"
        )

        command_group.setStyleSheet(
            """
            QGroupBox {
                font-size: 20px;
                font-weight: bold;
                margin-top: 10px;
                padding-top: 15px;
            }

            QGroupBox::title {
                left: 10px;
                padding: 0 5px;
            }
            """
        )

        command_layout = QHBoxLayout()


        command_label = QLabel(
            "Commands:"
        )

        command_label.setStyleSheet(
            "font-size: 18px;"
        )


        # ====================================================
        # COMMAND DROPDOWN
        # ====================================================

        self.command_combo = QComboBox()

        self.command_combo.setMinimumWidth(
            350
        )

        self.command_combo.setMinimumHeight(
            42
        )

        self.command_combo.setStyleSheet(
            """
            QComboBox {
                font-size: 17px;
                padding: 5px;
            }
            """
        )


        # All Commands

        self.command_combo.addItem(
            "All Commands"
        )


        # Linux Commands

        commands = [
            "hostname",
            "hostname -I",
            "uptime",
            "free -h",
            "df -h",
            "vmstat",
            "top -bn1"
        ]

        for command in commands:

            self.command_combo.addItem(
                command
            )


        # Execute Button

        self.execute_button = QPushButton(
            "Execute"
        )

        self.execute_button.setFixedSize(
            150,
            42
        )

        self.execute_button.setStyleSheet(
            """
            QPushButton {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.execute_button.clicked.connect(
            self.execute_command
        )


        command_layout.addWidget(
            command_label
        )

        command_layout.addWidget(
            self.command_combo
        )

        command_layout.addWidget(
            self.execute_button
        )

        command_layout.addStretch()

        command_group.setLayout(
            command_layout
        )

        main_layout.addWidget(
            command_group
        )


        # ====================================================
        # TABS
        # ====================================================

        self.tabs = QTabWidget()

        self.tabs.setStyleSheet(
            """
            QTabBar::tab {
                font-size: 16px;
                padding: 10px 18px;
                min-width: 180px;
            }
                                   
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            """
        )

        main_layout.addWidget(
            self.tabs
        )


        # ====================================================
        # CREATE TABS
        # ====================================================

        self.create_live_output_tab()

        self.create_previous_records_tab()

        self.create_visualization_tab()


    # ========================================================
    # LIVE OUTPUT TAB
    # ========================================================

    def create_live_output_tab(self):

        output_tab = QWidget()

        output_layout = QVBoxLayout(
            output_tab
        )

        title = QLabel(
            "Live Output"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 23px;
                font-weight: bold;
            }
            """
        )

        output_layout.addWidget(
            title
        )


        self.output_box = QTextEdit()

        self.output_box.setReadOnly(
            True
        )

        self.output_box.setStyleSheet(
            """
            QTextEdit {
                font-size: 15px;
                font-family: Consolas;
            }
            """
        )

        output_layout.addWidget(
            self.output_box
        )


        self.tabs.addTab(
            output_tab,
            "Live Output"
        )


    # ========================================================
    # PREVIOUS RECORDS TAB
    # ========================================================

    def create_previous_records_tab(self):

        records_tab = QWidget()

        records_layout = QVBoxLayout(
            records_tab
        )

        title = QLabel(
            "Previous Monitoring Records"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 23px;
                font-weight: bold;
            }
            """
        )

        records_layout.addWidget(
            title
        )


        # ====================================================
        # FILTERS
        # ====================================================

        filter_layout = QHBoxLayout()


        date_label = QLabel(
            "Select Date:"
        )

        date_label.setStyleSheet(
            "font-size: 18px;"
        )


        self.date_combo = QComboBox()

        self.date_combo.setMinimumWidth(
            180
        )

        self.date_combo.setMinimumHeight(
            38
        )

        self.date_combo.setStyleSheet(
            "font-size: 17px;"
        )

        self.date_combo.addItem(
            "All Dates"
        )

        self.date_combo.currentTextChanged.connect(
            self.apply_filters
        )


        command_label = QLabel(
            "Command:"
        )

        command_label.setStyleSheet(
            "font-size: 18px;"
        )


        self.record_command_combo = QComboBox()

        self.record_command_combo.setMinimumWidth(
            220
        )

        self.record_command_combo.setMinimumHeight(
            38
        )

        self.record_command_combo.setStyleSheet(
            "font-size: 17px;"
        )

        self.record_command_combo.addItem(
            "All Commands"
        )

        self.record_command_combo.currentTextChanged.connect(
            self.apply_filters
        )


        self.refresh_records_button = QPushButton(
            "🔄 Refresh Records"
        )

        self.refresh_records_button.setMinimumHeight(
            38
        )

        self.refresh_records_button.setStyleSheet(
            "font-size: 17px;"
        )

        self.refresh_records_button.clicked.connect(
            self.load_old_records
        )


        filter_layout.addWidget(
            date_label
        )

        filter_layout.addWidget(
            self.date_combo
        )

        filter_layout.addWidget(
            command_label
        )

        filter_layout.addWidget(
            self.record_command_combo
        )

        filter_layout.addWidget(
            self.refresh_records_button
        )

        filter_layout.addStretch()

        records_layout.addLayout(
            filter_layout
        )


        # ====================================================
        # TABLE
        # ====================================================

        self.records_table = QTableWidget()

        self.records_table.setColumnCount(
            4
        )

        self.records_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Time",
                "Command",
                "Output"
            ]
        )

        self.records_table.setStyleSheet(
            """
            QTableWidget {
                font-size: 15px;
            }

            QHeaderView::section {
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
            """
        )


        header = self.records_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.Stretch
        )


        records_layout.addWidget(
            self.records_table
        )


        self.tabs.addTab(
            records_tab,
            "Previous Records"
        )


    # ========================================================
    # VISUALIZATION TAB
    # ========================================================

    def create_visualization_tab(self):

        visualization_tab = QWidget()

        layout = QVBoxLayout(
            visualization_tab
        )


        title = QLabel(
            "📊 System Data Visualization"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
            """
        )

        layout.addWidget(
            title
        )


        # ====================================================
        # DATE / TIME SELECTION
        # ====================================================

        selection_layout = QHBoxLayout()

        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-size: 18px;")

        self.visualization_date_combo = QComboBox()
        self.visualization_date_combo.setMinimumWidth(180)
        self.visualization_date_combo.setMinimumHeight(38)
        self.visualization_date_combo.setStyleSheet("font-size: 17px;")
        self.visualization_date_combo.addItem("Select Date")

        time_label = QLabel("Time:")
        time_label.setStyleSheet("font-size: 18px;")

        self.visualization_time_combo = QComboBox()
        self.visualization_time_combo.setMinimumWidth(180)
        self.visualization_time_combo.setMinimumHeight(38)
        self.visualization_time_combo.setStyleSheet("font-size: 17px;")
        self.visualization_time_combo.addItem("Select Time")

        selection_layout.addWidget(date_label)
        selection_layout.addWidget(self.visualization_date_combo)
        selection_layout.addWidget(time_label)
        selection_layout.addWidget(self.visualization_time_combo)
        selection_layout.addStretch()

        layout.addLayout(selection_layout)

        self.visualization_date_combo.currentTextChanged.connect(
            self.populate_visualization_times
        )
        self.visualization_time_combo.currentTextChanged.connect(
            self.apply_visualization_date_time_filter
        )


        # ====================================================
        # CHART BUTTONS
        # ====================================================

        button_layout = QHBoxLayout()


        self.all_chart_button = QPushButton(
            "📊 Overall System Usage"
        )

        self.cpu_chart_button = QPushButton(
            "🖥️ CPU Usage (%)"
        )

        self.ram_chart_button = QPushButton(
            "💾 RAM Usage (%)"
        )

        self.disk_chart_button = QPushButton(
            "💿 Disk Usage (%)"
        )

        self.timeline_chart_button = QPushButton(
            "📈 Monitoring Timeline"
        )

        self.command_chart_button = QPushButton(
            "📋 Command Analysis"
        )


        buttons = [
            self.all_chart_button,
            self.cpu_chart_button,
            self.ram_chart_button,
            self.disk_chart_button,
            self.timeline_chart_button,
            self.command_chart_button
        ]


        for button in buttons:

            button.setMinimumHeight(
                42
            )

            button.setStyleSheet(
                """
                QPushButton {
                    font-size: 15px;
                    font-weight: bold;
                    padding: 8px 10px;
                    border: 1px solid #cbd6e2;
                    border-radius: 6px;
                    background-color: #f4f7fa;
                }
                QPushButton:hover {
                    background-color: #e6eef7;
                }
                QPushButton:pressed {
                    background-color: #d7e3f0;
                }
                """
            )

            button_layout.addWidget(
                button
            )


        layout.addLayout(
            button_layout
        )


        # ====================================================
        # BUTTON EVENTS
        # ====================================================

        self.command_chart_button.clicked.connect(
            self.show_command_chart
        )

        self.timeline_chart_button.clicked.connect(
            self.show_timeline_chart
        )

        self.cpu_chart_button.clicked.connect(
            self.show_cpu_chart
        )

        self.ram_chart_button.clicked.connect(
            self.show_ram_chart
        )

        self.disk_chart_button.clicked.connect(
            self.show_disk_chart
        )

        self.all_chart_button.clicked.connect(
            self.show_all_system_charts
        )


        # ====================================================
        # MATPLOTLIB
        # ====================================================

        self.figure = Figure()

        self.canvas = FigureCanvas(
            self.figure
        )

        layout.addWidget(
            self.canvas
        )


        self.tabs.addTab(
            visualization_tab,
            "Data Visualization"
        )


    # ========================================================
    # VISUALIZATION DATE / TIME FILTERS
    # NOTE: Visualization uses its own filter dataframe and is
    # completely independent from Previous Records filters.
    # ========================================================

    def populate_visualization_dates(self):

        if not hasattr(self, "visualization_date_combo"):
            return

        current_date = self.visualization_date_combo.currentText()

        self.visualization_date_combo.blockSignals(True)
        self.visualization_date_combo.clear()
        self.visualization_date_combo.addItem("Select Date")

        if not self.df.empty and "Date" in self.df.columns:
            dates = sorted(
                self.df["Date"].dropna().astype(str).unique(),
                key=lambda x: datetime.strptime(x, "%d-%m-%Y") if x and x != "nan" else datetime.min,
                reverse=True
            )
            for date_value in dates:
                self.visualization_date_combo.addItem(date_value)

        index = self.visualization_date_combo.findText(current_date)
        if index >= 0:
            self.visualization_date_combo.setCurrentIndex(index)
        elif self.visualization_date_combo.count() > 1:
            self.visualization_date_combo.setCurrentIndex(1)

        selected_date = self.visualization_date_combo.currentText()
        self.visualization_date_combo.blockSignals(False)

        self.populate_visualization_times(selected_date)


    def populate_visualization_times(self, selected_date):

        if not hasattr(self, "visualization_time_combo"):
            return

        current_time = self.visualization_time_combo.currentText()

        self.visualization_time_combo.blockSignals(True)
        self.visualization_time_combo.clear()
        self.visualization_time_combo.addItem("Select Time")

        if (
            selected_date != "Select Date"
            and not self.df.empty
            and "Date" in self.df.columns
            and "Time" in self.df.columns
        ):
            date_data = self.df[
                self.df["Date"].astype(str).str.strip() == str(selected_date).strip()
            ]

            times = sorted(
                date_data["Time"].dropna().astype(str).str.strip().unique(),
                reverse=True
            )

            for time_value in times:
                if time_value and time_value != "nan":
                    self.visualization_time_combo.addItem(time_value)

        index = self.visualization_time_combo.findText(current_time)
        if index >= 0:
            self.visualization_time_combo.setCurrentIndex(index)
        elif self.visualization_time_combo.count() > 1:
            self.visualization_time_combo.setCurrentIndex(1)

        self.visualization_time_combo.blockSignals(False)

        self.apply_visualization_date_time_filter()


    def apply_visualization_date_time_filter(self):

        if self.df.empty:
            self.visualization_filtered_df = self.df.copy()
            return

        selected_date = self.visualization_date_combo.currentText()
        selected_time = self.visualization_time_combo.currentText()

        filtered = self.df.copy()

        if selected_date != "Select Date" and "Date" in filtered.columns:
            filtered = filtered[
                filtered["Date"].astype(str).str.strip() == str(selected_date).strip()
            ]

        if selected_time != "Select Time" and "Time" in filtered.columns:
            filtered = filtered[
                filtered["Time"].astype(str).str.strip() == str(selected_time).strip()
            ]

        self.visualization_filtered_df = filtered.copy()


    # ========================================================
    # SSH CONNECTION
    # ========================================================

    def connect_ssh(self):

        ip_address = (
            self.ip_input.text().strip()
        )

        username = (
            self.username_input.text().strip()
        )

        password = (
            self.password_input.text().strip()
        )


        if not ip_address:

            QMessageBox.warning(
                self,
                "Missing IP Address",
                "Please enter IP Address."
            )

            return


        if not username:

            QMessageBox.warning(
                self,
                "Missing Username",
                "Please enter Username."
            )

            return


        if not password:

            QMessageBox.warning(
                self,
                "Missing Password",
                "Please enter Password."
            )

            return


        try:

            # 🟡 Connecting

            self.session_status.setText(
                "🟡 Connecting to Linux System..."
            )

            self.session_status.setStyleSheet(
                """
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: orange;
                    padding: 8px;
                }
                """
            )

            QApplication.processEvents()


            # SSH Client

            self.ssh = paramiko.SSHClient()

            self.ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )


            # Connect

            self.ssh.connect(
                hostname=ip_address,
                username=username,
                password=password,
                timeout=10
            )


            # 🟢 SUCCESS

            self.session_status.setText(
                "🟢 SSH Connected"
            )

            self.session_status.setStyleSheet(
                """
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: green;
                    padding: 8px;
                }
                """
            )

            # Automatically show the Live Output tab after SSH connection
            self.tabs.setCurrentIndex(0)
            self.output_box.clear()
            self.output_box.append("🟢 SSH Connected Successfully!\n")
            QApplication.processEvents()


            QMessageBox.information(
                self,
                "SSH Connected",
                "🟢 SSH Connected Successfully!"
            )


        except paramiko.AuthenticationException:

            self.ssh = None

            self.session_status.setText(
                "🔴 SSH Authentication Failed"
            )

            self.session_status.setStyleSheet(
                """
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: red;
                    padding: 8px;
                }
                """
            )


            QMessageBox.critical(
                self,
                "Authentication Failed",
                "Please check Username and Password."
            )


        except Exception as e:

            self.ssh = None

            self.session_status.setText(
                "🔴 SSH Connection Failed"
            )

            self.session_status.setStyleSheet(
                """
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: red;
                    padding: 8px;
                }
                """
            )


            QMessageBox.critical(
                self,
                "SSH Connection Error",
                str(e)
            )


    # ========================================================
    # EXECUTE COMMAND
    # ========================================================

    def execute_command(self):

        if self.ssh is None:

            QMessageBox.warning(
                self,
                "SSH Not Connected",
                "Please connect SSH first."
            )

            return


        selected_command = (
            self.command_combo.currentText()
        )


        # ====================================================
        # ALL COMMANDS
        # ====================================================

        if selected_command == "All Commands":

            commands = [
                "hostname",
                "hostname -I",
                "uptime",
                "free -h",
                "df -h",
                "vmstat",
                "top -bn1"
            ]

        else:

            commands = [
                selected_command
            ]


        self.output_box.clear()


        for command in commands:

            self.run_single_command(
                command
            )


    # ========================================================
    # RUN SINGLE COMMAND
    # ========================================================

    def run_single_command(
        self,
        command
    ):

        try:

            self.output_box.append(
                "=" * 70
            )

            self.output_box.append(
                f"COMMAND: {command}"
            )

            self.output_box.append(
                "=" * 70
            )

            QApplication.processEvents()


            stdin, stdout, stderr = (
                self.ssh.exec_command(
                    command
                )
            )


            output = stdout.read().decode(
                errors="ignore"
            )


            error = stderr.read().decode(
                errors="ignore"
            )


            if error.strip():

                output += (
                    "\nERROR:\n"
                    + error
                )


            self.output_box.append(
                output
            )


            # Save CSV

            self.save_record(
                command,
                output
            )


        except Exception as e:

            self.output_box.append(
                f"\n❌ Error: {str(e)}"
            )


    # ========================================================
    # SAVE RECORD
    # ========================================================

    def save_record(
        self,
        command,
        output
    ):

        now = datetime.now()


        date_value = now.strftime(
            "%d-%m-%Y"
        )


        time_value = now.strftime(
            "%H:%M:%S"
        )


        file_exists = os.path.exists(
            CSV_FILE
        )


        with open(
            CSV_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(
                file
            )


            if not file_exists:

                writer.writerow(
                    [
                        "Date",
                        "Time",
                        "Command",
                        "Output"
                    ]
                )


            writer.writerow(
                [
                    date_value,
                    time_value,
                    command,
                    output.replace(
                        "\n",
                        " | "
                    )
                ]
            )


        # Reload data

        self.load_old_records()


    # ========================================================
    # LOAD OLD RECORDS
    # ========================================================

    def load_old_records(self):

        if not os.path.exists(
            CSV_FILE
        ):

            return


        try:

            self.df = pd.read_csv(
                CSV_FILE
            )


            if self.df.empty:

                return


            # Convert to string

            for column in [
                "Date",
                "Time",
                "Command",
                "Output"
            ]:

                if column in self.df.columns:

                    self.df[column] = (
                        self.df[column]
                        .astype(str)
                    )


            # Populate filters

            self.populate_filters()

            # Populate Date/Time selectors in Data Visualization
            self.populate_visualization_dates()


            # Apply filters

            self.apply_filters()


        except Exception as e:

            print(
                "Loading Error:",
                e
            )


    # ========================================================
    # POPULATE FILTERS
    # ========================================================

    def populate_filters(self):

        current_date = (
            self.date_combo.currentText()
        )

        current_command = (
            self.record_command_combo.currentText()
        )


        self.date_combo.blockSignals(
            True
        )

        self.record_command_combo.blockSignals(
            True
        )


        self.date_combo.clear()

        self.record_command_combo.clear()


        self.date_combo.addItem(
            "All Dates"
        )

        self.record_command_combo.addItem(
            "All Commands"
        )


        # ====================================================
        # DATES
        # ====================================================

        dates = sorted(
            self.df["Date"]
            .dropna()
            .unique(),
            reverse=True
        )


        for date in dates:

            self.date_combo.addItem(
                str(date)
            )


        # ====================================================
        # COMMANDS
        # ====================================================

        commands = sorted(
            self.df["Command"]
            .dropna()
            .unique()
        )


        for command in commands:

            self.record_command_combo.addItem(
                str(command)
            )


        # Restore old selection

        index = self.date_combo.findText(
            current_date
        )


        if index >= 0:

            self.date_combo.setCurrentIndex(
                index
            )


        index = self.record_command_combo.findText(
            current_command
        )


        if index >= 0:

            self.record_command_combo.setCurrentIndex(
                index
            )


        self.date_combo.blockSignals(
            False
        )

        self.record_command_combo.blockSignals(
            False
        )


    # ========================================================
    # APPLY FILTERS (PREVIOUS RECORDS ONLY)
    # NOTE: This filter is independent from Data Visualization.
    # ========================================================

    def apply_filters(self):

        if self.df.empty:

            return


        filtered = self.df.copy()


        selected_date = (
            self.date_combo.currentText()
        )

        selected_command = (
            self.record_command_combo.currentText()
        )


        # ====================================================
        # DATE FILTER
        # ====================================================

        if selected_date != "All Dates":

            filtered = filtered[
                filtered["Date"]
                == selected_date
            ]


        # ====================================================
        # COMMAND FILTER
        # ====================================================

        if selected_command != "All Commands":

            filtered = filtered[
                filtered["Command"]
                == selected_command
            ]


        self.previous_filtered_df = filtered.copy()


        self.display_records(
            filtered
        )


    # ========================================================
    # DISPLAY RECORDS
    # ========================================================

    def display_records(
        self,
        df
    ):

        self.records_table.setRowCount(
            0
        )


        if df.empty:

            return


        for _, row in df.iterrows():

            table_row = (
                self.records_table.rowCount()
            )


            self.records_table.insertRow(
                table_row
            )


            self.records_table.setItem(
                table_row,
                0,
                QTableWidgetItem(
                    str(row["Date"])
                )
            )


            self.records_table.setItem(
                table_row,
                1,
                QTableWidgetItem(
                    str(row["Time"])
                )
            )


            self.records_table.setItem(
                table_row,
                2,
                QTableWidgetItem(
                    str(row["Command"])
                )
            )


            self.records_table.setItem(
                table_row,
                3,
                QTableWidgetItem(
                    str(row["Output"])
                )
            )


    # ========================================================
    # COMMAND CHART
    # ========================================================

    def show_command_chart(self):

        if self.visualization_filtered_df.empty:

            self.no_data_message()

            return


        self.figure.clear()


        ax = self.figure.add_subplot(
            111
        )


        counts = (
            self.visualization_filtered_df["Command"]
            .value_counts()
        )


        # Give every command its own color
        color_map = {
            "hostname": "#4E79A7",
            "hostname -I": "#59A14F",
            "uptime": "#F28E2B",
            "free -h": "#E15759",
            "df -h": "#B07AA1",
            "vmstat": "#76B7B2",
            "top -bn1": "#EDC948"
        }

        bar_colors = [
            color_map.get(str(command), "#9C9C9C")
            for command in counts.index
        ]

        bars = ax.bar(
            counts.index,
            counts.values,
            color=bar_colors,
            edgecolor="#555555",
            linewidth=0.8
        )

        # Show record count above each bar
        for bar, count in zip(bars, counts.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(count),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )


        ax.set_title(
            "Command-wise Monitoring Records"
        )

        ax.set_xlabel(
            "Commands"
        )

        ax.set_ylabel(
            "Number of Records"
        )


        ax.tick_params(
            axis="x",
            rotation=25
        )


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # TIMELINE CHART
    # ========================================================

    def show_timeline_chart(self):

        if self.visualization_filtered_df.empty:

            self.no_data_message()

            return


        self.figure.clear()


        ax = self.figure.add_subplot(
            111
        )


        data = self.visualization_filtered_df.copy()


        data["DateTime"] = pd.to_datetime(
            data["Date"]
            + " "
            + data["Time"],
            format="%d-%m-%Y %H:%M:%S",
            errors="coerce"
        )


        data = data.dropna(
            subset=["DateTime"]
        )


        data = data.sort_values(
            "DateTime"
        )


        data["RecordNumber"] = range(
            1,
            len(data) + 1
        )


        ax.plot(
            data["DateTime"],
            data["RecordNumber"],
            marker="o"
        )


        ax.set_title(
            "Linux Monitoring Timeline"
        )

        ax.set_xlabel(
            "Date and Time"
        )

        ax.set_ylabel(
            "Record Number"
        )


        ax.tick_params(
            axis="x",
            rotation=30
        )


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # EXTRACT CPU DATA
    # ========================================================

    def extract_cpu_data(self):

        cpu_data = []


        for _, row in self.visualization_filtered_df.iterrows():

            command = str(
                row["Command"]
            )

            output = str(
                row["Output"]
            )


            # Only top command

            if "top" in command.lower():

                # Find idle CPU percentage
                #
                # Example:
                # %Cpu(s):  2.0 us, 1.0 sy,
                # 0.0 ni, 96.5 id, ...

                idle_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*id\b",
                    output,
                    re.IGNORECASE
                )


                if idle_match:

                    idle_cpu = float(
                        idle_match.group(1)
                    )


                    # Actual CPU Usage
                    usage = 100 - idle_cpu


                    # Keep value between 0 and 100

                    usage = max(
                        0,
                        min(
                            100,
                            usage
                        )
                    )


                    cpu_data.append(
                        usage
                    )


        return cpu_data


    # ========================================================
    # CPU CHART
    # ========================================================

    def show_cpu_chart(self):

        cpu_data = (
            self.extract_cpu_data()
        )


        self.figure.clear()


        ax = self.figure.add_subplot(
            111
        )


        if not cpu_data:

            ax.text(
                0.5,
                0.5,
                "CPU Usage data not available",
                ha="center",
                va="center",
                fontsize=16
            )

            ax.set_axis_off()


        else:

            ax.plot(
                range(
                    1,
                    len(cpu_data) + 1
                ),
                cpu_data,
                marker="o"
            )


            ax.set_title(
                "CPU Usage (%)"
            )

            ax.set_xlabel(
                "Monitoring Record"
            )

            ax.set_ylabel(
                "CPU Usage (%)"
            )

            ax.set_ylim(
                0,
                100
            )


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # CONVERT MEMORY VALUE TO BYTES
    # ========================================================

    def memory_to_bytes(
        self,
        value,
        unit
    ):

        try:

            value = float(value)

        except:

            return 0


        unit = unit.strip().lower()


        multipliers = {
            "": 1,
            "b": 1,
            "k": 1024,
            "kb": 1024,
            "ki": 1024,
            "kib": 1024,
            "m": 1024 ** 2,
            "mb": 1024 ** 2,
            "mi": 1024 ** 2,
            "mib": 1024 ** 2,
            "g": 1024 ** 3,
            "gb": 1024 ** 3,
            "gi": 1024 ** 3,
            "gib": 1024 ** 3,
            "t": 1024 ** 4,
            "tb": 1024 ** 4,
            "ti": 1024 ** 4,
            "tib": 1024 ** 4,
            "p": 1024 ** 5,
            "pb": 1024 ** 5,
            "pi": 1024 ** 5,
            "pib": 1024 ** 5
        }


        multiplier = multipliers.get(
            unit,
            1
        )


        return value * multiplier


    # ========================================================
    # EXTRACT RAM DATA
    # ========================================================

    def extract_ram_data(self):

        ram_data = []


        for _, row in self.visualization_filtered_df.iterrows():

            command = str(
                row["Command"]
            )

            output = str(
                row["Output"]
            )


            # Only free -h command

            if "free" in command.lower():

                # Find Mem line
                #
                # Example:
                # Mem:  3.8Gi  1.2Gi  2.6Gi
                #
                # Because CSV stores newlines as " | ",
                # the complete output can still be searched.

                match = re.search(
                    r"Mem:\s*"
                    r"([\d.]+)\s*([KMGTPE]?i?B?)\s+"
                    r"([\d.]+)\s*([KMGTPE]?i?B?)",
                    output,
                    re.IGNORECASE
                )


                if match:

                    total_value = float(
                        match.group(1)
                    )

                    total_unit = match.group(2)


                    used_value = float(
                        match.group(3)
                    )

                    used_unit = match.group(4)


                    total_bytes = (
                        self.memory_to_bytes(
                            total_value,
                            total_unit
                        )
                    )


                    used_bytes = (
                        self.memory_to_bytes(
                            used_value,
                            used_unit
                        )
                    )


                    if total_bytes > 0:

                        usage = (
                            used_bytes
                            / total_bytes
                        ) * 100


                        # Keep value between 0 and 100

                        usage = max(
                            0,
                            min(
                                100,
                                usage
                            )
                        )


                        ram_data.append(
                            usage
                        )


        return ram_data


    # ========================================================
    # RAM CHART
    # ========================================================

    def show_ram_chart(self):

        ram_data = (
            self.extract_ram_data()
        )


        self.figure.clear()


        ax = self.figure.add_subplot(
            111
        )


        if not ram_data:

            ax.text(
                0.5,
                0.5,
                "RAM Usage data not available",
                ha="center",
                va="center",
                fontsize=16
            )

            ax.set_axis_off()


        else:

            ax.plot(
                range(
                    1,
                    len(ram_data) + 1
                ),
                ram_data,
                marker="o"
            )


            ax.set_title(
                "RAM Usage (%)"
            )

            ax.set_xlabel(
                "Monitoring Record"
            )

            ax.set_ylabel(
                "RAM Usage (%)"
            )

            ax.set_ylim(
                0,
                100
            )


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # EXTRACT DISK DATA
    # ========================================================

    def extract_disk_data(self):

        disk_data = []


        for _, row in self.visualization_filtered_df.iterrows():

            command = str(
                row["Command"]
            )

            output = str(
                row["Output"]
            )


            if "df" in command.lower():

                matches = re.findall(
                    r"(\d+)%",
                    output
                )


                for value in matches:

                    disk_data.append(
                        float(value)
                    )


        return disk_data


    # ========================================================
    # DISK CHART
    # ========================================================

    def show_disk_chart(self):

        disk_data = (
            self.extract_disk_data()
        )


        self.figure.clear()


        ax = self.figure.add_subplot(
            111
        )


        if not disk_data:

            ax.text(
                0.5,
                0.5,
                "Disk Usage data not available",
                ha="center",
                va="center",
                fontsize=16
            )

            ax.set_axis_off()


        else:

            ax.bar(
                range(
                    1,
                    len(disk_data) + 1
                ),
                disk_data
            )


            ax.set_title(
                "Disk Usage (%)"
            )

            ax.set_xlabel(
                "Disk Record"
            )

            ax.set_ylabel(
                "Disk Usage (%)"
            )

            ax.set_ylim(
                0,
                100
            )


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # ALL SYSTEM CHARTS
    # ========================================================

    def show_all_system_charts(self):

        self.figure.clear()


        cpu_data = (
            self.extract_cpu_data()
        )

        ram_data = (
            self.extract_ram_data()
        )

        disk_data = (
            self.extract_disk_data()
        )


        # ====================================================
        # CPU
        # ====================================================

        ax1 = self.figure.add_subplot(
            311
        )


        if cpu_data:

            ax1.plot(
                range(
                    1,
                    len(cpu_data) + 1
                ),
                cpu_data,
                marker="o"
            )

            ax1.set_title(
                "CPU Usage (%)"
            )

            ax1.set_ylabel(
                "Usage (%)"
            )

            ax1.set_ylim(
                0,
                100
            )

        else:

            ax1.text(
                0.5,
                0.5,
                "CPU Data Not Available",
                ha="center",
                va="center"
            )

            ax1.set_axis_off()


        # ====================================================
        # RAM
        # ====================================================

        ax2 = self.figure.add_subplot(
            312
        )


        if ram_data:

            ax2.plot(
                range(
                    1,
                    len(ram_data) + 1
                ),
                ram_data,
                marker="o"
            )

            ax2.set_title(
                "RAM Usage (%)"
            )

            ax2.set_ylabel(
                "Usage (%)"
            )

            ax2.set_ylim(
                0,
                100
            )

        else:

            ax2.text(
                0.5,
                0.5,
                "RAM Data Not Available",
                ha="center",
                va="center"
            )

            ax2.set_axis_off()


        # ====================================================
        # DISK
        # ====================================================

        ax3 = self.figure.add_subplot(
            313
        )


        if disk_data:

            ax3.bar(
                range(
                    1,
                    len(disk_data) + 1
                ),
                disk_data
            )

            ax3.set_title(
                "Disk Usage (%)"
            )

            ax3.set_xlabel(
                "Disk Record"
            )

            ax3.set_ylabel(
                "Usage (%)"
            )

            ax3.set_ylim(
                0,
                100
            )

        else:

            ax3.text(
                0.5,
                0.5,
                "Disk Data Not Available",
                ha="center",
                va="center"
            )

            ax3.set_axis_off()


        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # NO DATA MESSAGE
    # ========================================================

    def no_data_message(self):

        QMessageBox.warning(
            self,
            "No Data",
            "No data available for visualization."
        )


    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        if self.ssh is not None:

            try:

                self.ssh.close()

            except Exception:

                pass


        event.accept()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = LinuxDashboard()

    window.showMaximized()

    sys.exit(
        app.exec_()
    )