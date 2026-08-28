import streamlit as st
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บของ Streamlit
st.set_page_config(page_title="Datapaq Viewer", layout="wide")
st.title("📈 Datapaq Viewer")

# 2. ข้อมูลจำลองสำหรับแสดงผล (แก้ช่องว่างเดิม ให้มีข้อมูลตัวอย่างที่พร้อมใช้งาน)
x_data = [1, 2, 3, 4, 5]
y_data1 = [10, 15, 13, 17, 22]
y_data2 = [22, 19, 25, 20, 26]

# 3. สร้างกราฟชิ้นที่ 1
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=x_data, y=y_data1, mode='lines+markers', name='Data 1'))
fig1.update_layout(title="Graph 1", xaxis_title="X Axis", yaxis_title="Y Axis")

# 4. สร้างกราฟชิ้นที่ 2 (แก้ไขจุดที่เคยเกิดวงเล็บค้างในบรรทัด 207 ของคุณให้ถูกต้องแล้ว)
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=x_data, 
    y=y_data2, 
    mode='lines+markers', 
    name='Data 2'
))  # ปิดวงเล็บของ go.Scatter และ add_trace ครบถ้วน
fig2.update_layout(title="Graph 2", xaxis_title="X Axis", yaxis_title="Y Axis")

# 5. แสดงผลกราฟบนหน้าเว็บ Streamlit โดยแบ่งเป็น 2 คอลัมน์แบบเต็มหน้าจอ
col1, col2 = st.columns(2)

with col1:
    st.subheader("ส่วนแสดงผลกราฟที่ 1")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("ส่วนแสดงผลกราฟที่ 2")
    st.plotly_chart(fig2, use_container_width=True)
