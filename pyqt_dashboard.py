import sys
import os
import re
import csv
from datetime import datetime

import paramiko
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QMessageBox,
    QSizePolicy,
    QHeaderView
)

from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ============================================================
# CONFIGURATION
# ============================================================

REPORT_FOLDER = "reports"
CSV_FILE = os.path.join(REPORT_FOLDER, "system_report.csv")

COMMANDS = [
    "hostname",
    "hostname -I",
    "uptime",
    "free -h",
    "df -h",
    "vmstat",
    "top -bn1 | head -20"
]


# ============================================================
# MATPLOTLIB CANVAS
# ============================================================

class ChartCanvas(FigureCanvas):

    def __init__(self, parent=None):

        self.figure = Figure(figsize=(8, 5))
        self.ax = self.figure.add_subplot(111)

        super().__init__(self.figure)

        self.setParent(parent)


# ============================================================
# MAIN DASHBOARD
# ============================================================

class LinuxDashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        self.ssh = None
        self.current_records = []

        os.makedirs(
            REPORT_FOLDER,
            exist_ok=True
        )

        self.setWindowTitle(
            "Linux System Monitoring Dashboard"
        )

        self.setMinimumSize(
            1000,
            700
        )

        self.resize(
            1200,
            850
        )

        self.setup_ui()

        self.load_dates()

        self.load_all_records()

        self.load_visualization_dates()


    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            20,
            15,
            20,
            20
        )

        main_layout.setSpacing(
            12
        )


        # ====================================================
        # TITLE
        # ====================================================

        title = QLabel(
            "Linux System Monitoring Dashboard"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                padding: 8px;
            }
        """)

        main_layout.addWidget(
            title
        )


        # ====================================================
        # SSH CONNECTION
        # ====================================================

        connection_group = QGroupBox(
            "SSH Connection"
        )

        connection_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
                padding-top: 25px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }

            QLabel {
                font-size: 14px;
            }

            QLineEdit {
                font-size: 14px;
                padding: 7px;
            }

            QPushButton {
                font-size: 14px;
                padding: 8px 25px;
            }
        """)


        connection_layout = QGridLayout()

        connection_layout.setContentsMargins(
            20,
            15,
            20,
            15
        )

        connection_layout.setVerticalSpacing(
            8
        )


        ip_label = QLabel(
            "IP Address:"
        )

        username_label = QLabel(
            "Username:"
        )

        password_label = QLabel(
            "Password:"
        )


        self.ip_input = QLineEdit()

        self.username_input = QLineEdit()

        self.password_input = QLineEdit()


        self.ip_input.setPlaceholderText(
            "Enter Linux IP Address"
        )

        self.username_input.setPlaceholderText(
            "Enter Username"
        )

        self.password_input.setPlaceholderText(
            "Enter Password"
        )


        self.password_input.setEchoMode(
            QLineEdit.Password
        )


        connection_layout.addWidget(
            ip_label,
            0,
            0
        )

        connection_layout.addWidget(
            self.ip_input,
            0,
            1
        )


        connection_layout.addWidget(
            username_label,
            1,
            0
        )

        connection_layout.addWidget(
            self.username_input,
            1,
            1
        )


        connection_layout.addWidget(
            password_label,
            2,
            0
        )

        connection_layout.addWidget(
            self.password_input,
            2,
            1
        )


        self.connect_button = QPushButton(
            "Submit"
        )

        self.connect_button.clicked.connect(
            self.connect_ssh
        )


        button_layout = QHBoxLayout()

        button_layout.addStretch()

        button_layout.addWidget(
            self.connect_button
        )

        button_layout.addStretch()


        connection_layout.addLayout(
            button_layout,
            3,
            0,
            1,
            2
        )


        connection_group.setLayout(
            connection_layout
        )


        main_layout.addWidget(
            connection_group
        )


        # ====================================================
        # STATUS
        # ====================================================

        self.status_label = QLabel(
            "Status: Not Connected"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                padding: 5px;
            }
        """)


        main_layout.addWidget(
            self.status_label
        )


        # ====================================================
        # LINUX COMMANDS
        # ====================================================

        command_group = QGroupBox(
            "Linux Commands"
        )

        command_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
                padding-top: 25px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }

            QLabel {
                font-size: 14px;
            }

            QComboBox {
                font-size: 14px;
                padding: 7px;
                min-height: 28px;
            }

            QPushButton {
                font-size: 14px;
                padding: 8px 22px;
            }
        """)


        command_layout = QGridLayout()

        command_layout.setContentsMargins(
            20,
            15,
            20,
            15
        )

        command_layout.setHorizontalSpacing(
            12
        )


        command_label = QLabel(
            "Commands:"
        )


        self.command_combo = QComboBox()

        self.command_combo.addItem(
            "All Commands"
        )


        for command in COMMANDS:

            self.command_combo.addItem(
                command
            )


        self.command_combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )


        self.execute_button = QPushButton(
            "Execute"
        )

        self.execute_button.clicked.connect(
            self.execute_selected_command
        )


        command_layout.addWidget(
            command_label,
            0,
            0
        )

        command_layout.addWidget(
            self.command_combo,
            0,
            1
        )

        command_layout.addWidget(
            self.execute_button,
            0,
            2
        )


        command_layout.setColumnStretch(
            1,
            1
        )


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

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 14px;
                padding: 10px 18px;
            }
        """)


        self.live_tab = self.create_live_tab()

        self.records_tab = self.create_records_tab()

        self.monitoring_tab = self.create_monitoring_tab()

        self.visualization_tab = self.create_visualization_tab()


        self.tabs.addTab(
            self.live_tab,
            "Live Output"
        )

        self.tabs.addTab(
            self.records_tab,
            "Previous Records"
        )

        self.tabs.addTab(
            self.monitoring_tab,
            "Monitoring Data"
        )

        self.tabs.addTab(
            self.visualization_tab,
            "Data Visualization"
        )


        main_layout.addWidget(
            self.tabs,
            1
        )


    # ========================================================
    # LIVE OUTPUT TAB
    # ========================================================

    def create_live_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        self.output_text = QTextEdit()

        self.output_text.setReadOnly(
            True
        )


        self.output_text.setStyleSheet("""
            QTextEdit {
                font-family: Consolas;
                font-size: 13px;
            }
        """)


        layout.addWidget(
            self.output_text
        )


        return widget


    # ========================================================
    # PREVIOUS RECORDS TAB
    # ========================================================

    def create_records_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        filter_layout = QHBoxLayout()


        date_label = QLabel(
            "Select Date:"
        )


        self.date_combo = QComboBox()

        self.date_combo.setMinimumWidth(
            200
        )


        self.refresh_button = QPushButton(
            "Refresh Records"
        )


        self.refresh_button.clicked.connect(
            self.refresh_records
        )


        self.date_combo.currentIndexChanged.connect(
            self.filter_records_by_date
        )


        filter_layout.addWidget(
            date_label
        )

        filter_layout.addWidget(
            self.date_combo
        )

        filter_layout.addWidget(
            self.refresh_button
        )

        filter_layout.addStretch()


        layout.addLayout(
            filter_layout
        )


        self.records_table = QTableWidget()

        self.records_table.setColumnCount(
            4
        )


        self.records_table.setHorizontalHeaderLabels([
            "Date",
            "Time",
            "Command",
            "Output"
        ])


        self.records_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch
        )


        self.records_table.setAlternatingRowColors(
            True
        )


        layout.addWidget(
            self.records_table
        )


        return widget


    # ========================================================
    # MONITORING DATA TAB
    # ========================================================

    def create_monitoring_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        self.monitoring_table = QTableWidget()

        self.monitoring_table.setColumnCount(
            4
        )


        self.monitoring_table.setHorizontalHeaderLabels([
            "Date",
            "Time",
            "Command",
            "Output"
        ])


        self.monitoring_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch
        )


        self.monitoring_table.setAlternatingRowColors(
            True
        )


        layout.addWidget(
            self.monitoring_table
        )


        return widget


    # ========================================================
    # DATA VISUALIZATION TAB
    # ========================================================

    def create_visualization_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )


        # ----------------------------------------------------
        # DATE FILTER
        # ----------------------------------------------------

        filter_layout = QHBoxLayout()


        date_label = QLabel(
            "Select Date:"
        )


        self.visualization_date_combo = QComboBox()

        self.visualization_date_combo.setMinimumWidth(
            220
        )


        self.visualization_date_combo.currentIndexChanged.connect(
            self.visualization_date_changed
        )


        self.visualization_refresh_button = QPushButton(
            "Refresh Dates"
        )


        self.visualization_refresh_button.clicked.connect(
            self.refresh_visualization_dates
        )


        filter_layout.addWidget(
            date_label
        )

        filter_layout.addWidget(
            self.visualization_date_combo
        )

        filter_layout.addWidget(
            self.visualization_refresh_button
        )

        filter_layout.addStretch()


        layout.addLayout(
            filter_layout
        )


        # ----------------------------------------------------
        # CHART BUTTONS
        # ----------------------------------------------------

        button_layout = QHBoxLayout()


        self.command_chart_button = QPushButton(
            "Command Records"
        )

        self.timeline_chart_button = QPushButton(
            "Timeline"
        )

        self.cpu_chart_button = QPushButton(
            "CPU Usage"
        )

        self.ram_chart_button = QPushButton(
            "RAM Usage"
        )

        self.disk_chart_button = QPushButton(
            "Disk Usage"
        )

        self.all_chart_button = QPushButton(
            "All System Charts"
        )


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
            self.show_all_charts
        )


        buttons = [
            self.command_chart_button,
            self.timeline_chart_button,
            self.cpu_chart_button,
            self.ram_chart_button,
            self.disk_chart_button,
            self.all_chart_button
        ]


        for button in buttons:

            button_layout.addWidget(
                button
            )


        layout.addLayout(
            button_layout
        )


        # ----------------------------------------------------
        # CHART AREA
        # ----------------------------------------------------

        self.chart = ChartCanvas(
            self
        )


        layout.addWidget(
            self.chart
        )


        return widget


    # ========================================================
    # SSH CONNECTION
    # ========================================================

    def connect_ssh(self):

        ip = self.ip_input.text().strip()

        username = self.username_input.text().strip()

        password = self.password_input.text()


        if not ip or not username or not password:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter IP Address, Username and Password."
            )

            return


        self.output_text.clear()


        try:

            self.output_text.append(
                "Connecting to Linux system..."
            )


            self.ssh = paramiko.SSHClient()


            self.ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )


            self.ssh.connect(
                hostname=ip,
                username=username,
                password=password,
                timeout=10
            )


            self.status_label.setText(
                "Status: Connected"
            )


            self.connect_button.setText(
                "Connected"
            )


            self.connect_button.setEnabled(
                False
            )


            self.output_text.append(
                "\nSSH connection successful."
            )


            QMessageBox.information(
                self,
                "Connection Successful",
                "Connected to Linux system successfully."
            )


        except paramiko.AuthenticationException:

            self.status_label.setText(
                "Status: Authentication Failed"
            )


            QMessageBox.critical(
                self,
                "Authentication Error",
                "Username or password is incorrect."
            )


        except Exception as e:

            self.status_label.setText(
                "Status: Connection Failed"
            )


            QMessageBox.critical(
                self,
                "Connection Error",
                str(e)
            )


    # ========================================================
    # EXECUTE COMMAND
    # ========================================================

    def execute_selected_command(self):

        if self.ssh is None:

            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to Linux first."
            )

            return


        selected = self.command_combo.currentText()


        self.output_text.clear()


        if selected == "All Commands":

            for command in COMMANDS:

                self.run_single_command(
                    command
                )

        else:

            self.run_single_command(
                selected
            )


        # Refresh all data after execution

        self.load_all_records()

        self.load_dates()

        self.load_visualization_dates()


    # ========================================================
    # RUN SINGLE COMMAND
    # ========================================================

    def run_single_command(self, command):

        try:

            self.output_text.append(
                "\n" + "=" * 70
            )


            self.output_text.append(
                f"Running: {command}"
            )


            stdin, stdout, stderr = self.ssh.exec_command(
                command
            )


            output = stdout.read().decode(
                "utf-8",
                errors="replace"
            )


            error = stderr.read().decode(
                "utf-8",
                errors="replace"
            )


            if error.strip():

                output = (
                    output
                    + "\nERROR:\n"
                    + error
                )


            self.output_text.append(
                output
            )


            self.save_record(
                command,
                output
            )


        except Exception as e:

            self.output_text.append(
                f"\nError executing command:\n{e}"
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


        output_clean = (
            output
            .replace("\r", "")
            .replace("\n", " | ")
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

                writer.writerow([
                    "Date",
                    "Time",
                    "Command",
                    "Output"
                ])


            writer.writerow([
                date_value,
                time_value,
                command,
                output_clean
            ])


    # ========================================================
    # LOAD PREVIOUS RECORD DATES
    # ========================================================

    def load_dates(self):

        self.date_combo.blockSignals(
            True
        )


        current_date = (
            self.date_combo.currentText()
        )


        self.date_combo.clear()


        if not os.path.exists(
            CSV_FILE
        ):

            self.date_combo.blockSignals(
                False
            )

            return


        try:

            df = pd.read_csv(
                CSV_FILE
            )


            if df.empty:

                self.date_combo.blockSignals(
                    False
                )

                return


            dates = (
                df["Date"]
                .dropna()
                .astype(str)
                .unique()
            )


            def date_sort_key(value):

                try:

                    return datetime.strptime(
                        value,
                        "%d-%m-%Y"
                    )

                except:

                    return datetime.min


            dates = sorted(
                dates,
                key=date_sort_key,
                reverse=True
            )


            self.date_combo.addItems(
                dates
            )


            if current_date in dates:

                self.date_combo.setCurrentText(
                    current_date
                )


        except Exception as e:

            print(
                "Date loading error:",
                e
            )


        self.date_combo.blockSignals(
            False
        )


        self.filter_records_by_date()


    # ========================================================
    # LOAD VISUALIZATION DATES
    # ========================================================

    def load_visualization_dates(self):

        if not hasattr(
            self,
            "visualization_date_combo"
        ):

            return


        self.visualization_date_combo.blockSignals(
            True
        )


        current_date = (
            self.visualization_date_combo.currentText()
        )


        self.visualization_date_combo.clear()


        if not os.path.exists(
            CSV_FILE
        ):

            self.visualization_date_combo.blockSignals(
                False
            )

            return


        try:

            df = pd.read_csv(
                CSV_FILE
            )


            if df.empty:

                self.visualization_date_combo.blockSignals(
                    False
                )

                return


            dates = (
                df["Date"]
                .dropna()
                .astype(str)
                .unique()
            )


            def date_sort_key(value):

                try:

                    return datetime.strptime(
                        value,
                        "%d-%m-%Y"
                    )

                except:

                    return datetime.min


            dates = sorted(
                dates,
                key=date_sort_key,
                reverse=True
            )


            self.visualization_date_combo.addItems(
                dates
            )


            if current_date in dates:

                self.visualization_date_combo.setCurrentText(
                    current_date
                )


        except Exception as e:

            print(
                "Visualization date loading error:",
                e
            )


        self.visualization_date_combo.blockSignals(
            False
        )


        # Show latest date automatically

        if self.visualization_date_combo.count() > 0:

            self.visualization_date_combo.setCurrentIndex(
                0
            )


            self.show_all_charts()


    # ========================================================
    # REFRESH VISUALIZATION DATES
    # ========================================================

    def refresh_visualization_dates(self):

        self.load_visualization_dates()


    # ========================================================
    # VISUALIZATION DATE CHANGED
    # ========================================================

    def visualization_date_changed(self):

        selected_date = (
            self.visualization_date_combo.currentText()
        )


        if selected_date:

            self.show_all_charts()


    # ========================================================
    # LOAD ALL RECORDS
    # ========================================================

    def load_all_records(self):

        if not os.path.exists(
            CSV_FILE
        ):

            self.current_records = []

            self.records_table.setRowCount(
                0
            )

            self.monitoring_table.setRowCount(
                0
            )

            return


        try:

            df = pd.read_csv(
                CSV_FILE
            )


            df = df.fillna("")


            self.current_records = (
                df.to_dict("records")
            )


            self.fill_table(
                self.monitoring_table,
                self.current_records
            )


        except Exception as e:

            print(
                "Record loading error:",
                e
            )


    # ========================================================
    # FILTER PREVIOUS RECORDS BY DATE
    # ========================================================

    def filter_records_by_date(self):

        selected_date = (
            self.date_combo.currentText()
        )


        if not selected_date:

            self.records_table.setRowCount(
                0
            )

            return


        if not os.path.exists(
            CSV_FILE
        ):

            self.records_table.setRowCount(
                0
            )

            return


        try:

            df = pd.read_csv(
                CSV_FILE
            )


            df = df.fillna("")


            filtered = df[
                df["Date"].astype(str)
                == selected_date
            ]


            records = filtered.to_dict(
                "records"
            )


            self.fill_table(
                self.records_table,
                records
            )


        except Exception as e:

            print(
                "Filtering error:",
                e
            )


    # ========================================================
    # REFRESH RECORDS
    # ========================================================

    def refresh_records(self):

        self.load_dates()

        self.load_all_records()

        self.load_visualization_dates()


    # ========================================================
    # FILL TABLE
    # ========================================================

    def fill_table(
        self,
        table,
        records
    ):

        table.setRowCount(
            0
        )


        for row_data in records:

            row = table.rowCount()


            table.insertRow(
                row
            )


            table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(
                        row_data.get(
                            "Date",
                            ""
                        )
                    )
                )
            )


            table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(
                        row_data.get(
                            "Time",
                            ""
                        )
                    )
                )
            )


            table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(
                        row_data.get(
                            "Command",
                            ""
                        )
                    )
                )
            )


            table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(
                        row_data.get(
                            "Output",
                            ""
                        )
                    )
                )
            )


    # ========================================================
    # GET FILTERED DATAFRAME
    # ========================================================

    def get_dataframe(self):

        if not os.path.exists(
            CSV_FILE
        ):

            return pd.DataFrame()


        try:

            df = pd.read_csv(
                CSV_FILE
            )


            df = df.fillna("")


            # -----------------------------------------------
            # DATE-WISE VISUALIZATION FILTER
            # -----------------------------------------------

            selected_date = ""


            if hasattr(
                self,
                "visualization_date_combo"
            ):

                selected_date = (
                    self.visualization_date_combo.currentText()
                )


            if selected_date:

                df = df[
                    df["Date"].astype(str)
                    == selected_date
                ]


            # -----------------------------------------------
            # DATETIME
            # -----------------------------------------------

            df["DateTime"] = pd.to_datetime(
                df["Date"].astype(str)
                + " "
                + df["Time"].astype(str),
                format="%d-%m-%Y %H:%M:%S",
                errors="coerce"
            )


            return df


        except Exception as e:

            print(
                "DataFrame error:",
                e
            )


            return pd.DataFrame()


    # ========================================================
    # COMMAND RECORD CHART
    # ========================================================

    def show_command_chart(self):

        df = self.get_dataframe()


        if df.empty:

            self.show_no_data()

            return


        counts = (
            df["Command"]
            .value_counts()
        )


        self.chart.ax.clear()


        self.chart.ax.bar(
            counts.index,
            counts.values
        )


        self.chart.ax.set_title(
            "Command Execution Records"
        )


        self.chart.ax.set_xlabel(
            "Command"
        )


        self.chart.ax.set_ylabel(
            "Number of Records"
        )


        self.chart.ax.tick_params(
            axis="x",
            rotation=45
        )


        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # TIMELINE CHART
    # ========================================================

    def show_timeline_chart(self):

        df = self.get_dataframe()


        if df.empty:

            self.show_no_data()

            return


        timeline = (
            df.groupby("DateTime")
            .size()
            .sort_index()
        )


        self.chart.ax.clear()


        self.chart.ax.plot(
            timeline.index,
            timeline.values,
            marker="o"
        )


        self.chart.ax.set_title(
            "System Monitoring Timeline"
        )


        self.chart.ax.set_xlabel(
            "Time"
        )


        self.chart.ax.set_ylabel(
            "Records"
        )


        self.chart.figure.autofmt_xdate()

        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # CPU DATA EXTRACTION
    # ========================================================

    def extract_cpu_values(self, df):

        values = []


        for _, row in df.iterrows():

            if row["Command"] != "top -bn1 | head -20":

                continue


            output = str(
                row["Output"]
            )


            # top output:
            # %Cpu(s): ... 92.3 id

            match = re.search(
                r"(\d+(?:\.\d+)?)\s*id\b",
                output,
                re.IGNORECASE
            )


            if match:

                idle = float(
                    match.group(1)
                )


                cpu_usage = (
                    100 - idle
                )


                values.append({
                    "time": row["DateTime"],
                    "value": cpu_usage
                })


        return values


    # ========================================================
    # CPU CHART
    # ========================================================

    def show_cpu_chart(self):

        df = self.get_dataframe()


        values = self.extract_cpu_values(
            df
        )


        if not values:

            self.show_message(
                "CPU data not found.\n\n"
                "Run the top command first."
            )

            return


        times = [
            item["time"]
            for item in values
        ]


        usage = [
            item["value"]
            for item in values
        ]


        self.chart.ax.clear()


        self.chart.ax.plot(
            times,
            usage,
            marker="o"
        )


        self.chart.ax.set_title(
            "CPU Usage"
        )


        self.chart.ax.set_xlabel(
            "Time"
        )


        self.chart.ax.set_ylabel(
            "CPU Usage (%)"
        )


        self.chart.ax.set_ylim(
            0,
            100
        )


        self.chart.figure.autofmt_xdate()

        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # CONVERT MEMORY TO MB
    # ========================================================

    def convert_to_mb(
        self,
        value,
        unit
    ):

        try:

            number = float(
                value
            )


            unit = unit.lower()


            if unit == "kib":
                return number / 1024


            if unit == "mib":
                return number


            if unit == "gib":
                return number * 1024


            if unit == "tib":
                return number * 1024 * 1024


            if unit == "kb":
                return number / 1024


            if unit == "mb":
                return number


            if unit == "gb":
                return number * 1024


            if unit == "tb":
                return number * 1024 * 1024


            return number


        except:

            return None


    # ========================================================
    # RAM DATA EXTRACTION
    # ========================================================

    def extract_ram_values(self, df):

        values = []


        for _, row in df.iterrows():

            if row["Command"] != "free -h":

                continue


            output = str(
                row["Output"]
            )


            # Example:
            # Mem: 3.6Gi 472Mi 3.1Gi

            match = re.search(
                r"Mem:\s+"
                r"([\d.]+)\s*([KMGT]i?B)"
                r"\s+"
                r"([\d.]+)\s*([KMGT]i?B)",
                output,
                re.IGNORECASE
            )


            if match:

                total = self.convert_to_mb(
                    match.group(1),
                    match.group(2)
                )


                used = self.convert_to_mb(
                    match.group(3),
                    match.group(4)
                )


                if (
                    total is not None
                    and used is not None
                    and total > 0
                ):

                    percentage = (
                        used / total
                    ) * 100


                    values.append({
                        "time": row["DateTime"],
                        "value": percentage
                    })


        return values


    # ========================================================
    # RAM CHART
    # ========================================================

    def show_ram_chart(self):

        df = self.get_dataframe()


        values = self.extract_ram_values(
            df
        )


        if not values:

            self.show_message(
                "RAM data not found.\n\n"
                "Run the free -h command first."
            )

            return


        times = [
            item["time"]
            for item in values
        ]


        usage = [
            item["value"]
            for item in values
        ]


        self.chart.ax.clear()


        self.chart.ax.plot(
            times,
            usage,
            marker="o"
        )


        self.chart.ax.set_title(
            "RAM Usage"
        )


        self.chart.ax.set_xlabel(
            "Time"
        )


        self.chart.ax.set_ylabel(
            "RAM Usage (%)"
        )


        self.chart.ax.set_ylim(
            0,
            100
        )


        self.chart.figure.autofmt_xdate()

        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # DISK DATA EXTRACTION
    # ========================================================

    def extract_disk_values(self, df):

        values = []


        for _, row in df.iterrows():

            if row["Command"] != "df -h":

                continue


            output = str(
                row["Output"]
            )


            matches = re.findall(
                r"(\d+)%",
                output
            )


            for value in matches:

                try:

                    values.append({
                        "time": row["DateTime"],
                        "value": float(value)
                    })


                except:

                    pass


        return values


    # ========================================================
    # DISK CHART
    # ========================================================

    def show_disk_chart(self):

        df = self.get_dataframe()


        values = self.extract_disk_values(
            df
        )


        if not values:

            self.show_message(
                "Disk data not found.\n\n"
                "Run the df -h command first."
            )

            return


        times = [
            item["time"]
            for item in values
        ]


        usage = [
            item["value"]
            for item in values
        ]


        self.chart.ax.clear()


        self.chart.ax.plot(
            times,
            usage,
            marker="o"
        )


        self.chart.ax.set_title(
            "Disk Usage"
        )


        self.chart.ax.set_xlabel(
            "Time"
        )


        self.chart.ax.set_ylabel(
            "Disk Usage (%)"
        )


        self.chart.ax.set_ylim(
            0,
            100
        )


        self.chart.figure.autofmt_xdate()

        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # ALL SYSTEM CHARTS
    # ========================================================

    def show_all_charts(self):

        df = self.get_dataframe()


        if df.empty:

            self.show_no_data()

            return


        cpu_values = (
            self.extract_cpu_values(df)
        )


        ram_values = (
            self.extract_ram_values(df)
        )


        disk_values = (
            self.extract_disk_values(df)
        )


        self.chart.ax.clear()


        plotted = False


        # ----------------------------------------------------
        # CPU
        # ----------------------------------------------------

        if cpu_values:

            self.chart.ax.plot(
                [
                    x["time"]
                    for x in cpu_values
                ],
                [
                    x["value"]
                    for x in cpu_values
                ],
                marker="o",
                label="CPU Usage"
            )


            plotted = True


        # ----------------------------------------------------
        # RAM
        # ----------------------------------------------------

        if ram_values:

            self.chart.ax.plot(
                [
                    x["time"]
                    for x in ram_values
                ],
                [
                    x["value"]
                    for x in ram_values
                ],
                marker="o",
                label="RAM Usage"
            )


            plotted = True


        # ----------------------------------------------------
        # DISK
        # ----------------------------------------------------

        if disk_values:

            self.chart.ax.plot(
                [
                    x["time"]
                    for x in disk_values
                ],
                [
                    x["value"]
                    for x in disk_values
                ],
                marker="o",
                label="Disk Usage"
            )


            plotted = True


        if not plotted:

            self.show_message(
                "CPU, RAM किंवा Disk monitoring data सापडला नाही."
            )

            return


        selected_date = (
            self.visualization_date_combo.currentText()
        )


        self.chart.ax.set_title(
            f"System Usage - {selected_date}"
        )


        self.chart.ax.set_xlabel(
            "Time"
        )


        self.chart.ax.set_ylabel(
            "Usage (%)"
        )


        self.chart.ax.set_ylim(
            0,
            100
        )


        self.chart.ax.legend()


        self.chart.figure.autofmt_xdate()

        self.chart.figure.tight_layout()

        self.chart.draw()


    # ========================================================
    # MESSAGE BOXES
    # ========================================================

    def show_no_data(self):

        QMessageBox.information(
            self,
            "No Data",
            "No monitoring records are available yet."
        )


    def show_message(self, message):

        QMessageBox.information(
            self,
            "Monitoring Data",
            message
        )


    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(self, event):

        try:

            if self.ssh:

                self.ssh.close()

        except:

            pass


        event.accept()


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )


    window = LinuxDashboard()

    window.show()


    sys.exit(
        app.exec_()
    )