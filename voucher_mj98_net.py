import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

# ----------------------------
# LOGIN SECTION
# ----------------------------
USERS = {
    "admin1": "password1",
    "admin2": "password2"
}

st.set_page_config(page_title="Voucher MJ98-NET", layout="wide")
st.title("📊 Aplikasi Penjualan Voucher MJ98-NET")

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if USERS.get(username) == password:
            st.session_state.authenticated = True
            st.success("Login berhasil!")
        else:
            st.error("Username atau password salah")
    st.stop()

# ----------------------------
# FILE UPLOAD
# ----------------------------
uploaded_file = st.file_uploader("Upload file Excel hasil penjualan voucher MJ98-NET", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Pastikan kolom tanggal dalam format datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Tanggal']):
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])

    df['Pendapatan Link'] = df['Link'].notna() * df['Harga Jual']
    df['Pendapatan Cabang'] = df['Cabang'].notna() * df['Harga Jual']
    df['Pendapatan Cabang dari Link'] = df['Link'].notna() * df['Harga Jual']

    df['Fee Link'] = df['Link'].notna() * (df['Modal'] * 0.05)
    df['Fee Cabang'] = df['Cabang'].notna() * (df['Modal'] * 0.10)
    df['Komisi Mitra-Cbg'] = df['Modal'] * 0.05

    df['Tanggal'] = df['Tanggal'].dt.date

    st.subheader("Tabel Data Asli")
    st.dataframe(df)

    # ----------------------------
    # REKAP TOTAL
    # ----------------------------
    total_pendapatan = df['Harga Jual'].sum()
    total_modal = df['Modal'].sum()
    total_laba = total_pendapatan - total_modal
    total_voucher_terjual = len(df)

    st.subheader("Ringkasan Total")
    st.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    st.metric("Total Modal", f"Rp {total_modal:,.0f}")
    st.metric("Total Laba Bersih", f"Rp {total_laba:,.0f}")
    st.metric("Total Voucher Terjual", total_voucher_terjual)

    # ----------------------------
    # LAPORAN PER HARI, 10 HARI, BULAN
    # ----------------------------
    st.subheader("📆 Laporan Penjualan per Hari")
    per_hari = df.groupby('Tanggal').agg({
        'Harga Jual': 'sum',
        'Modal': 'sum',
        'Fee Link': 'sum',
        'Fee Cabang': 'sum',
        'Komisi Mitra-Cbg': 'sum'
    }).reset_index()
    st.dataframe(per_hari)

    st.subheader("🗓️ Laporan Penjualan per 10 Hari")
    df['10Hari'] = df['Tanggal'].apply(lambda d: (d - datetime.date(2025, 1, 1)).days // 10)
    per_10_hari = df.groupby('10Hari').agg({
        'Harga Jual': 'sum',
        'Modal': 'sum',
        'Fee Link': 'sum',
        'Fee Cabang': 'sum',
        'Komisi Mitra-Cbg': 'sum'
    }).reset_index()
    st.dataframe(per_10_hari)

    st.subheader("📅 Laporan Penjualan per Bulan")
    df['Bulan'] = pd.to_datetime(df['Tanggal']).dt.to_period('M')
    per_bulan = df.groupby('Bulan').agg({
        'Harga Jual': 'sum',
        'Modal': 'sum',
        'Fee Link': 'sum',
        'Fee Cabang': 'sum',
        'Komisi Mitra-Cbg': 'sum'
    }).reset_index()
    st.dataframe(per_bulan)

    # ----------------------------
    # EXPORT TO EXCEL
    # ----------------------------
    st.subheader("📤 Export Rekapan ke Excel")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Penjualan')
        per_hari.to_excel(writer, index=False, sheet_name='Per Hari')
        per_10_hari.to_excel(writer, index=False, sheet_name='Per 10 Hari')
        per_bulan.to_excel(writer, index=False, sheet_name='Per Bulan')

    st.download_button(
        label="📥 Download Rekap Excel",
        data=output.getvalue(),
        file_name="rekapan_voucher_mj98_net.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload file Excel terlebih dahulu.")
