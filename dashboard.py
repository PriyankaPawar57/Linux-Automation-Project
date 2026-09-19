import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime, time
import plotly.express as px


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Linux System Monitoring Dashboard",
    page_icon="💻",
    layout="wide"
)


# ============================================================
# FILE PATH
# ============================================================

CSV_FILE = "reports/system_report.csv"


# ============================================================
# TITLE
# ============================================================

st.title("💻 Linux System Monitoring Dashboard")

st.caption(
    "Interactive dashboard for Linux system monitoring data"
)


# ============================================================
# LOAD CSV
# ============================================================

@st.cache_data
def load_data():

    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            CSV_FILE,
            encoding="utf-8"
        )

        # Remove unwanted spaces from column names
        df.columns = df.columns.str.strip()

        # Make sure required columns exist
        required_columns = [
            "Date",
            "Time",
            "Command",
            "Output"
        ]

        for column in required_columns:

            if column not in df.columns:
                df[column] = ""

        # Convert Date
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
            dayfirst=True
        )

        # Convert Time to string
        df["Time"] = df["Time"].astype(str)

        # Convert Command to string
        df["Command"] = df["Command"].astype(str)

        # Convert Output to string
        df["Output"] = df["Output"].fillna("").astype(str)

        # Create DateTime column
        df["DateTime"] = pd.to_datetime(
            df["Date"].dt.strftime("%Y-%m-%d")
            + " "
            + df["Time"],
            errors="coerce"
        )

        # Remove invalid DateTime rows
        df = df.dropna(
            subset=["DateTime"]
        )

        return df

    except Exception as e:

        st.error(
            f"CSV reading error: {e}"
        )

        return pd.DataFrame()


# ============================================================
# READ DATA
# ============================================================

df = load_data()


# ============================================================
# CHECK DATA
# ============================================================

if df.empty:

    st.error(
        "❌ No data found."
    )

    st.info(
        f"CSV expected at: {CSV_FILE}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filters")


# ============================================================
# DATE FILTER
# ============================================================

available_dates = sorted(
    df["DateTime"].dt.date.unique()
)


selected_date = st.sidebar.selectbox(
    "📅 Select Date",
    available_dates
)


# ============================================================
# FILTER DATA BY DATE
# ============================================================

date_df = df[
    df["DateTime"].dt.date == selected_date
].copy()


if date_df.empty:

    st.warning(
        "No records available for selected date."
    )

    st.stop()


# ============================================================
# TIME VALUES
# ============================================================

time_values = sorted(
    date_df["DateTime"].dt.time.unique()
)


if not time_values:

    st.warning(
        "No time data available."
    )

    st.stop()


# ============================================================
# START TIME
# ============================================================

start_time = st.sidebar.selectbox(
    "🕐 Start Time",
    time_values,
    format_func=lambda x: x.strftime("%H:%M:%S")
)


# ============================================================
# END TIME OPTIONS
# ============================================================

end_time_values = [
    t for t in time_values
    if t >= start_time
]


if not end_time_values:
    end_time_values = [start_time]


end_time = st.sidebar.selectbox(
    "🕐 End Time",
    end_time_values,
    index=len(end_time_values) - 1,
    format_func=lambda x: x.strftime("%H:%M:%S")
)


# ============================================================
# COMMAND LIST
# ============================================================

commands = sorted(
    date_df["Command"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


# ============================================================
# COMMAND MULTISELECT
# ============================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    "💻 Select Commands"
)


selected_commands = st.sidebar.multiselect(
    "Choose Commands",
    options=commands,
    default=[],
    placeholder="Select one or more commands..."
)


# ============================================================
# RESET COMMAND FILTER
# ============================================================

if selected_commands:

    command_df = date_df[
        date_df["Command"].isin(
            selected_commands
        )
    ].copy()

else:

    command_df = date_df.copy()


# ============================================================
# TIME FILTER
# ============================================================

filtered_df = command_df[
    (
        command_df["DateTime"].dt.time >= start_time
    )
    &
    (
        command_df["DateTime"].dt.time <= end_time
    )
].copy()


# ============================================================
# SELECTED FILTER SUMMARY
# ============================================================

st.header("📋 Selected Filters")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Selected Date",
        selected_date.strftime("%d-%m-%Y")
    )


with col2:

    st.metric(
        "Start Time",
        start_time.strftime("%H:%M:%S")
    )


with col3:

    st.metric(
        "End Time",
        end_time.strftime("%H:%M:%S")
    )


# ============================================================
# SELECTED COMMANDS
# ============================================================

if selected_commands:

    st.write(
        "**Selected Commands:**",
        ", ".join(selected_commands)
    )

else:

    st.write(
        "**Selected Commands:** All Commands"
    )


st.divider()


# ============================================================
# RECORD COUNT
# ============================================================

st.header("📊 System Performance Summary")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Records",
        len(filtered_df)
    )


# ============================================================
# MEMORY PARSER
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

    return (
        total,
        used,
        free,
        total_unit,
        used_unit,
        free_unit
    )


# ============================================================
# MEMORY TO MB
# ============================================================

def memory_to_mb(value, unit):

    unit = unit.lower()

    if unit in ["g", "gb", "gi", "gib"]:
        return value * 1024

    if unit in ["m", "mb", "mi", "mib"]:
        return value

    if unit in ["k", "kb", "ki", "kib"]:
        return value / 1024

    return value


# ============================================================
# CPU PARSER
# ============================================================

def parse_cpu(output):

    match = re.search(
        r"%Cpu\(s\):\s*([\d.]+)\s+us.*?"
        r"([\d.]+)\s+sy.*?"
        r"([\d.]+)\s+ni.*?"
        r"([\d.]+)\s+id",
        output,
        re.DOTALL
    )

    if not match:
        return None

    user = float(match.group(1))
    system = float(match.group(2))
    idle = float(match.group(4))

    usage = 100 - idle

    return usage


# ============================================================
# DISK PARSER
# ============================================================

def parse_disk(output):

    matches = re.findall(
        r"\s(\d+)%\s+(/[^\s]+)",
        output
    )

    if not matches:
        return None

    # Prefer root /
    for usage, mount in matches:

        if mount == "/":

            return float(usage)

    return float(
        matches[0][0]
    )


# ============================================================
# LOAD PARSER
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

    return (
        float(match.group(1)),
        float(match.group(2)),
        float(match.group(3))
    )


# ============================================================
# COLLECT METRICS
# ============================================================

cpu_data = []
memory_data = []
disk_data = []

load1_data = []
load5_data = []
load15_data = []

cpu_times = []
memory_times = []
disk_times = []
load_times = []


for _, row in filtered_df.iterrows():

    command = row["Command"]
    output = row["Output"]
    dt = row["DateTime"]


    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    if command.startswith("top"):

        cpu = parse_cpu(output)

        if cpu is not None:

            cpu_data.append(cpu)
            cpu_times.append(dt)


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    if command == "free -h":

        memory = parse_memory(output)

        if memory:

            (
                total,
                used,
                free,
                total_unit,
                used_unit,
                free_unit
            ) = memory

            used_mb = memory_to_mb(
                used,
                used_unit
            )

            memory_data.append(
                used_mb
            )

            memory_times.append(
                dt
            )


    # --------------------------------------------------------
    # DISK
    # --------------------------------------------------------

    if command == "df -h":

        disk = parse_disk(output)

        if disk is not None:

            disk_data.append(disk)
            disk_times.append(dt)


    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    if command == "uptime":

        load = parse_load(output)

        if load:

            load1, load5, load15 = load

            load1_data.append(load1)
            load5_data.append(load5)
            load15_data.append(load15)

            load_times.append(dt)


# ============================================================
# SUMMARY METRICS
# ============================================================

with col2:

    if cpu_data:

        st.metric(
            "Average CPU Usage",
            f"{sum(cpu_data) / len(cpu_data):.2f}%"
        )

    else:

        st.metric(
            "Average CPU Usage",
            "N/A"
        )


with col3:

    if memory_data:

        st.metric(
            "Average Memory",
            f"{sum(memory_data) / len(memory_data):.2f} MB"
        )

    else:

        st.metric(
            "Average Memory",
            "N/A"
        )


with col4:

    if disk_data:

        st.metric(
            "Average Disk Usage",
            f"{sum(disk_data) / len(disk_data):.2f}%"
        )

    else:

        st.metric(
            "Average Disk Usage",
            "N/A"
        )


st.divider()


# ============================================================
# CPU GRAPH
# ============================================================

st.header("⚙️ CPU Usage")


if cpu_data:

    cpu_chart = pd.DataFrame({
        "DateTime": cpu_times,
        "CPU Usage (%)": cpu_data
    })

    fig_cpu = px.line(
        cpu_chart,
        x="DateTime",
        y="CPU Usage (%)",
        markers=True,
        title="CPU Usage Over Time"
    )

    fig_cpu.update_yaxes(
        range=[0, 100]
    )

    st.plotly_chart(
        fig_cpu,
        use_container_width=True
    )

else:

    st.info(
        "No CPU data available for selected filters."
    )


# ============================================================
# MEMORY GRAPH
# ============================================================

st.header("🧠 Memory Usage")


if memory_data:

    memory_chart = pd.DataFrame({
        "DateTime": memory_times,
        "Memory Used (MB)": memory_data
    })

    fig_memory = px.line(
        memory_chart,
        x="DateTime",
        y="Memory Used (MB)",
        markers=True,
        title="Memory Usage Over Time"
    )

    st.plotly_chart(
        fig_memory,
        use_container_width=True
    )

else:

    st.info(
        "No memory data available for selected filters."
    )


# ============================================================
# DISK GRAPH
# ============================================================

st.header("💾 Disk Usage")


if disk_data:

    disk_chart = pd.DataFrame({
        "DateTime": disk_times,
        "Disk Usage (%)": disk_data
    })

    fig_disk = px.bar(
        disk_chart,
        x="DateTime",
        y="Disk Usage (%)",
        title="Disk Usage Over Time"
    )

    fig_disk.update_yaxes(
        range=[0, 100]
    )

    st.plotly_chart(
        fig_disk,
        use_container_width=True
    )

else:

    st.info(
        "No disk data available for selected filters."
    )


# ============================================================
# SYSTEM LOAD
# ============================================================

st.header("📈 System Load")


if load1_data:

    load_chart = pd.DataFrame({
        "DateTime": load_times,
        "1 Minute": load1_data,
        "5 Minutes": load5_data,
        "15 Minutes": load15_data
    })

    fig_load = px.line(
        load_chart,
        x="DateTime",
        y=[
            "1 Minute",
            "5 Minutes",
            "15 Minutes"
        ],
        markers=True,
        title="System Load Average"
    )

    st.plotly_chart(
        fig_load,
        use_container_width=True
    )

else:

    st.info(
        "No load data available for selected filters."
    )


# ============================================================
# COMMAND OUTPUT
# ============================================================

st.divider()

st.header("💻 Command Output")


if selected_commands:

    command_output_df = filtered_df[
        filtered_df["Command"].isin(
            selected_commands
        )
    ].copy()

else:

    command_output_df = filtered_df.copy()


if not command_output_df.empty:

    # --------------------------------------------------------
    # Command selection for viewing output
    # --------------------------------------------------------

    output_commands = sorted(
        command_output_df["Command"]
        .unique()
        .tolist()
    )


    selected_output_command = st.selectbox(
        "🔍 Open Command Output",
        output_commands,
        key="command_output_selector"
    )


    selected_output = command_output_df[
        command_output_df["Command"]
        == selected_output_command
    ].copy()


    # --------------------------------------------------------
    # Show output
    # --------------------------------------------------------

    for _, row in selected_output.iterrows():

        with st.expander(
            f"📌 {row['Command']} | "
            f"{row['DateTime'].strftime('%d-%m-%Y %H:%M:%S')}"
        ):

            st.code(
                row["Output"],
                language="text"
            )


else:

    st.warning(
        "No records found for the selected filters."
    )


# ============================================================
# FULL FILTERED DATA
# ============================================================

st.divider()

st.header("📋 Filtered Monitoring Records")


display_df = filtered_df[
    [
        "DateTime",
        "Date",
        "Time",
        "Command",
        "Output"
    ]
].copy()


display_df["Date"] = display_df[
    "Date"
].dt.strftime("%d-%m-%Y")


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD CSV
# ============================================================

st.divider()

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_data,
    file_name="filtered_system_report.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Linux System Monitoring Dashboard | "
    "Interactive Date, Time and Command Filtering"
)