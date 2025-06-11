import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Water Pollution Dashboard", layout="wide")
st.title("💧 Dashboard Kualitas Air Sungai di China")

st.markdown("Selamat datang di dashboard interaktif untuk menganalisis kualitas air sungai di China. Gunakan sidebar di kiri untuk navigasi antar visualisasi.")

# Baca CSV dari folder
DATA_FOLDER = "data"
CSV_FILE = "china_water_pollution_data.csv"
csv_path = os.path.join(DATA_FOLDER, CSV_FILE)

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)

    # ✅ DATA WRANGLING
    df = df.drop_duplicates()
    df = df.fillna(method='ffill')  # atau pilih metode sesuai kebutuhan
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.dropna(subset=['Date'], inplace=True)
    df = df.rename(columns={"Latitude": "latitude", "Longitude": "longitude"})

    # ✅ RINGKASAN DATA
    st.header("📄 Ringkasan Data")
    st.subheader("Informasi Umum Data")
    st.dataframe(df)

    st.write(f"Jumlah baris: {df.shape[0]}")
    st.write(f"Jumlah kolom: {df.shape[1]}")

    # Cek missing values
    st.subheader("Missing Values")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        st.success("Tidak ada missing values!")
    else:
        st.dataframe(missing)

    st.markdown("---")

    # Sidebar Filter
    st.sidebar.header("🔎 Filter Data")
    date_range = st.sidebar.date_input(
        "Pilih rentang tanggal",
        [df['Date'].min(), df['Date'].max()]
    )

    station_options = df['Monitoring_Station'].unique()
    selected_stations = st.sidebar.multiselect(
        "Pilih Monitoring Station (max 6)",
        station_options,
        default=station_options[:6]
    )

    if len(selected_stations) > 6:
        st.sidebar.warning("Maksimal 6 station ditampilkan. Dipotong otomatis.")
        selected_stations = selected_stations[:6]

    filtered_df = df[
        (df['Date'] >= pd.to_datetime(date_range[0])) &
        (df['Date'] <= pd.to_datetime(date_range[1])) &
        (df['Monitoring_Station'].isin(selected_stations))
    ]

    # ✅ EDA
    st.header("📊 Statistik Data Filter")
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Data", len(filtered_df))
    col2.metric("Station Aktif", filtered_df['Monitoring_Station'].nunique())
    col3.metric("Rata-rata Suhu", f"{filtered_df['Water_Temperature_C'].mean():.2f}°C")

    st.markdown("---")

    grouped = filtered_df.groupby(['Date', 'Monitoring_Station']).mean(numeric_only=True).reset_index()

    # ✅ VISUALISASI

    st.subheader("🌡️ Rata-rata Suhu Air")
    fig_temp = px.line(
        grouped, x='Date', y='Water_Temperature_C',
        color='Monitoring_Station',
        title="Water Temperature (°C) Over Time",
        markers=True
    )
    fig_temp.update_layout(template="plotly_dark")
    st.plotly_chart(fig_temp, use_container_width=True)

    if 'Dissolved_Oxygen_mg_L' in grouped.columns:
        st.subheader("🫧 Oksigen Terlarut (Dissolved Oxygen)")
        fig_do = px.line(
            grouped, x='Date', y='Dissolved_Oxygen_mg_L',
            color='Monitoring_Station',
            title="Dissolved Oxygen (mg/L)"
        )
        fig_do.update_layout(template="plotly_dark")
        st.plotly_chart(fig_do, use_container_width=True)

    if 'Turbidity_NTU' in grouped.columns:
        st.subheader("🌫️ Turbidity (NTU)")
        fig_turb = px.line(
            grouped, x='Date', y='Turbidity_NTU',
            color='Monitoring_Station',
            title="Turbidity (NTU)"
        )
        fig_turb.update_layout(template="plotly_dark")
        st.plotly_chart(fig_turb, use_container_width=True)

    if 'Nitrate_mg_L' in grouped.columns:
        st.subheader("💧 Nitrate (mg/L)")
        fig_nit = px.line(
            grouped, x='Date', y='Nitrate_mg_L',
            color='Monitoring_Station',
            title="Nitrate Level Over Time"
        )
        fig_nit.update_layout(template="plotly_dark")
        st.plotly_chart(fig_nit, use_container_width=True)

    st.subheader("📊 Statistik Per Provinsi")
    stat_cols = ['Water_Temperature_C', 'pH', 'Dissolved_Oxygen_mg_L']
    if all(col in df.columns for col in stat_cols):
        prov_stats = df.groupby('Province')[stat_cols].mean().round(2).reset_index()
        st.dataframe(prov_stats)

    st.subheader("📊 Top 5 Station dengan Rata-rata Suhu Tertinggi (Bar Chart)")
    avg_temp_per_station = filtered_df.groupby('Monitoring_Station')['Water_Temperature_C'].mean().sort_values(ascending=False)
    top5_station = avg_temp_per_station.head(5).reset_index()

    fig_bar = px.bar(
        top5_station,
        x='Water_Temperature_C',
        y='Monitoring_Station',
        orientation='h',
        title="Top 5 Station dengan Rata-rata Suhu Air Tertinggi (°C)",
        text='Water_Temperature_C'
    )
    fig_bar.update_layout(template='plotly_dark', height=600)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 Komposisi Rata-rata Parameter Air (Pie Chart)")
    pie_data = {
        'Water_Temperature_C': filtered_df['Water_Temperature_C'].mean(),
        'Dissolved_Oxygen_mg_L': filtered_df['Dissolved_Oxygen_mg_L'].mean() if 'Dissolved_Oxygen_mg_L' in filtered_df else 0,
        'Turbidity_NTU': filtered_df['Turbidity_NTU'].mean() if 'Turbidity_NTU' in filtered_df else 0,
        'Nitrate_mg_L': filtered_df['Nitrate_mg_L'].mean() if 'Nitrate_mg_L' in filtered_df else 0
    }

    pie_df = pd.DataFrame(list(pie_data.items()), columns=['Parameter', 'Rata-rata'])
    fig_pie = px.pie(pie_df, names='Parameter', values='Rata-rata', title="Komposisi Rata-rata Parameter Air")
    fig_pie.update_layout(template='plotly_dark')
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("🗺️ Lokasi Monitoring Station (Peta)")
    st.map(filtered_df[['latitude', 'longitude']].dropna())

    st.subheader("📤 Download Data Hasil Filter")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "💾 Download CSV",
        data=csv,
        file_name="filtered_water_pollution.csv",
        mime='text/csv'
    )

else:
    st.error(f"File '{CSV_FILE}' tidak ditemukan di folder '{DATA_FOLDER}'. Pastikan file ada di sana.")
