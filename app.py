import streamlit as st
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Datapaq Profile Viewer", layout="wide")
st.title("📊 Datapaq (.paq) Interactive Graph Viewer")
st.write("อัปโหลดไฟล์ `.paq` เพื่อดู กราฟโปรไฟล์อุณหภูมิแบบ Interactive")

# ฟังก์ชันสำหรับ Parse ไฟล์ .paq (รูปแบบ XML)
def parse_paq_file(uploaded_file):
    # อ่านไฟล์เป็น String
    file_content = uploaded_file.read().decode("utf-8", errors="ignore")
    
    try:
        # แปลงข้อความเป็น XML Tree
        root = ET.fromstring(file_content)
        
        # ค้นหาข้อมูลหมวดหมู่ต่างๆ (โครงสร้างอาจต่างกันเล็กน้อยตามเวอร์ชันของ Datapaq)
        # ตัวอย่างนี้อ้างอิงจากโครงสร้างมาตรฐานที่มีแท็ก <Data> หรือ <DataPoints>
        data_points = []
        
        # ลูปเจาะหาจุดข้อมูล (อันนี้เป็นตัวอย่างโครงสร้างจำลอง คุณอาจต้องปรับให้ตรงกับหัวข้อ XML ในไฟล์จริง)
        # ปกติจะอยู่ภายใต้แท็ก <DataRow> หรือใช้การอ่านแบบบรรทัดหากเป็น Text format
        
        # รีเซ็ต pointer ของไฟล์กลับไปเริ่มต้น
        uploaded_file.seek(0)
        lines = uploaded_file.readlines()
        
        # หมายเหตุ: หากไฟล์ .paq ของคุณเป็นแบบ Tab-Separated Text (มักพบในรุ่นเก่า/ส่งออก) 
        # สามารถใช้ pd.read_csv ได้เลย เช่น:
        # df = pd.read_csv(uploaded_file, sep='\t', skiprows=... )
        
        # วิธีการแบบ Universal สำหรับ .paq ที่เป็น XML/Text ผสม:
        # ค้นหาจุดเริ่มต้นของข้อมูลดิบ ตัวอย่างเช่นคำว่า [Data] หรือ <Data>
        # (แนะนำให้เปิดไฟล์ .paq ด้วย Notepad เพื่อเช็คโครงสร้างที่แน่นอนก่อน)
        
        return None  # คืนค่า DataFrame ที่แปลงเสร็จแล้ว
        
    except Exception as e:
        # หาก Parse XML ไม่สำเร็จ ให้ลองอ่านแบบ Text/CSV (กรณี Datapaq บางรุ่นบันทึกเป็น Text format)
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep='\t', skiprows=10, encoding='utf-8') 
        return df

# ส่วนการอัปโหลดไฟล์
uploaded_file = st.file_uploader("เลือกไฟล์ Datapaq (.paq)", type=["paq"])

if uploaded_file is not None:
    # อ่านและแปลงข้อมูล
    with st.spinner("กำลังประมวลผลไฟล์..."):
        # สำหรับตัวอย่างนี้ สมมติว่าสร้างข้อมูลจำลอง (Mockup) ขึ้นมาแทน เพื่อให้เห็นภาพกราฟที่ได้จาก Datapaq
        # (เนื่องจากโครงสร้าง .paq แต่ละเวอร์ชันจะต่างกันเล็กน้อย)
        
        # --- เริ่มช่วงโค้ดจำลองข้อมูล (ให้เปลี่ยนเป็นฟังก์ชันอ่านไฟล์จริงของคุณ) ---
        import numpy as np
        time_seq = np.arange(0, 600, 2)  # 0 ถึง 10 นาที (เก็บทุก 2 วินาที)
        mock_data = {
            "Time (s)": time_seq,
            "Ch 1 (Air)": 25 + 150 / (1 + np.exp(-(time_seq-150)/50)),
            "Ch 2 (Product Top)": 25 + 145 / (1 + np.exp(-(time_seq-180)/60)),
            "Ch 3 (Product Base)": 25 + 140 / (1 + np.exp(-(time_seq-210)/70)),
        }
        df = pd.DataFrame(mock_data)
        # --- จบช่วงโค้ดจำลองข้อมูล ---

    st.success("โหลดข้อมูลสำเร็จ!")

    # แสดงข้อมูลดิบบางส่วน
    with st.expander("ดูข้อมูลดิบ (Data Preview)"):
        st.dataframe(df.head(100))

    # ตัวเลือกในการคัดเลือก Channels ที่ต้องการพล็อตกราฟ
    channels = [col for col in df.columns if col != "Time (s)"]
    selected_channels = st.multiselect("เลือกช่องสัญญาณ (Channels) ที่ต้องการแสดง:", channels, default=channels)

    if selected_channels:
        # แปลงข้อมูลให้อยู่ในรูปแบบ Long Format สำหรับ Plotly
        df_melted = df.melt(id_vars=["Time (s)"], value_vars=selected_channels, 
                            var_name="Sensor Channel", value_name="Temperature (°C)")

        # สร้าง Interactive Graph ด้วย Plotly
        fig = px.line(
            df_melted, 
            x="Time (s)", 
            y="Temperature (°C)", 
            color="Sensor Channel",
            title="Datapaq Temperature Profile",
            labels={"Time (s)": "Time (Seconds)", "Temperature (°C)": "Temperature (°C)"}
        )

        # ปรับแต่งหน้าตากราฟเพิ่มเติม (เช่น เพิ่มเส้น Grid, เปิด Tooltip)
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="เวลา (วินาที)",
            yaxis_title="อุณหภูมิ (°C)",
            legend_title="เซนเซอร์"
        )

        # แสดงกราฟบน Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("กรุณาเลือกอย่างน้อย 1 ช่องสัญญาณเพื่อแสดงกราฟ")

