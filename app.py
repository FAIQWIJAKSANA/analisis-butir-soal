import streamlit as st
import pandas as pd
import numpy as np
import io

# Mengatur tampilan halaman web
st.set_page_config(page_title="Analisis Soal Pro", layout="wide")

st.title("📊 Sistem Analisis Butir Soal (Lengkap)")
st.write("Menganalisis Validitas, Reliabilitas, Daya Pembeda, dan Tingkat Kesukaran.")
st.markdown("---")

# ==========================================
# FITUR: DOWNLOAD TEMPLATE EXCEL
# ==========================================
st.subheader("📥 Belum punya file? Download Template di Sini")
st.write("Klik tombol di bawah ini untuk mendapatkan file Excel contoh yang siap pakai.")

data_template = {
    'Nama_Siswa': ['Ahmad', 'Budi', 'Cici', 'Dedi', 'Eka', 'Fani', 'Gani', 'Hana', 'Iwan', 'Joko', 'Kiki', 'Lani', 'Maman', 'Nia', 'Oman'],
    'Soal_1': [1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1],
    'Soal_2': [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0],
    'Soal_3': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1],
    'Soal_4': [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1],
    'Soal_5': [1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1],
    'Soal_6': [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1],
    'Soal_7': [1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1],
    'Soal_8': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Soal_9': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    'Soal_10': [1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0]
}
df_template = pd.DataFrame(data_template)

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False, sheet_name='Data_Ujian')
buffer.seek(0)

st.download_button(
    label="📄 Download File Excel Contoh (.xlsx)",
    data=buffer,
    file_name="template_analisis_soal.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")

# ==========================================
# 1. BAGIAN UPLOAD DATA (Perbaikan Parsing)
# ==========================================
st.subheader("📤 Upload File yang Akan Dianalisis")
uploaded_file = st.file_uploader("Upload file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            # Memastikan jika csv dipisahkan koma/titik koma tetap terbaca rapi
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
        st.success("File berhasil diunggah!")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        df = df_template
else:
    st.info("💡 Menampilkan data uji coba (Dummy Data). Silakan download template di atas lalu upload kembali di sini.")
    df = df_template

with st.expander("Klik untuk melihat Data Jawaban Mentah"):
    st.dataframe(df, use_container_width=True)

# ==========================================
# 2. PROSES PERHITUNGAN LOGIKA (Safe Mode)
# ==========================================
try:
    # Memisahkan kolom nama dengan kolom skor angka soal
    df_soal = df.drop(df.columns[0], axis=1).apply(pd.to_numeric, errors='coerce').fillna(0)
    skor_total = df_soal.sum(axis=1)

    # A. Tingkat Kesukaran
    tingkat_kesukaran = df_soal.mean()

    # B. Daya Pembeda
    df_sorted = df_soal.assign(Total=skor_total).sort_values(by='Total', ascending=False)
    n_kelompok = max(1, len(df_sorted) // 2) 
    kelompok_atas = df_sorted.iloc[:n_kelompok].drop(columns=['Total'])
    kelompok_bawah = df_sorted.iloc[-n_kelompok:].drop(columns=['Total'])
    daya_pembeda = kelompok_atas.mean() - kelompok_bawah.mean()

    # C. Validitas
    validitas = df_soal.apply(lambda x: x.corr(skor_total)).fillna(0)

    # D. Reliabilitas (KR-20)
    k = len(df_soal.columns) 
    pq = tingkat_kesukaran * (1 - tingkat_kesukaran)
    varians_total = skor_total.var(ddof=0)
    
    if varians_total == 0 or k <= 1:
        reliabilitas = 0
    else:
        reliabilitas = (k / (k - 1)) * (1 - (pq.sum() / varians_total))

    # ==========================================
    # 3. FUNGSI UNTUK MEMBERIKAN KRITERIA
    # ==========================================
    def kriteria_kesukaran(nilai):
        if nilai < 0.30: return "Sulit"
        elif nilai <= 0.70: return "Sedang"
        else: return "Mudah"

    def kriteria_pembeda(nilai):
        if nilai <= 0: return "Revisi Total / Buang"
        elif nilai < 0.20: return "Buruk"
        elif nilai < 0.40: return "Cukup"
        elif nilai < 0.70: return "Baik"
        else: return "Sangat Baik"

    def kriteria_validitas(nilai):
        if nilai > 0.30: return "Valid ✅"
        else: return "Tidak Valid ❌"

    # Membuat tabel hasil akhir
    hasil_akhir = pd.DataFrame({
        'Validitas (r)': validitas.round(3),
        'Status Validitas': validitas.apply(kriteria_validitas),
        'Daya Pembeda': daya_pembeda.round(3),
        'Kriteria Pembeda': daya_pembeda.apply(kriteria_pembeda),
        'Tk. Kesukaran': tingkat_kesukaran.round(3),
        'Kriteria Kesukaran': tingkat_kesukaran.apply(kriteria_kesukaran)
    })

    # ==========================================
    # 4. TAMPILAN HASIL DI WEBSITE
    # ==========================================
    st.markdown("---")
    st.write("### 📈 Hasil Analisis Keseluruhan")

    status_reliabilitas = "Reliabel (Bisa Diandalkan)" if reliabilitas > 0.70 else "Tidak Reliabel"
    st.metric(label="Reliabilitas Tes (KR-20)", value=f"{reliabilitas:.3f}", delta=status_reliabilitas)

    st.write("### 🔍 Rincian Analisis Per Butir Soal")
    st.dataframe(hasil_akhir, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Validitas", "Daya Pembeda", "Tingkat Kesukaran"])

    with tab1:
        st.subheader("Uji Validitas")
        st.dataframe(hasil_akhir[['Validitas (r)', 'Status Validitas']], use_container_width=True)

    with tab2:
        st.subheader("Uji Daya Pembeda")
        st.dataframe(hasil_akhir[['Daya Pembeda', 'Kriteria Pembeda']], use_container_width=True)

    with tab3:
        st.subheader("Uji Tingkat Kesukaran")
        st.dataframe(hasil_akhir[['Tk. Kesukaran', 'Kriteria Kesukaran']], use_container_width=True)

except Exception as e:
    st.error(f"Terjadi kesalahan perhitungan struktur data. Pastikan format kolom file sesuai. Detail: {e}")