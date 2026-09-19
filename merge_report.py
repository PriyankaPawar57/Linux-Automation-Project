import pandas as pd
import os
import glob
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


# ============================================================
# 1. FILE PATHS
# ============================================================

CSV_FILE = "reports/system_report.csv"

VISUALIZATION_FOLDER = "reports/visualizations"

MERGED_REPORT_FOLDER = "reports/merged_reports"


os.makedirs(
    MERGED_REPORT_FOLDER,
    exist_ok=True
)


# ============================================================
# 2. CURRENT DATE AND TIME
# ============================================================

run_datetime = datetime.now()

report_date = run_datetime.strftime(
    "%d-%m-%Y"
)

report_time = run_datetime.strftime(
    "%H:%M:%S"
)

timestamp = run_datetime.strftime(
    "%d-%m-%Y_%H-%M-%S"
)


# ============================================================
# 3. OUTPUT PDF FILE
# ============================================================

pdf_file = os.path.join(
    MERGED_REPORT_FOLDER,
    f"linux_merged_report_{timestamp}.pdf"
)


print("\n==============================================")
print("          LINUX MERGED REPORT")
print("==============================================")


# ============================================================
# 4. CHECK CSV FILE
# ============================================================

if not os.path.exists(CSV_FILE):

    print("\n❌ CSV file not found:")
    print(CSV_FILE)

    exit()


# ============================================================
# 5. READ CSV
# ============================================================

df = pd.read_csv(
    CSV_FILE
)


print(
    "\nTotal records:",
    len(df)
)


# ============================================================
# 6. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Date",
    "Time",
    "Command",
    "Output"
]


for column in required_columns:

    if column not in df.columns:

        print(
            f"\n❌ Required column missing: {column}"
        )

        exit()


# ============================================================
# 7. CLEAN DATE AND TIME
# ============================================================

df["Date"] = (
    df["Date"]
    .astype(str)
    .str.strip()
)

df["Time"] = (
    df["Time"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 8. GET UNIQUE DATES
# ============================================================

unique_dates = (
    df["Date"]
    .dropna()
    .unique()
)


print("\nDates found:")

for date in unique_dates:

    print(
        " -",
        date
    )


# ============================================================
# 9. CHECK VISUALIZATION FOLDER
# ============================================================

if os.path.exists(
    VISUALIZATION_FOLDER
):

    print(
        "\nVisualization folder found:"
    )

    print(
        VISUALIZATION_FOLDER
    )

else:

    print(
        "\n⚠️ Visualization folder not found:"
    )

    print(
        VISUALIZATION_FOLDER
    )


# ============================================================
# 10. PDF DOCUMENT
# ============================================================

pdf = SimpleDocTemplate(

    pdf_file,

    pagesize=landscape(A4),

    rightMargin=25,
    leftMargin=25,
    topMargin=25,
    bottomMargin=25
)


# ============================================================
# 11. PDF STYLES
# ============================================================

styles = getSampleStyleSheet()


title_style = ParagraphStyle(

    "ReportTitle",

    parent=styles["Title"],

    fontSize=20,

    leading=24,

    alignment=TA_CENTER,

    spaceAfter=10
)


heading_style = ParagraphStyle(

    "Heading",

    parent=styles["Heading2"],

    fontSize=14,

    leading=18,

    spaceAfter=8
)


normal_style = ParagraphStyle(

    "NormalText",

    parent=styles["BodyText"],

    fontSize=8,

    leading=10
)


small_style = ParagraphStyle(

    "SmallText",

    parent=styles["BodyText"],

    fontSize=6.5,

    leading=8
)


date_style = ParagraphStyle(

    "DateHeading",

    parent=styles["Heading1"],

    fontSize=16,

    leading=20,

    alignment=TA_CENTER,

    spaceAfter=12
)


# ============================================================
# 12. PDF CONTENT
# ============================================================

story = []


# ============================================================
# 13. MAIN REPORT TITLE
# ============================================================

story.append(

    Paragraph(
        "Linux System Monitoring - Merged Report",
        title_style
    )
)


story.append(

    Paragraph(
        f"<b>Report Generated Date:</b> "
        f"{report_date}",
        normal_style
    )
)


story.append(

    Paragraph(
        f"<b>Report Generated Time:</b> "
        f"{report_time}",
        normal_style
    )
)


story.append(
    Spacer(1, 15)
)


# ============================================================
# 14. PROCESS EACH DATE
# ============================================================

for date_index, current_date in enumerate(unique_dates):


    print(
        "\n=============================================="
    )

    print(
        "Processing date:",
        current_date
    )

    print(
        "=============================================="
    )


    # ========================================================
    # FILTER DATA FOR CURRENT DATE
    # ========================================================

    date_df = df[
        df["Date"] == str(current_date)
    ].copy()


    # ========================================================
    # DATE HEADING
    # ========================================================

    story.append(

        Paragraph(
            f"System Report - {current_date}",
            date_style
        )
    )


    # ========================================================
    # EXECUTION TIMES
    # ========================================================

    execution_times = (

        date_df["Time"]

        .dropna()

        .astype(str)

        .unique()

    )


    if len(execution_times) > 0:

        execution_text = ", ".join(
            execution_times
        )

        story.append(

            Paragraph(

                f"<b>Execution Time:</b> "
                f"{execution_text}",

                normal_style

            )
        )


    story.append(
        Spacer(1, 10)
    )


    # ========================================================
    # TABLE DATA
    # ========================================================

    table_data = []


    # ========================================================
    # TABLE HEADER
    # ========================================================

    header = [

        Paragraph(
            "<b>Date</b>",
            normal_style
        ),

        Paragraph(
            "<b>Time</b>",
            normal_style
        ),

        Paragraph(
            "<b>Command</b>",
            normal_style
        ),

        Paragraph(
            "<b>Output</b>",
            normal_style
        )
    ]


    table_data.append(
        header
    )


    # ========================================================
    # TABLE ROWS
    # ========================================================

    for _, row in date_df.iterrows():


        date_value = str(
            row["Date"]
        )


        time_value = str(
            row["Time"]
        )


        command_value = str(
            row["Command"]
        )


        output_value = str(
            row["Output"]
        )


        # ----------------------------------------------------
        # Escape HTML characters
        # ----------------------------------------------------

        date_value = (
            date_value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        time_value = (
            time_value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        command_value = (
            command_value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        output_value = (
            output_value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


        row_data = [

            Paragraph(
                date_value,
                small_style
            ),

            Paragraph(
                time_value,
                small_style
            ),

            Paragraph(
                command_value,
                small_style
            ),

            Paragraph(
                output_value,
                small_style
            )
        ]


        table_data.append(
            row_data
        )


    # ========================================================
    # CREATE TABLE
    # ========================================================

    data_table = Table(

        table_data,

        repeatRows=1,

        colWidths=[
            70,
            70,
            110,
            520
        ]
    )


    # ========================================================
    # TABLE STYLE
    # ========================================================

    data_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.darkblue
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
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
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


    # ========================================================
    # ADD TABLE
    # ========================================================

    story.append(
        data_table
    )


    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # VISUALIZATION SECTION
    # ========================================================

    story.append(

        Paragraph(
            "System Visualization",
            heading_style
        )
    )


    # ========================================================
    # FIND VISUALIZATION
    # ========================================================

    visualization_files = []


    if os.path.exists(
        VISUALIZATION_FOLDER
    ):


        # ----------------------------------------------------
        # Search pattern
        # ----------------------------------------------------

        search_pattern = os.path.join(

            VISUALIZATION_FOLDER,

            f"linux_system_visualization_{current_date}_*.png"

        )


        print(
            "\nSearching visualization:"
        )


        print(
            search_pattern
        )


        # ----------------------------------------------------
        # Find files
        # ----------------------------------------------------

        visualization_files = glob.glob(
            search_pattern
        )


    # ========================================================
    # SORT FILES
    # ========================================================

    visualization_files.sort(
        key=os.path.getmtime
    )


    # ========================================================
    # DISPLAY FOUND FILES
    # ========================================================

    if visualization_files:


        print(
            "\n✅ Visualization files found:"
        )


        for file in visualization_files:

            print(
                "   ",
                os.path.basename(file)
            )


        # ----------------------------------------------------
        # Select latest visualization
        # ----------------------------------------------------

        image_path = visualization_files[-1]


        latest_visualization = os.path.basename(
            image_path
        )


        print(
            "\n✅ Using latest visualization:"
        )


        print(
            latest_visualization
        )


        # ====================================================
        # ADD IMAGE
        # ====================================================

        try:


            image = Image(

                image_path,

                width=700,

                height=420

            )


            story.append(
                image
            )


            story.append(
                Spacer(1, 10)
            )


            story.append(

                Paragraph(

                    f"<b>Visualization File:</b> "
                    f"{latest_visualization}",

                    small_style

                )
            )


            print(
                "✅ Visualization added to PDF."
            )


        except Exception as e:


            print(
                "\n❌ Visualization loading error:"
            )


            print(
                e
            )


            story.append(

                Paragraph(

                    "Visualization could not be loaded.",

                    normal_style

                )
            )


    else:


        print(
            "\n⚠️ No visualization found for:"
        )


        print(
            current_date
        )


        story.append(

            Paragraph(

                f"No visualization available "
                f"for {current_date}.",

                normal_style

            )
        )


    # ========================================================
    # PAGE BREAK
    # ========================================================

    if date_index < len(unique_dates) - 1:


        story.append(
            PageBreak()
        )


# ============================================================
# 15. BUILD PDF
# ============================================================

print(
    "\n=============================================="
)

print(
    "           Creating PDF"
)

print(
    "=============================================="
)


pdf.build(
    story
)


# ============================================================
# 16. SUCCESS MESSAGE
# ============================================================

print(
    "\n=============================================="
)

print(
    "✅ MERGED REPORT CREATED SUCCESSFULLY!"
)

print(
    "=============================================="
)


print(
    "\nSaved at:"
)

print(
    pdf_file
)


print(
    "\nReport contains:"
)

print(
    "✅ Complete CSV/System Data"
)

print(
    "✅ Date and Time"
)

print(
    "✅ Separate page for each date"
)

print(
    "✅ Latest visualization for each date"
)

print(
    "✅ Visualization filename"
)

print(
    "✅ Report Generation Date & Time"
)

print(
    "✅ Old merged reports are NOT overwritten"
)


print(
    "\n=============================================="
)