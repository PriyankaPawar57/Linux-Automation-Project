import paramiko
import pandas as pd
import os
from datetime import datetime
import sqlite3

# ==========================================================
# PDF LIBRARIES
# ==========================================================

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# ==========================================================
# PARSE MEMORY DATA
# ==========================================================

def parse_free_memory(output):

    lines = output.splitlines()

    for line in lines:

        if line.startswith("Mem:"):

            parts = line.split()

            return {
                "Total": parts[1],
                "Used": parts[2],
                "Free": parts[3],
                "Shared": parts[4],
                "Buff/Cache": parts[5],
                "Available": parts[6]
            }

    return {}


# ==========================================================
# USER INPUT
# ==========================================================

host = input("Enter Linux IP Address: ")
username = input("Enter Username: ")
password = input("Enter Password: ")


# ==========================================================
# CREATE SSH CLIENT
# ==========================================================

ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy()
)


# ==========================================================
# MAIN PROGRAM
# ==========================================================

try:

    # ======================================================
    # CONNECT TO LINUX
    # ======================================================

    ssh.connect(
        hostname=host,
        username=username,
        password=password
    )

    print("\n✅ Connected Successfully!")


    # ======================================================
    # CURRENT DATE AND TIME
    # ======================================================

    current_date = datetime.now().strftime(
        "%d-%m-%Y"
    )

    current_time = datetime.now().strftime(
        "%H:%M:%S"
    )

    # Timestamp for unique PDF
    report_timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )


    # ======================================================
    # CREATE REPORTS FOLDER
    # ======================================================

    os.makedirs(
        "reports",
        exist_ok=True
    )


    # ======================================================
    # SQLITE DATABASE
    # ======================================================

    conn = sqlite3.connect(
        "reports/system_report.db"
    )

    cursor = conn.cursor()


    # ======================================================
    # CREATE SQLITE TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            command TEXT,
            output TEXT
        )
    """)

    conn.commit()


    # ======================================================
    # LINUX COMMANDS
    # ======================================================

    commands = [

        "hostname",

        "hostname -I",

        "uptime",

        "free -h",

        "df -h",

        "vmstat",

        "top -bn1 | head -5"

    ]


    # ======================================================
    # STORE RESULTS
    # ======================================================

    results = {}


    # ======================================================
    # EXECUTE LINUX COMMANDS
    # ======================================================

    for cmd in commands:

        print(
            "\n" + "=" * 60
        )

        print(
            "Running:",
            cmd
        )


        stdin, stdout, stderr = ssh.exec_command(
            cmd
        )


        # Read command output
        output = stdout.read().decode(
            errors="ignore"
        ).strip()


        # Read command error
        error = stderr.read().decode(
            errors="ignore"
        ).strip()


        # ==================================================
        # CHECK ERROR
        # ==================================================

        if error:

            results[cmd] = error

            print(
                error
            )

        else:

            results[cmd] = output

            print(
                output
            )


        # ==================================================
        # PARSE MEMORY DATA
        # ==================================================

        if cmd == "free -h":

            memory_data = parse_free_memory(
                output
            )


            print(
                "\n===== Parsed Memory Data ====="
            )


            for key, value in memory_data.items():

                print(
                    f"{key}: {value}"
                )


    # ======================================================
    # CLEAN OUTPUT
    # ======================================================

    clean_results = {}


    for cmd, output in results.items():


        # ==================================================
        # STORE DATA INTO SQLITE
        # ==================================================

        cursor.execute("""
            INSERT INTO system_report
            (date, time, command, output)
            VALUES (?, ?, ?, ?)
        """,
        (
            current_date,
            current_time,
            cmd,
            output
        ))


        # ==================================================
        # CLEAN OUTPUT
        # ==================================================

        clean_output = " ".join(
            output.split()
        )


        clean_results[cmd] = clean_output


    conn.commit()


    # ======================================================
    # CREATE DATAFRAME
    # ======================================================

    df = pd.DataFrame(
        list(clean_results.items()),
        columns=[
            "Command",
            "Output"
        ]
    )


    # ======================================================
    # ADD DATE
    # ======================================================

    df.insert(
        0,
        "Date",
        current_date
    )


    # ======================================================
    # ADD TIME
    # ======================================================

    df.insert(
        1,
        "Time",
        current_time
    )


    # ======================================================
    # EXCEL REPORT
    # ======================================================

    file_path = (
        "reports/system_report.xlsx"
    )


    if os.path.exists(file_path):

        old_excel = pd.read_excel(
            file_path
        )


        final_excel = pd.concat(
            [
                old_excel,
                df
            ],
            ignore_index=True
        )

    else:

        final_excel = df


    # ======================================================
    # SAVE EXCEL
    # ======================================================

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl"
    ) as writer:

        final_excel.to_excel(
            writer,
            sheet_name="System Report",
            index=False
        )


    print(
        "\n✅ Excel Report Updated Successfully!"
    )

    print(
        "Saved at:",
        file_path
    )


    # ======================================================
    # CSV REPORT
    # ======================================================

    csv_file_path = (
        "reports/system_report.csv"
    )


    if os.path.exists(csv_file_path):

        old_df = pd.read_csv(
            csv_file_path
        )


        final_df = pd.concat(
            [
                old_df,
                df
            ],
            ignore_index=True
        )

    else:

        final_df = df


    # ======================================================
    # SAVE CSV
    # ======================================================

    final_df.to_csv(
        csv_file_path,
        index=False
    )


    print(
        "\n✅ CSV Report Updated Successfully!"
    )

    print(
        "Saved at:",
        csv_file_path
    )


    # ======================================================
    # CSV TO PDF CONVERSION
    # ======================================================

    print(
        "\n===== Converting CSV to PDF ====="
    )


    # ======================================================
    # UNIQUE PDF FILE NAME
    # ======================================================

    pdf_file_path = (
        f"reports/system_report_"
        f"{report_timestamp}.pdf"
    )


    # ======================================================
    # CREATE PDF DOCUMENT
    # ======================================================

    pdf = SimpleDocTemplate(

        pdf_file_path,

        pagesize=landscape(A4),

        rightMargin=20,

        leftMargin=20,

        topMargin=20,

        bottomMargin=20

    )


    # ======================================================
    # PDF STYLES
    # ======================================================

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    normal_style = styles["Normal"]

    body_style = styles["BodyText"]


    # ======================================================
    # READ CSV
    # ======================================================

    pdf_df = pd.read_csv(
        csv_file_path
    )


    # Convert Date and Time to string
    pdf_df["Date"] = pdf_df["Date"].astype(str)

    pdf_df["Time"] = pdf_df["Time"].astype(str)


    # ======================================================
    # STORY
    # ======================================================

    story = []


    # ======================================================
    # GROUP DATA BY DATE
    # ======================================================

    grouped_data = pdf_df.groupby(
        "Date"
    )


    date_list = list(
        grouped_data
    )


    # ======================================================
    # CREATE ONE PAGE FOR EACH DATE
    # ======================================================

    for date_index, (
        report_date,
        date_data
    ) in enumerate(date_list):


        # ==================================================
        # TITLE
        # ==================================================

        title = Paragraph(

            "<b>Linux System Information Report</b>",

            title_style

        )


        story.append(
            title
        )


        story.append(
            Spacer(1, 10)
        )


        # ==================================================
        # REPORT DATE
        # ==================================================

        date_heading = Paragraph(

            f"<b>Report Date:</b> "
            f"{report_date}",

            normal_style

        )


        story.append(
            date_heading
        )


        story.append(
            Spacer(1, 5)
        )


        # ==================================================
        # EXECUTION TIME
        # ==================================================

        times = ", ".join(
            date_data["Time"]
            .astype(str)
            .unique()
        )


        time_heading = Paragraph(

            f"<b>Execution Time:</b> "
            f"{times}",

            normal_style

        )


        story.append(
            time_heading
        )


        story.append(
            Spacer(1, 5)
        )


        # ==================================================
        # REPORT GENERATED TIME
        # ==================================================

        generated_heading = Paragraph(

            f"<b>PDF Generated On:</b> "
            f"{current_date} {current_time}",

            normal_style

        )


        story.append(
            generated_heading
        )


        story.append(
            Spacer(1, 15)
        )


        # ==================================================
        # TABLE DATA
        # ==================================================

        table_data = []


        # ==================================================
        # TABLE HEADER
        # ==================================================

        header = [

            Paragraph(
                "<b>Date</b>",
                body_style
            ),

            Paragraph(
                "<b>Time</b>",
                body_style
            ),

            Paragraph(
                "<b>Command</b>",
                body_style
            ),

            Paragraph(
                "<b>Output</b>",
                body_style
            )

        ]


        table_data.append(
            header
        )


        # ==================================================
        # TABLE ROWS
        # ==================================================

        for _, row in date_data.iterrows():

            row_data = [

                Paragraph(
                    str(row["Date"]),
                    body_style
                ),

                Paragraph(
                    str(row["Time"]),
                    body_style
                ),

                Paragraph(
                    str(row["Command"]),
                    body_style
                ),

                Paragraph(
                    str(row["Output"]),
                    body_style
                )

            ]


            table_data.append(
                row_data
            )


        # ==================================================
        # CREATE TABLE
        # ==================================================

        table = Table(

            table_data,

            repeatRows=1,

            colWidths=[
                70,
                70,
                120,
                480
            ]

        )


        # ==================================================
        # TABLE STYLE
        # ==================================================

        table.setStyle(

            TableStyle([

                # Header background
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#2F5597")
                ),

                # Header text color
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                # Header font
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                # Font size
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                # Grid
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black
                ),

                # Vertical alignment
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                # Left padding
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                # Right padding
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                # Top padding
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                # Bottom padding
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )

            ])

        )


        # ==================================================
        # ADD TABLE
        # ==================================================

        story.append(
            table
        )


        # ==================================================
        # PAGE BREAK
        # ==================================================

        if date_index < len(date_list) - 1:

            story.append(
                PageBreak()
            )


    # ======================================================
    # BUILD PDF
    # ======================================================

    pdf.build(
        story
    )


    # ======================================================
    # PDF SUCCESS MESSAGE
    # ======================================================

    print(
        "\n✅ Date-wise PDF Report Generated Successfully!"
    )


    print(
        "Saved at:",
        pdf_file_path
    )


    # ======================================================
    # DISPLAY SQLITE RECORDS
    # ======================================================

    print(
        "\n===== SQLite Database Records ====="
    )


    cursor.execute(
        "SELECT * FROM system_report"
    )


    rows = cursor.fetchall()


    for row in rows:

        print(
            row
        )


# ==========================================================
# EXCEPTION HANDLING
# ==========================================================

except Exception as e:

    print(
        "\n❌ Error:",
        e
    )


# ==========================================================
# FINALLY
# ==========================================================

finally:

    try:

        conn.commit()

        conn.close()

    except:

        pass


    try:

        ssh.close()

    except:

        pass


    print(
        "\n🔒 SSH Connection Closed."
    )