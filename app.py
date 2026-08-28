import streamlit as st
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET
import io

# 1. ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Datapaq Profile Viewer", layout="wide", page_icon="📊")
st.title("📊 Datapaq (.paq) Interactive Graph Viewer")
st.write("อัปโหลดไฟล์ `.paq` ของคุณเพื่อแปลงเป็นกราฟพล็อตอุณหภูมิแบบ Interactive (ซูมและเปิด-ปิดแชนเนลได้)")

# 2. ฟังก์ชันสำหรับอ่านและแปลงไฟล์ .paq ทุกรูปแบบ
def process_datapaq(uploaded_file):
    # อ่านไฟล์เป็นไบนารีและแปลงเป็นข้อความ (UTF-8 หรือ ANSI)
    raw_bytes = uploaded_file.read()
    try:
        file_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        file_text = raw_bytes.decode("ansi", errors="ignore")
    
    # --- รูปแบบที่ 1: ตรวจสอบว่าเป็นไฟล์ XML หรือไม่ ---
    if file_text.strip().startswith("<?xml") or "<Data" in file_text:
        try:
            root = ET.fromstring(file_text)
            
            # มองหาแท็กข้อมูลอุณหภูมิ (ส่วนใหญ่จะอยู่ใน <DataRow> หรือ <Sample>)
            time_list = []
            channels_data = {}
            
            # ลูปค้นหาตำแหน่งข้อมูล (ปรับตามโครงสร้าง XML ทั่วไปของ Datapaq)
            for row in root.findall(".//DataRow") or root.findall(".//Sample"):
                # ดึงค่าเวลา (Time)
                t_val = row.get("Time") or row.findtext("Time")
                if t_val is not None:
                    time_list.append(float(t_val))
                    
                    # ดึงค่าวาล์วอุณหภูมิในแต่ละจุด (เช่น <Val Ch="1">150.2</Val>)
                    for val_tag in row.findall("Val") or row.findall("Value"):
                        ch_num = val_tag.get("Ch") or val_tag.get("Channel")
                        ch_name = f"Channel {ch_num}"
                        if ch_name not in channels_data:
                            channels_data[ch_name] = []
                        channels_data[ch_name].append(float(val_tag.text))
            
            if time_list and channels_data:
                channels_data["Time (s)"] = time_list
                df = pd.DataFrame(channels_data)
                # สลับให้คอลัมน์ Time ขึ้นก่อน
                cols = ["Time (s)"] + [c for c in df.columns if c != "Time (s)"]
                return df[cols], "XML Format"
        except Exception as e:
            pass # หากแปลงแบบ XML พลาด ให้ข้ามไปลองแบบ Text

    # --- รูปแบบที่ 2: ตรวจสอบว่าเป็นไฟล์ Text / Tab-Separated Values (TSV) ---
    # ค้นหาว่าตารางข้อมูลเริ่มที่บรรทัดไหน โดยหาคำสำคัญ เช่น "Time", "Seconds" หรือ "Ch 1"
    lines = file_text.splitlines()
    data_start_idx = None
    
    for idx, line in enumerate(lines):
        # เช็คหัวตารางข้อมูลส่วนใหญ่ของ Datapaq
        if "time" in line.lower() and ("ch" in line.lower() or "temp" in line.lower()):
            data_start_idx = idx
            break
            
    if data_start_idx is not None:
        # ดึงข้อความตั้งแต่บรรทัดหัวตารางลงไปเพื่อแปลงเป็น DataFrame
        data_body = "\n".join(lines[data_start_idx:])
        df = pd.read_csv(io.StringIO(data_body), sep=None, engine='python') # ค้นหาตัวคั่น (Tab/Comma) อัตโนมัติ
        
        # ปรับชื่อคอลัมน์แรกให้เป็นมาตรฐานคำว่า "Time (s)" เพื่อความง่าย
        df.rename(columns={df.columns[0]: "Time (s)"}, inplace=True)
        return df, "Text/TSV Format"
        
    # --- รูปแบบที่ 3: กรณีที่โครงสร้างไม่ตรงกับเงื่อนไขด้านบนเลย (พยายามอ่านแบบเดาแถว) ---
    try:
        # ข้ามหัวข้อไป 15 บรรทัดแรก (โครงสร้างมาตรฐานส่วนใหญ่)
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=None, skiprows=15, engine='python', error_bad_lines=False)
        df.rename(columns={df.columns[0]: "Time (s)"}, inplace=True)
        return df, "Fallback Text Format (Raw)"
    except:
        return None, "Unknown Format"

# 3. ส่วนแสดงผลบนหน้าเว็บ (UI)
uploaded_file = st.file_uploader("📂 ลากและวางไฟล์ .paq ของคุณที่นี่", type=["paq"])

if uploaded_file is not None:
    with st.spinner("🔄 กำลังวิเคราะห์และแปลงโครงสร้างไฟล์ Datapaq..."):
        df, file_type = process_datapaq(uploaded_file)
        
    if df is not None and not df.empty and df.shape[1] > 1:
        st.success(f"✅ อ่านไฟล์สำเร็จ! ตรวจพบโครงสร้างแบบ: {file_type}")
        
        # แยกคอลัมน์เวลาและเซนเซอร์
        time_col = "Time (s)"
        channels = [col for col in df.columns if col != time_col]
        
        # ตัวเลือกเปิด-ปิด เซนเซอร์บนหน้าเว็บ
        st.sidebar.header("🛠️ ตั้งค่ากราฟ")
        selected_channels = st.sidebar.multiselect(
            "เลือกช่องสัญญาณ (Channels):", 
            options=channels, 
            default=channels[:6] # แสดง 6 แชนเนลแรกเป็นค่าเริ่มต้นก่อนเพื่อไม่ให้กราฟลายตาเกินไป
        )
        
        if selected_channels:
            # แปลงตารางข้อมูลให้เหมาะสมกับการพล็อตกราฟเส้นใน Plotly
            df_melted = df.melt(id_vars=[time_col], value_vars=selected_channels, 
                                var_name="Sensor", value_name="Temperature (°C)")
            
            # สร้างกราฟเส้น Interactive ด้วย Plotly
            fig = px.line(
                df_melted, 
                x=time_col, 
                y="Temperature (°C)", 
                color="Sensor",
                title="📈 Datapaq Temperature Profile",
                labels={time_col: "เวลา (วินาที)", "Temperature (°C)": "อุณหภูมิ (°C)"}
            )
            
            # ตกแต่งกราฟให้สวยงามและส่องข้อมูลได้ง่าย
            fig.update_layout(
                hovermode="x unified", # แสดงอุณหภูมิทุกเซนเซอร์พร้อมกันเมื่อเอาเมาส์ไปชี้ที่เวลาเดียวกัน
                xaxis_title="เวลา (วินาที)",
                yaxis_title="อุณหภูมิ (°C)",
                legend_title="ตำแหน่งเซนเซอร์",
                template="plotly_white"
            )
            
            # แสดงกราฟเส้นขนาดเต็มความกว้างหน้าจอ
            st.plotly_chart(fig, use_container_width=True)
            
            # แสดงตารางข้อมูลดิบเผื่อผู้ใช้ต้องการตรวจสอบหรือกดดาวน์โหลดเป็น Excel/CSV
            with st.expander("👁️ ดูตารางข้อมูลดิบ (Data Table Preview)"):
                st.dataframe(df)
        else:
            st.warning("⚠️ กรุณาติ๊กเลือกช่องสัญญาณ (Channels) ที่แถบเมนูด้านซ้ายอย่างน้อย 1 ช่อง เพื่อแสดงเส้นกราฟ")
    else:
        st.error("❌ ระบบไม่สามารถอ่านโครงสร้างไฟล์นี้ได้ เนื่องจากโครงสร้างตัวเลขภายในไฟล์ไม่ตรงตามรูปแบบมาตรฐาน")
        st.info("💡 วิธีแก้ไข: รบกวนเปิดไฟล์ .paq นี้ในโปรแกรม Notepad จากนั้นก๊อปปี้ข้อความ 20 บรรทัดแรกส่งมาให้ผมในแชทนี้ เพื่อปรับโค้ดให้อ่านไฟล์ของคุณได้ตรงเป๊ะครับ")
