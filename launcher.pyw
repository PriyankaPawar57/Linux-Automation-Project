import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import webbrowser
import os
import sys
import time


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)

DASHBOARD_FILE = os.path.join(
    PROJECT_FOLDER,
    "dashboard.py"
)


# ============================================================
# START DASHBOARD
# ============================================================

def start_dashboard():

    if not os.path.exists(DASHBOARD_FILE):

        messagebox.showerror(
            "File Not Found",
            "dashboard.py file project folder मध्ये सापडली नाही."
        )

        return

    start_button.config(
        state="disabled"
    )

    status_label.config(
        text="⏳ Starting Dashboard..."
    )

    progress_label.config(
        text="Please wait..."
    )

    thread = threading.Thread(
        target=run_dashboard,
        daemon=True
    )

    thread.start()


# ============================================================
# RUN STREAMLIT
# ============================================================

def run_dashboard():

    try:

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                DASHBOARD_FILE,
                "--server.headless=true"
            ],
            cwd=PROJECT_FOLDER,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(4)

        webbrowser.open(
            "http://localhost:8501"
        )

        root.after(
            0,
            dashboard_started
        )

    except Exception as e:

        root.after(
            0,
            lambda: show_error(str(e))
        )


# ============================================================
# DASHBOARD STARTED
# ============================================================

def dashboard_started():

    status_label.config(
        text="✅ Dashboard Running"
    )

    progress_label.config(
        text="Dashboard opened in browser."
    )

    start_button.config(
        state="normal"
    )


# ============================================================
# ERROR
# ============================================================

def show_error(error):

    status_label.config(
        text="❌ Dashboard could not start"
    )

    progress_label.config(
        text=""
    )

    start_button.config(
        state="normal"
    )

    messagebox.showerror(
        "Dashboard Error",
        error
    )


# ============================================================
# EXIT
# ============================================================

def exit_application():

    root.destroy()


# ============================================================
# GUI WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Linux System Monitoring"
)

root.geometry(
    "550x350"
)

root.resizable(
    False,
    False
)


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,
    text="💻 Linux System Monitoring",
    font=("Arial", 22, "bold")
)

title_label.pack(
    pady=30
)


# ============================================================
# SUBTITLE
# ============================================================

subtitle_label = tk.Label(
    root,
    text="Interactive Monitoring Dashboard",
    font=("Arial", 12)
)

subtitle_label.pack(
    pady=5
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,
    text="Dashboard Ready",
    font=("Arial", 14)
)

status_label.pack(
    pady=25
)


# ============================================================
# START BUTTON
# ============================================================

start_button = tk.Button(
    root,
    text="🚀 Start Dashboard",
    font=("Arial", 14, "bold"),
    width=22,
    height=2,
    command=start_dashboard
)

start_button.pack(
    pady=10
)


# ============================================================
# PROGRESS
# ============================================================

progress_label = tk.Label(
    root,
    text="Click the button to open the dashboard.",
    font=("Arial", 10)
)

progress_label.pack(
    pady=10
)


# ============================================================
# EXIT BUTTON
# ============================================================

exit_button = tk.Button(
    root,
    text="Exit",
    font=("Arial", 11),
    width=12,
    command=exit_application
)

exit_button.pack(
    pady=15
)


# ============================================================
# RUN GUI
# ============================================================

root.mainloop()