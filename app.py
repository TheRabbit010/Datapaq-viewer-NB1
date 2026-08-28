import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# 1. ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Datapaq Analytics WebApp", layout="wide", page_icon="🔥")
st.title("🔥 Datapaq Furnace Profile Advanced Viewer")
st.write("ระบบวิเคราะห์โปรไฟล์เตาอบความร้อนอัจฉริยะ (เวอร์ชันปรับแต่งโซนเตาอบผ่านหน้าเว็บได้อิสระ)")

# 2. ฟังก์ชันประมวลผลเตรียมข้อมูลดิบ (Data Processing Stage)
def process_raw_data(uploaded_file):
    raw_bytes = uploaded_file.read()
    try:
        file_text = raw_bytes.decode("utf-8")
    except:
        file_text = raw_bytes.decode("cp1252", errors="ignore")
        
    lines = file_text.splitlines()
    start_line = 0
    for idx, line in enumerate(lines):
        if "time" in line.lower() and ("ch" in line.lower() or "pb#" in line.lower() or "temp" in line.lower()):
            start_line = idx
            break
            
    data_body = "\n".join(lines[start_line:])
    df = pd.read_csv(io.StringIO(data_body), sep=None, engine='python')
    
    # ทำความสะอาดคอลัมน์
    df.columns = [str(col).strip() for col in df.columns]
    
    raw_time_col = df.columns[0]
    
    if "Time_Seconds" not in df.columns:
        df["Time_Seconds"] = pd.to_numeric(df[raw_time_col], errors='coerce').fillna(0)
    
    if "Time_HHMMSS" not in df.columns:
        df["Time_HHMMSS"] = df["Time_Seconds"].apply(
            lambda x: f"{int(x//3600):02d}:{int((x%3600)//60):02d}:{int(x%60):02d}"
        )
        
    for col in df.columns:
        if col.startswith("CH") or col.startswith("Channel"):
            df.rename(columns={col: col.replace("CH", "PB#").replace("Channel ", "PB#")}, inplace=True)
            
    probe_cols = [c for c in df.columns if c.startswith("PB#")]
    
    detected_start_sec = 0
    probe_start_info = {}
    
    for col in probe_cols:
        entry_rows = df[df[col] >= 60.0]
        if not entry_rows.empty:
            start_sec = entry_rows["Time_Seconds"].iloc[0]
            start_time_str = entry_rows["Time_HHMMSS"].iloc[0]
        else:
            start_sec = df["Time_Seconds"].iloc[0]
            start_time_str = df["Time_HHMMSS"].iloc[0]
            
        probe_start_info[col] = {
            "Start_Sec": start_sec,
            "Start_HHMMSS": start_time_str,
            "Is_First": False,
            "Offset_Sec": 0
        }
        
    if probe_start_info:
        first_probe = min(probe_start_info, key=lambda k: probe_start_info[k]["Start_Sec"])
        detected_start_sec = probe_start_info[first_probe]["Start_Sec"]
        probe_start_info[first_probe]["Is_First"] = True
        
        for col in probe_cols:
            probe_start_info[col]["Offset_Sec"] = int(probe_start_info[col]["Start_Sec"] - detected_start_sec)
            
    return df, probe_cols, detected_start_sec, probe_start_info, uploaded_file.name

# 3. สร้างแผงควบคุมที่ Sidebar ด้านซ้ายสำหรับกรอกค่าแบบ Dynamic
st.sidebar.header("🛠️ ตั้งค่าเกณฑ์ควบคุมวิกฤต")
TRIGGER_TEMP_BRAZING = st.sidebar.number_input("Brazing Temp Threshold (°C)", min_value=0.0, max_value=1200.0, value=577.0, step=1.0)
active_furnace = st.sidebar.text_input("ชื่อเตาอบ (Furnace ID)", value="NB2")

st.sidebar.markdown("---")
st.sidebar.header("📐 ปรับช่วงวินาทีในแต่ละโซนเตา")

# สร้างฟังก์ชันจำลองให้กรอกข้อมูลโซนได้สูงสุด 6 โซน
FURNACE_ZONES = []
num_zones = st.sidebar.slider("จำนวนโซนเตาอบที่ต้องการระบุ:", min_value=1, max_value=8, value=5)

# ค่าเริ่มต้นเริ่มต้น (Default values) เผื่อผู้ใช้ขี้เกียจกรอกใหม่
default_zones = [
    {"name": "Dryer Zo#1", "start": 0, "end": 120, "group": "Dryer"},
    {"name": "Zone 2", "start": 120, "end": 420, "group": "Heating"},
    {"name": "Zone 3", "start": 420, "end": 720, "group": "Heating"},
    {"name": "Brazing High", "start": 720, "end": 1020, "group": "Brazing"},
    {"name": "Cooling Zone", "start": 1020, "end": 1500, "group": "Cooling"},
    {"name": "Zone 6", "start": 1500, "end": 1800, "group": "Cooling"},
    {"name": "Zone 7", "start": 1800, "end": 2100, "group": "Cooling"},
    {"name": "Zone 8", "start": 2100, "end": 2400, "group": "Cooling"}
]

GROUP_COLORS = {
    "Dryer": "rgba(255, 235, 153, 0.25)",
    "Heating": "rgba(255, 153, 102, 0.2)",
    "Brazing": "rgba(255, 102, 102, 0.25)",
    "Cooling": "rgba(102, 204, 255, 0.2)"
}

# ลูปสร้างกล่องรับข้อมูลใน Sidebar แบบสแกนทีละโซน
for i in range(num_zones):
    with st.sidebar.expander(f"📦 โซนที่ {i+1}: {default_zones[i]['name']}"):
        z_name = st.text_input(f"ชื่อโซน {i+1}", value=default_zones[i]['name'], key=f"name_{i}")
        col_s, col_e = st.columns(2)
        with col_s:
            z_start = st.number_input(f"เริ่ม (วินาที)", value=default_zones[i]['start'], min_value=0, key=f"start_{i}")
        with col_e:
            z_end = st.number_input(f"สิ้นสุด (วินาที)", value=default_zones[i]['end'], min_value=0, key=f"end_{i}")
        z_group = st.selectbox(f"กลุ่มสีพื้นหลัง", options=["Dryer", "Heating", "Brazing", "Cooling"], index=["Dryer", "Heating", "Brazing", "Cooling"].index(default_zones[i]['group']), key=f"group_{i}")
        
        FURNACE_ZONES.append({
            "num": i+1,
            "name": z_name,
            "start_sec": z_start,
            "end_sec": z_end,
            "group": z_group
        })

# 4. ส่วนอินเทอร์เฟซอัปโหลดไฟล์หลัก
uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์รายงานจาก Colab ของคุณที่นี่เพื่อเริ่มพล็อตกราฟ", type=["txt", "csv", "xlsx"])

if uploaded_file is not None:
    try:
        df_master, probe_cols, detected_start_sec, probe_start_info, paq_file = process_raw_data(uploaded_file)
        
        if "Elapsed_Seconds" not in df_master.columns:
            df_master["Elapsed_Seconds"] = df_master["Time_Seconds"] - detected_start_sec
        elapsed_mins = df_master["Elapsed_Seconds"] / 60.0
        
        plot_title = paq_file.replace(".paq", "")
        
        st.success("📊 คำนวณและกระจายค่าพล็อตร่วมกับตารางแผงควบคุมสำเร็จ!")
        
        # ส่วนแท็บการแสดงผลกราฟและรายงานตารางข้อมูล
        tab1, tab2, tab3 = st.tabs(["📈 Chart 1: Global Time Profile", "📊 Table Summary", "📉 Chart 2: Aligned Probe Profile"])
        
        with tab1:
            st.subheader("CHART 1: GLOBAL FURNACE PROFILE")
            custom_hover_data1 = np.stack(
                (df_master["Time_HHMMSS"], df_master["Time_Seconds"], df_master["Elapsed_Seconds"]), axis=-1
            )
            fig1 = go.Figure()
            for col in probe_cols:
                fig1.add_trace(go.Scatter(
                    x=elapsed_mins, y=df_master[col], mode="lines", name=col,
                    customdata=custom_hover_data1,
                    hovertemplate=(
                        "<b>%{fullData.name}</b>: <b style='font-size:14px;'>%{y:.1f} °C</b><br>"
                        "Elapsed: <b>%{x:.2f} min</b> (%{customdata[2]:.0f}s)<br>"
                        "Clock Time: %{customdata[0]}<extra></extra>"
                    )
                ))
            
            # วาดแถบสีตามค่าปัจจุบันในแผงควบคุม (Dynamic vrect)
            for z in FURNACE_ZONES:
                fig1.add_vrect(
                    x0=z["start_sec"]/60.0, x1=z["end_sec"]/60.0, fillcolor=GROUP_COLORS.get(z["group"], "rgba(200,200,200,0.2)"),
                    layer="below", line_width=0.5, line_dash="dot", line_color="rgba(120, 120, 120, 0.4)",
                    annotation_text=f"<b>{z['num']}.{z['name']}</b>", annotation_position="top left",
                    annotation=dict(font_size=9, font_color="#222222", textangle=-90)
                )
            fig1.add_hline(y=TRIGGER_TEMP_BRAZING, line_dash="dash", line_color="red", line_width=1.5,
                           annotation_text=f"<b>Brazing Temp Threshold ({TRIGGER_TEMP_BRAZING}°C)</b>", annotation_position="bottom right")
            fig1.add_vline(x=0.0, line_dash="solid", line_color="green", line_width=2,
                           annotation_text=" <b>First Probe Entrance (0:00)</b>", annotation_position="bottom right")
            fig1.update_layout(
                title=f"<b>CHART 1: GLOBAL FURNACE PROFILE ({active_furnace} TIME BASED):</b> {plot_title}",
                xaxis=dict(title="Elapsed Time (Minutes)", showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)', zeroline=True, zerolinecolor='black'),
                yaxis=dict(title="Temperature (°C)", showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
                hovermode="x unified", template="plotly_white", height=600,
                legend=dict(title="Probes", x=1.01, y=1, bordercolor="LightGray", borderwidth=1)
            )
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.subheader("📊 INDIVIDUAL PROBE START POINT ALIGNMENT SUMMARY (60°C ENTRY)")
            shift_table_rows = []
            for col, info in probe_start_info.items():
                status = "🏆 First (Lead Probe)" if info["Is_First"] else f"+{info['Offset_Sec']}s lag"
                shift_table_rows.append({
                    "Probe": col,
                    "Start Time (HH:MM:SS)": info["Start_HHMMSS"],
                    "Start Sec": f"{info['Start_Sec']}s",
                    "Lag Time vs First Probe": f"+{info['Offset_Sec']}s" if info['Offset_Sec'] > 0 else "0s (Lead)",
                    "Status": status
                })
            df_shift_summary = pd.DataFrame(shift_table_rows)
            st.dataframe(df_shift_summary, use_container_width=True, hide_index=True)

        with tab3:
            st.subheader("CHART 2: INDIVIDUALLY ALIGNED PROBE CHART")
            fig2 = go.Figure()
            for col in probe_cols:
                p_start_sec = probe_start_info[col]["Start_Sec"]
                offset_sec = probe_start_info[col]["Offset_Sec"]
                indiv_elapsed_mins = (df_master["Time_Seconds"] - p_start_sec) / 60.0
                indiv_hover_data = np.stack(
