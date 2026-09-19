import csv
import os
import re
from datetime import datetime

import matplotlib.pyplot as plt


# ============================================================
# 1. FILE PATHS
# ============================================================

CSV_FILE = "reports/system_report.csv"

OUTPUT_FOLDER = "reports/visualizations"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# 2. READ CSV DATA
# ============================================================

def read_csv_data():

    records = []

    if not os.path.exists(CSV_FILE):

        print("\n❌ CSV file not found!")
        print("Expected:", CSV_FILE)

        return records

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            records.append({
                "Date": row.get("Date", "").strip(),
                "Time": row.get("Time", "").strip(),
                "Command": row.get("Command", "").strip(),
                "Output": row.get("Output", "").strip()
            })

    return records


# ============================================================
# 3. MEMORY PARSER
# ============================================================

def parse_memory(output):

    match = re.search(
        r"Mem:\s+([\d.]+)([A-Za-z]+)\s+"
        r"([\d.]+)([A-Za-z]+)\s+"
        r"([\d.]+)([A-Za-z]+)",
        output
    )

    if not match:

        return None

    total = float(match.group(1))
    used = float(match.group(3))
    free = float(match.group(5))

    total_unit = match.group(2)
    used_unit = match.group(4)
    free_unit = match.group(6)

    return {

        "total": total,
        "used": used,
        "free": free,

        "total_unit": total_unit,
        "used_unit": used_unit,
        "free_unit": free_unit

    }


# ============================================================
# 4. MEMORY TO MB
# ============================================================

def memory_to_mb(value, unit):

    unit = unit.lower()

    if unit in ["g", "gb", "gi", "gib"]:

        return value * 1024

    elif unit in ["m", "mb", "mi", "mib"]:

        return value

    elif unit in ["k", "kb", "ki", "kib"]:

        return value / 1024

    return value


# ============================================================
# 5. SYSTEM LOAD PARSER
# ============================================================

def parse_load(output):

    match = re.search(
        r"load average:\s*"
        r"([\d.]+),\s*"
        r"([\d.]+),\s*"
        r"([\d.]+)",
        output
    )

    if not match:

        return None

    return {

        "load1": float(match.group(1)),
        "load5": float(match.group(2)),
        "load15": float(match.group(3))

    }


# ============================================================
# 6. CPU PARSER
# ============================================================

def parse_cpu(output):

    match = re.search(
        r"%Cpu\(s\):\s*([\d.]+)\s+us.*?"
        r"([\d.]+)\s+sy.*?"
        r"([\d.]+)\s+ni.*?"
        r"([\d.]+)\s+id",
        output
    )

    if not match:

        return None

    user = float(match.group(1))
    system = float(match.group(2))
    idle = float(match.group(4))

    cpu_usage = 100 - idle

    return {

        "user": user,
        "system": system,
        "idle": idle,
        "usage": cpu_usage

    }


# ============================================================
# 7. DISK USAGE PARSER
# ============================================================

def parse_disk(output):

    matches = re.findall(
        r"\s(\d+)%\s+(/[^\s|]+)",
        output
    )

    if not matches:

        return None

    # Prefer root filesystem
    for usage, mount in matches:

        if mount == "/":

            return float(usage)

    # Otherwise first filesystem
    return float(matches[0][0])


# ============================================================
# 8. COLLECT DATA FOR ONE DATE
# ============================================================

def collect_date_data(records, selected_date):

    memory_used = []
    memory_free = []

    cpu_usage = []

    disk_usage = []

    load1 = []
    load5 = []
    load15 = []

    times = []


    # --------------------------------------------------------
    # Only selected date
    # --------------------------------------------------------

    date_records = [

        record

        for record in records

        if record["Date"] == selected_date

    ]


    # --------------------------------------------------------
    # Process records
    # --------------------------------------------------------

    for record in date_records:

        command = record["Command"]

        output = record["Output"]

        time = record["Time"]


        # ====================================================
        # MEMORY
        # ====================================================

        if command == "free -h":

            memory = parse_memory(output)

            if memory:

                used_mb = memory_to_mb(
                    memory["used"],
                    memory["used_unit"]
                )

                free_mb = memory_to_mb(
                    memory["free"],
                    memory["free_unit"]
                )

                memory_used.append(
                    used_mb
                )

                memory_free.append(
                    free_mb
                )

                times.append(time)


        # ====================================================
        # CPU
        # ====================================================

        elif command.startswith("top"):

            cpu = parse_cpu(output)

            if cpu:

                cpu_usage.append(
                    cpu["usage"]
                )


        # ====================================================
        # DISK
        # ====================================================

        elif command == "df -h":

            disk = parse_disk(output)

            if disk is not None:

                disk_usage.append(
                    disk
                )


        # ====================================================
        # SYSTEM LOAD
        # ====================================================

        elif command == "uptime":

            load = parse_load(output)

            if load:

                load1.append(
                    load["load1"]
                )

                load5.append(
                    load["load5"]
                )

                load15.append(
                    load["load15"]
                )


    return {

        "times": times,

        "memory_used": memory_used,
        "memory_free": memory_free,

        "cpu_usage": cpu_usage,

        "disk_usage": disk_usage,

        "load1": load1,
        "load5": load5,
        "load15": load15

    }


# ============================================================
# 9. CREATE VISUALIZATION FOR ONE DATE
# ============================================================

def create_visualization(
    selected_date,
    data
):

    print(
        "\n----------------------------------------------"
    )

    print(
        "Creating visualization for:",
        selected_date
    )

    print(
        "----------------------------------------------"
    )


    memory_used = data["memory_used"]
    memory_free = data["memory_free"]

    cpu_usage = data["cpu_usage"]

    disk_usage = data["disk_usage"]

    load1 = data["load1"]
    load5 = data["load5"]
    load15 = data["load15"]

    times = data["times"]


    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(16, 10)
    )


    # ========================================================
    # CPU USAGE
    # ========================================================

    ax1 = axes[0, 0]

    if cpu_usage:

        x = range(
            len(cpu_usage)
        )

        ax1.plot(
            x,
            cpu_usage,
            marker="o",
            label="CPU Usage"
        )

        ax1.set_ylim(
            0,
            100
        )

        ax1.set_xlabel(
            "Monitoring Record"
        )

        ax1.set_ylabel(
            "CPU Usage (%)"
        )

        ax1.set_title(
            "CPU Usage"
        )

        ax1.grid(True)

        ax1.legend()

    else:

        ax1.set_title(
            "CPU Usage - No Data"
        )


    # ========================================================
    # MEMORY USAGE
    # ========================================================

    ax2 = axes[0, 1]

    if memory_used:

        x = range(
            len(memory_used)
        )

        ax2.plot(
            x,
            memory_used,
            marker="o",
            label="Used Memory"
        )

        ax2.plot(
            x,
            memory_free,
            marker="o",
            label="Free Memory"
        )

        ax2.set_xlabel(
            "Monitoring Record"
        )

        ax2.set_ylabel(
            "Memory (MB)"
        )

        ax2.set_title(
            "Memory Usage"
        )

        ax2.grid(True)

        ax2.legend()

    else:

        ax2.set_title(
            "Memory Usage - No Data"
        )


    # ========================================================
    # DISK USAGE
    # ========================================================

    ax3 = axes[1, 0]

    if disk_usage:

        x = range(
            len(disk_usage)
        )

        ax3.bar(
            x,
            disk_usage
        )

        ax3.set_ylim(
            0,
            100
        )

        ax3.set_xlabel(
            "Monitoring Record"
        )

        ax3.set_ylabel(
            "Disk Usage (%)"
        )

        ax3.set_title(
            "Disk Usage"
        )

        ax3.grid(
            axis="y"
        )

    else:

        ax3.set_title(
            "Disk Usage - No Data"
        )


    # ========================================================
    # SYSTEM LOAD
    # ========================================================

    ax4 = axes[1, 1]

    if load1:

        x = range(
            len(load1)
        )

        ax4.plot(
            x,
            load1,
            marker="o",
            label="1 Minute"
        )

        ax4.plot(
            x,
            load5,
            marker="o",
            label="5 Minutes"
        )

        ax4.plot(
            x,
            load15,
            marker="o",
            label="15 Minutes"
        )

        ax4.set_xlabel(
            "Monitoring Record"
        )

        ax4.set_ylabel(
            "Load Average"
        )

        ax4.set_title(
            "System Load"
        )

        ax4.grid(True)

        ax4.legend()

    else:

        ax4.set_title(
            "System Load - No Data"
        )


    # ========================================================
    # MAIN TITLE
    # ========================================================

    fig.suptitle(
        "Linux System Monitoring Visualization",
        fontsize=20
    )


    # ========================================================
    # DATE AND TIME
    # ========================================================

    first_time = ""

    if times:

        first_time = times[0]


    fig.text(

        0.5,
        0.935,

        f"Report Date: {selected_date}    "
        f"Execution Time: {first_time}",

        ha="center",

        fontsize=12

    )


    # ========================================================
    # LAYOUT
    # ========================================================

    plt.tight_layout(
        rect=[
            0,
            0,
            1,
            0.90
        ]
    )


    # ========================================================
    # SAFE DATE FOR FILE NAME
    # ========================================================

    safe_date = selected_date.replace(
        "/",
        "-"
    )


    # ========================================================
    # CREATE FILE NAME
    # ========================================================

    output_file = os.path.join(

        OUTPUT_FOLDER,

        f"linux_system_visualization_"
        f"{safe_date}_"
        f"{datetime.now().strftime('%H-%M-%S')}.png"

    )


    # ========================================================
    # SAVE IMAGE
    # ========================================================

    plt.savefig(

        output_file,

        dpi=200,

        bbox_inches="tight"

    )


    plt.close()


    print(
        "✅ Visualization Created!"
    )

    print(
        "Saved at:",
        output_file
    )


# ============================================================
# 10. MAIN PROGRAM
# ============================================================

def main():

    print(
        "\n=============================================="
    )

    print(
        "     Linux System Visualization"
    )

    print(
        "=============================================="
    )


    # ========================================================
    # READ CSV
    # ========================================================

    records = read_csv_data()


    if not records:

        print(
            "\n❌ No CSV records found."
        )

        return


    print(
        "\nTotal CSV records:",
        len(records)
    )


    # ========================================================
    # GET UNIQUE DATES
    # ========================================================

    unique_dates = []

    for record in records:

        date = record["Date"]

        if date and date not in unique_dates:

            unique_dates.append(date)


    print(
        "\nDates found:"
    )


    for date in unique_dates:

        print(
            " -",
            date
        )


    # ========================================================
    # CREATE VISUALIZATION FOR EACH DATE
    # ========================================================

    for selected_date in unique_dates:

        data = collect_date_data(

            records,

            selected_date

        )


        print(
            "\nData Summary for",
            selected_date
        )

        print(
            "Memory records:",
            len(data["memory_used"])
        )

        print(
            "CPU records:",
            len(data["cpu_usage"])
        )

        print(
            "Disk records:",
            len(data["disk_usage"])
        )

        print(
            "Load records:",
            len(data["load1"])
        )


        create_visualization(

            selected_date,

            data

        )


    # ========================================================
    # COMPLETION
    # ========================================================

    print(
        "\n=============================================="
    )

    print(
        "✅ ALL DATE VISUALIZATIONS CREATED!"
    )

    print(
        "=============================================="
    )

    print(
        "\nVisualization folder:"
    )

    print(
        OUTPUT_FOLDER
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()