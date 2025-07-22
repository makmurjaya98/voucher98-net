
import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="Voucher MJ98-NET", layout="wide")
st.title("📊 Aplikasi Penjualan Voucher MJ98-NET")

# ----------------------------
# LOGIN SECTION
# ----------------------------
USERS = {
    "admin1": "password1",
    "admin2": "password2"
}

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
# FILE UPLOAD SECTION
# ----------------------------
st.header("📥 Upload File Excel")
stok_file = st.file_uploader("Upload file stok awal", type=["xlsx"], key="stok")
penjualan_file = st.file_uploader("Upload file penjualan voucher", type=["xlsx"], key="penjualan")

# ----------------------------
# FORM TAMBAH DATA
# ----------------------------
st.sidebar.header("➕ Tambah Data")

# Tambah Cabang / Link Baru
with st.sidebar.expander("Tambah Cabang / Link"):
    jenis = st.radio("Pilih jenis", ["Cabang", "Link"], horizontal=True)
    nama_baru = st.text_input("Nama baru")
    if st.button("Simpan Nama"):
        st.success(f"{jenis} '{nama_baru}' berhasil ditambahkan (simulasi)")  # Simulasi

# Tambah Stok Manual
with st.sidebar.expander("Tambah Stok Voucher"):
    cabang_link = st.text_input("Nama Cabang/Link")
    jenis_voucher = st.selectbox("Jenis Voucher", [
        "Voucher 2 Jam", "Voucher 5 Jam", "Voucher 11 Jam", "Voucher 15 Jam", "Voucher 30 Hari"
    ])
    jumlah = st.number_input("Jumlah Voucher", min_value=1, step=1)
    if st.button("Tambah Stok"):
        waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state['log_stok_manual'] = st.session_state.get('log_stok_manual', []) + [{
            "Waktu": waktu,
            "Cabang/Link": cabang_link,
            "Jenis Voucher": jenis_voucher,
            "Jumlah Ditambahkan": jumlah,
            "Admin": username
        }]
        st.success("Stok berhasil ditambahkan (simulasi)")

# ----------------------------
# PROSES FILE
# ----------------------------
if stok_file and penjualan_file:
    stok_df = pd.read_excel(stok_file)
    df = pd.read_excel(penjualan_file)

    if not pd.api.types.is_datetime64_any_dtype(df['Tanggal']):
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])

    df['Pendapatan Link'] = df['Link'].notna() * df['Harga Jual']
    df['Pendapatan Cabang'] = df['Cabang'].notna() * df['Harga Jual']
    df['Pendapatan Cabang dari Link'] = df['Link'].notna() * df['Harga Jual']

    df['Fee Link'] = df['Link'].notna() * (df['Modal'] * 0.05)
    df['Fee Cabang'] = df['Cabang'].notna() * (df['Modal'] * 0.10)
    df['Komisi Mitra-Cbg'] = df['Modal'] * 0.05

    df['Tanggal'] = df['Tanggal'].dt.date

    st.subheader("📄 Tabel Data Penjualan")
    st.dataframe(df)

    # Update Stok Real-time
    stok_df = stok_df.copy()
    stok_df['Terjual'] = stok_df['Jenis Voucher'].map(df['Jenis Voucher'].value_counts()).fillna(0).astype(int)
    stok_df['Sisa Stok'] = stok_df['Stok'] - stok_df['Terjual']

    # Tambahkan stok manual (simulasi)
    if 'log_stok_manual' in st.session_state:
        tambahan = pd.DataFrame(st.session_state['log_stok_manual'])
        st.subheader("📜 Log Tambahan Stok Manual")
        st.dataframe(tambahan)
    else:
        tambahan = pd.DataFrame(columns=["Waktu", "Cabang/Link", "Jenis Voucher", "Jumlah Ditambahkan", "Admin"])

    st.subheader("📦 Stok Real-time")
    st.dataframe(stok_df[['Jenis Voucher', 'Stok', 'Terjual', 'Sisa Stok']])

    # Rekap Penjualan
    total_pendapatan = df['Harga Jual'].sum()
    total_modal = df['Modal'].sum()
    total_laba = total_pendapatan - total_modal
    total_voucher_terjual = len(df)

    st.subheader("📈 Ringkasan Total")
    st.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    st.metric("Total Modal", f"Rp {total_modal:,.0f}")
    st.metric("Total Laba Bersih", f"Rp {total_laba:,.0f}")
    st.metric("Total Voucher Terjual", total_voucher_terjual)

    # Laporan per Hari, 10 Hari, Bulan
    df['10Hari'] = df['Tanggal'].apply(lambda d: (d - datetime.date(2025, 1, 1)).days // 10)
    df['Bulan'] = pd.to_datetime(df['Tanggal']).dt.to_period('M')

    st.subheader("📆 Laporan Penjualan per Hari")
    st.dataframe(df.groupby('Tanggal').agg({
        'Harga Jual': 'sum', 'Modal': 'sum', 'Fee Link': 'sum',
        'Fee Cabang': 'sum', 'Komisi Mitra-Cbg': 'sum'
    }).reset_index())

    st.subheader("🗓️ Laporan Penjualan per 10 Hari")
    st.dataframe(df.groupby('10Hari').agg({
        'Harga Jual': 'sum', 'Modal': 'sum', 'Fee Link': 'sum',
        'Fee Cabang': 'sum', 'Komisi Mitra-Cbg': 'sum'
    }).reset_index())

    st.subheader("📅 Laporan Penjualan per Bulan")
    st.dataframe(df.groupby('Bulan').agg({
        'Harga Jual': 'sum', 'Modal': 'sum', 'Fee Link': 'sum',
        'Fee Cabang': 'sum', 'Komisi Mitra-Cbg': 'sum'
    }).reset_index())

    # Export to Excel
    st.subheader("📤 Export Rekapan ke Excel")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Penjualan')
        stok_df.to_excel(writer, index=False, sheet_name='Stok Real-time')
        tambahan.to_excel(writer, index=False, sheet_name='Log Tambah Manual')

    st.download_button(
        label="📥 Download Rekap Excel",
        data=output.getvalue(),
        file_name="rekapan_voucher_mj98_net.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload file stok awal dan penjualan terlebih dahulu.")
