import paramiko
import pandas as pd
import os
from datetime import datetime
import sqlite3

# PDF Libraries
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Parse Memory Data
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

# User Input
host = input("Enter Linux IP Address: ")
username = input("Enter Username: ")
password = input("Enter Password: ")

# Create SSH Client
ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy()
)

try:
    # Connect to Linux
    ssh.connect(
        hostname=host,
        username=username,
        password=password
    )
    print("\n✅ Connected Successfully!")

    # Current Date and Time
    current_date = datetime.now().strftime("%d-%m-%Y")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Create Reports Folder
    os.makedirs("reports", exist_ok=True)
    
    # SQLite Database
    conn = sqlite3.connect(
        "reports/system_report.db"
    )
    cursor = conn.cursor()

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
    
    # Linux Commands
    commands = [
        "hostname",
        "hostname -I",
        "uptime",
        "free -h",
        "df -h",
        "vmstat",
        "top -bn1 | head -5"
    ]
    # Store Results
    results = {}

    for cmd in commands:

        print("\n" + "=" * 60)
        print("Running:", cmd)

        stdin, stdout, stderr = ssh.exec_command(cmd)

        output = stdout.read().decode().strip()

        error = stderr.read().decode().strip()

        if error:

            results[cmd] = error

            print(error)

        else:

            results[cmd] = output

            print(output)

            # Parse Memory Data
            if cmd == "free -h":

                memory_data = parse_free_memory(output)

                print("\n===== Parsed Memory Data =====")

                for key, value in memory_data.items():

                    print(f"{key}: {value}")

    # Clean Output
    clean_results = {}

    for cmd, output in results.items():

        # Store Data into SQLite
        cursor.execute("""
            INSERT INTO system_report
            (date, time, command, output)
            VALUES (?, ?, ?, ?)
        """, (
            current_date,
            current_time,
            cmd,
            output
        ))

        # Clean Output
        clean_output = " ".join(
            output.split()
        )
        clean_results[cmd] = clean_output
    conn.commit()

    # Create DataFrame
    df = pd.DataFrame(
        list(clean_results.items()),
        columns=["Command", "Output"]
    )

    # Add Timestamp
    df.insert(
        0,
        "Date",
        current_date
    )
    df.insert(
        1,
        "Time",
        current_time
    )

    # Excel File
    file_path = "reports/system_report.xlsx"

    if os.path.exists(file_path):

        old_excel = pd.read_excel(
            file_path
        )

        final_excel = pd.concat(
            [old_excel, df],
            ignore_index=True
        )

    else:
        
        final_excel = df

    # Save Excel
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

    # CSV File
    csv_file_path = "reports/system_report.csv"

    if os.path.exists(csv_file_path):

        old_df = pd.read_csv(
            csv_file_path
        )

        final_df = pd.concat(
            [old_df, df],
            ignore_index=True
        )

    else:

        final_df = df

    # Save CSV
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

    # CSV TO PDF CONVERSION
    print(
        "\n===== Converting CSV to PDF ====="
    )

    pdf_file_path = (
        "reports/system_report.pdf"
    )

    # Create PDF document
    pdf = SimpleDocTemplate(
        pdf_file_path,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    # PDF Styles
    styles = getSampleStyleSheet()

    title = Paragraph(
        "<b>Linux System Information Report</b>",
        styles["Title"]
    )

    subtitle = Paragraph(
        f"Generated on: {current_date} {current_time}",
        styles["Normal"]
    )

    # Read CSV
    pdf_df = pd.read_csv(
        csv_file_path
    )

    # Prepare PDF Table
    table_data = []
    # Header Row
    header = [
        Paragraph(
            f"<b>{column}</b>",
            styles["BodyText"]
        )
        for column in pdf_df.columns
    ]
    table_data.append(header)

    # Data Rows
    for _, row in pdf_df.iterrows():

        row_data = []

        for value in row.tolist():

            row_data.append(
                Paragraph(
                    str(value),
                    styles["BodyText"]
                )
            )

        table_data.append(row_data)

    # Create PDF Table
    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            70,
            70,
            100,
            500
        ]
    )

    # PDF Table Formatting
    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    # Generate PDF
    pdf.build([
        title,
        Spacer(1, 10),
        subtitle,
        Spacer(1, 10),
        table
    ])
    
    print(
        "\n✅ PDF Report Generated Successfully!"
    )

    print(
        "Saved at:",
        pdf_file_path
    )

    # Display SQLite Records
    print(
        "\n===== SQLite Database Records ====="
    )

    cursor.execute(
        "SELECT * FROM system_report"
    )

    rows = cursor.fetchall()

    for row in rows:

        print(row)

# Exception Handling
except Exception as e:

    print(
        "\n❌ Error:",
        e
    )

# Finally
finally:

    try:

        conn.commit()
        conn.close()

    except:

        pass

    ssh.close()

    print(
        "\n🔒 SSH Connection Closed."
    )