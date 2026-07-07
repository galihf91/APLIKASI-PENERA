import streamlit as st
import pandas as pd
from datetime import datetime
from modules.timbangan_jembatan.cerapan_tj_generator import generate_cerapan_pdf
from modules.timbangan_jembatan.sertifikat_tj_generator import generate_sertifikat_pdf
import os
from pathlib import Path

def bulan_ke_romawi(bulan):
    romawi = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    return romawi[bulan-1]

def generate_nomor_sertifikat(tanggal):
    if isinstance(tanggal, str):
        t = datetime.strptime(tanggal, '%Y-%m-%d')
    else:
        t = tanggal
    return f"500.2.3.15/0000/BID-K/{bulan_ke_romawi(t.month)}/{t.year}"

def generate_nomor_order(tanggal):
    if isinstance(tanggal, str):
        t = datetime.strptime(tanggal, '%Y-%m-%d')
    else:
        t = tanggal
    return f"0000/SCD/{bulan_ke_romawi(t.month)}/{t.year}"

# ===== BACA DATA PERUSAHAAN =====
def format_tanggal_indonesia(tanggal_str):
    """Mengubah format YYYY-MM-DD menjadi 'DD Month YYYY' (contoh: 8 Juni 2026)"""
    if not tanggal_str:
        return ""
    try:
        if isinstance(tanggal_str, str):
            t = datetime.strptime(tanggal_str, '%Y-%m-%d')
        else:
            t = tanggal_str
        bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        return f"{t.day} {bulan[t.month-1]} {t.year}"
    except:
        return tanggal_str

def load_data_perusahaan():
    """Membaca data perusahaan dari Excel atau fallback ke data kosong."""
    possible_names = ["data/data_perusahaan.xlsx"]
    for filename in possible_names:
        if os.path.exists(filename):
            try:
                df = pd.read_excel(filename, engine='openpyxl')
                required_cols = ['Nama Perusahaan', 'Alamat']
                if all(col in df.columns for col in required_cols):
                    # Hapus duplikat dan NaN
                    df = df.dropna(subset=['Nama Perusahaan'])
                    df = df.drop_duplicates(subset=['Nama Perusahaan'])
                    return df
                else:
                    st.warning(f"File {filename} ditemukan, tetapi kolom tidak sesuai. Harus ada: Nama Perusahaan, Alamat")
                    return None
            except Exception as e:
                st.warning(f"Error membaca {filename}: {e}. Gunakan data bawaan.")
                break
    # Fallback: data kosong (atau bisa beri contoh)
    return pd.DataFrame(columns=['Nama Perusahaan', 'Alamat'])

if 'data_perusahaan' not in st.session_state:
    st.session_state.data_perusahaan = load_data_perusahaan()
def load_data_penera():
    """Membaca file data penera dari Excel dengan pengecekan lokasi."""
    possible_names = ["data/data_penera.xlsx"]
    
    # Tampilkan file yang ada di direktori (debug)
    # st.write("File di direktori:", os.listdir())
    
    for filename in possible_names:
        if os.path.exists(filename):
            try:
                df = pd.read_excel(filename, engine='openpyxl')
                required_cols = ['Nama', 'NIP', 'Golongan']
                if all(col in df.columns for col in required_cols):
                    return df
                else:
                    st.warning(f"File {filename} ditemukan, tetapi kolom tidak sesuai. Harus ada: {required_cols}")
                    return None
            except Exception as e:
                st.error(f"Error membaca {filename}: {e}")
                return None
    st.warning("File data_penera.xlsx tidak ditemukan. Silakan input manual.")
    return None

if 'data_penera' not in st.session_state:
    st.session_state.data_penera = load_data_penera()
def copy_standar():
    """Salin nilai standar baris ke-2 (indeks 1) ke baris 4, 6, 8 (indeks 3,5,7)."""
    e = st.session_state.get('interval_skala_input', 20)
    key_src = f"standar_1_{e}"
    if key_src in st.session_state:
        val = st.session_state[key_src]
        st.session_state[f"standar_3_{e}"] = val
        st.session_state[f"standar_5_{e}"] = val
        st.session_state[f"standar_7_{e}"] = val

def sync_balas(prev_key, next_key):
    """Salin nilai dari prev_key ke next_key di session state."""
    if prev_key in st.session_state:
        st.session_state[next_key] = st.session_state[prev_key]
def hitung_bkd(muatan, interval_skala, kelas, keterangan):
    if interval_skala == 0:
        return 0, 0

    m = muatan / interval_skala

    # Tabel 4.7: BKD dasar untuk Kelas III
    batas = {
        'I'   : [(50000, 0.5), (200000, 1.0), (float('inf'), 1.5)],
        'II'  : [(5000,  0.5), (20000,  1.0), (100000, 1.5)],
        'III' : [(500,   0.5), (2000,   1.0), (10000,  1.5)],
        'IIII': [(50,    0.5), (200,    1.0), (1000,   1.5)],
    }

    koef_dasar = 1.5
    for batas_m, koef in batas.get(kelas, batas['III']):
        if m <= batas_m:
            koef_dasar = koef
            break

    # Tabel 4.8: Multiplier untuk Tera Ulang
    multiplier = 2.0 if keterangan == "Tera Ulang" else 1.0

    koef_final = koef_dasar * multiplier
    bkd_kg     = koef_final * interval_skala

    return koef_final, bkd_kg

# Konfigurasi halaman
st.set_page_config(
    page_title="Aplikasi Automasi Sertifikat Tera",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== INISIALISASI SESSION STATE =====
if 'saved_data' not in st.session_state:
    st.session_state.saved_data = {}

if 'test_results' not in st.session_state:
    st.session_state.test_results = []

# Nilai default untuk input utama (diambil dari saved_data jika ada)
if 'kapasitas_max_input' not in st.session_state:
    st.session_state.kapasitas_max_input = st.session_state.saved_data.get('kapasitas_max', 60000)

if 'daya_baca_input' not in st.session_state:
    st.session_state.daya_baca_input = st.session_state.saved_data.get('daya_baca', 10)

if 'interval_skala_input' not in st.session_state:
    st.session_state.interval_skala_input = st.session_state.daya_baca_input

if 'kelas' not in st.session_state:
    st.session_state.kelas = st.session_state.saved_data.get('kelas', 'III')

if 'keterangan' not in st.session_state:
    st.session_state.keterangan = st.session_state.saved_data.get('keterangan', 'Tera')
    
if 'generated_files' not in st.session_state:
    st.session_state.generated_files = {}
    
# CSS styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("⚖️ Aplikasi Automasi Sertifikat Tera Timbangan")
st.markdown("---")

# Sidebar - Navigation
with st.sidebar:
    st.header("📋 Menu Navigasi")
    mode = st.radio(
        "Pilih Mode:",
        ["📝 Input Data Pengujian", "📄 Generate Dokumen"],
        help="Pilih mode yang ingin Anda gunakan"
    )

if mode == "📝 Input Data Pengujian":
    st.header("Masukkan Data Pengujian")

    # Ambil nilai dari session state untuk digunakan di seluruh blok
    e = st.session_state.get('interval_skala_input', 20)
    cls = st.session_state.get('kelas', 'III')
    jns_uji = st.session_state.get('keterangan', 'Tera')

    # ======================== KOLOM 1-3 ========================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Identitas Pemilik")
        
        df_perusahaan = st.session_state.get('data_perusahaan')
        
        # Inisialisasi session state untuk nama dan alamat
        if 'nama_perusahaan' not in st.session_state:
            st.session_state.nama_perusahaan = st.session_state.saved_data.get('pemilik', '')
        if 'alamat_perusahaan' not in st.session_state:
            st.session_state.alamat_perusahaan = st.session_state.saved_data.get('alamat', '')
        if 'alamat_edit' not in st.session_state:
            st.session_state.alamat_edit = st.session_state.alamat_perusahaan
        if 'last_company' not in st.session_state:
            st.session_state.last_company = None
        
        if df_perusahaan is not None and not df_perusahaan.empty:
            all_names = df_perusahaan['Nama Perusahaan'].tolist()
            selected = st.selectbox(
                "Cari & Pilih Nama Perusahaan",
                options=[""] + all_names,
                index=0,
                placeholder="Ketik nama perusahaan...",
                key="perusahaan_select"
            )
            
            if selected:
                # Hanya set alamat jika pilihan perusahaan berubah
                if selected != st.session_state.last_company:
                    row = df_perusahaan[df_perusahaan['Nama Perusahaan'] == selected].iloc[0]
                    st.session_state.nama_perusahaan = selected
                    st.session_state.alamat_perusahaan = row['Alamat']
                    st.session_state.alamat_edit = row['Alamat']
                    st.session_state.last_company = selected
                else:
                    # Pilihan sama, tidak timpa alamat (jaga edit manual)
                    pass
            else:
                # Jika tidak ada pilihan, reset last_company
                st.session_state.last_company = None
                # Namun jangan hapus alamat yang sudah diisi manual
                # Biarkan alamat tetap seperti apa adanya
            
            # Text area alamat (dapat diedit)
            alamat = st.text_area(
                "Alamat (dapat diubah jika diperlukan)",
                value=st.session_state.alamat_edit,
                height=80,
                key="alamat_edit"
            )
            # Update alamat_perusahaan sesuai input user (text area sudah otomatis update session_state via key)
            st.session_state.alamat_perusahaan = st.session_state.alamat_edit
            
            # Opsi input manual untuk nama
            if st.checkbox("Input manual nama perusahaan"):
                manual_nama = st.text_input(
                    "Nama Pemilik/Perusahaan (manual)",
                    value=st.session_state.nama_perusahaan
                )
                if manual_nama:
                    st.session_state.nama_perusahaan = manual_nama
        else:
            # Jika file tidak ditemukan
            st.info("📂 File data perusahaan tidak ditemukan. Silakan input manual.")
            manual_nama = st.text_input(
                "Nama Pemilik/Perusahaan",
                value=st.session_state.nama_perusahaan
            )
            manual_alamat = st.text_area(
                "Alamat",
                value=st.session_state.alamat_perusahaan,
                height=80
            )
            st.session_state.nama_perusahaan = manual_nama
            st.session_state.alamat_perusahaan = manual_alamat
            st.session_state.alamat_edit = manual_alamat
        
        # Ambil nilai dari session state untuk digunakan di submit
        pemilik = st.session_state.get('nama_perusahaan', '')
        alamat = st.session_state.get('alamat_perusahaan', '')

    with col2:
        st.subheader("Spesifikasi Alat")
        merek = st.text_input("Merek/Buatan",
                              value=st.session_state.saved_data.get('merek', ''),
                              placeholder="")
        model = st.text_input("Model/Tipe",
                              value=st.session_state.saved_data.get('model', ''),
                              placeholder="")
        no_seri = st.text_input("No. Seri",
                                value=st.session_state.saved_data.get('no_seri', ''),
                                placeholder="")

    with col3:
        st.subheader("Kapasitas & Skala")

        # Kapasitas Maksimum
        st.number_input(
            "Kapasitas Maksimum (kg)",
            value=st.session_state.kapasitas_max_input,
            min_value=100,
            step=100,
            key="kapasitas_max_input"
        )

        # Daya Baca
        st.number_input(
            "Daya Baca (kg)",
            value=st.session_state.daya_baca_input,
            min_value=1,
            step=1,
            key="daya_baca_input"
        )

        # Sinkronkan Interval Skala dengan Daya Baca
        st.session_state.interval_skala_input = st.session_state.daya_baca_input

        # Interval Skala Verifikasi (disabled)
        st.number_input(
            "Interval Skala Verifikasi (kg)",
            value=st.session_state.interval_skala_input,
            min_value=1,
            step=1,
            disabled=True,
            key="interval_skala_input",
            help="Interval Skala Verifikasi (e) otomatis mengikuti Daya Baca (d)."
        )

        # Kapasitas Minimum = 20 × interval_skala (dengan key dinamis)
        current_e = st.session_state.interval_skala_input
        st.number_input(
            "Kapasitas Minimum (kg)",
            value=20 * current_e,
            min_value=1,
            step=1,
            disabled=True,
            key=f"kapasitas_min_{current_e}",   # 🔥 key dinamis
            help="Nilai ini otomatis = 20 × Interval Skala Verifikasi, namun dapat diubah."
        )
    st.markdown("---")

    # ======================== KELAS & JENIS PENGUJIAN ========================
    col_extra1, col_extra2, col_extra3 = st.columns(3)
    with col_extra1:
        st.text_input(
            "Kelas Timbangan",
            value="III",
            disabled=True
        )
        st.session_state.kelas = "III"

    with col_extra2:
        default_keterangan = st.session_state.saved_data.get("keterangan", "Tera Ulang")

        keterangan = st.selectbox(
            "Jenis Pengujian",
            ["Tera", "Tera Ulang"],
            index=0 if default_keterangan == "Tera" else 1
        )

        st.session_state.keterangan = keterangan

    with col_extra3:
        # kosong atau bisa untuk informasi tambahan
        st.write("")

    st.markdown("---")

    # ======================== DATA PENGUJIAN LAINNYA ========================
    col4, col5, col6 = st.columns(3)

    with col4:
        st.subheader("Data Pengujian")
        
        tanggal = st.date_input(
            "Tanggal Pengujian",
            value=datetime.strptime(st.session_state.saved_data.get('tanggal', ''),
                                    '%Y-%m-%d').date()
            if 'tanggal' in st.session_state.saved_data else datetime.now().date()
        )
        
        # Lokasi Pengujian selalu "Perusahaan" (tidak bisa diubah)
        lokasi = st.text_input(
            "Lokasi Pengujian",
            value="Perusahaan",
            disabled=True,
            help="Lokasi pengujian tetap Perusahaan sesuai standar."
        )

    with col5:
        st.subheader("Data Penera")
        
        df_penera = st.session_state.get('data_penera')
        
        if df_penera is not None and not df_penera.empty:
            # Pilihan nama dari dropdown
            selected_nama = st.selectbox(
                "Pilih Nama Penera",
                options=df_penera['Nama'].tolist(),
                index=None,
                placeholder="Ketik atau pilih nama...",
                key="penera_select"
            )
            
            if selected_nama:
                row = df_penera[df_penera['Nama'] == selected_nama].iloc[0]
                # Simpan ke session state
                st.session_state.nama_penera = selected_nama
                st.session_state.nip_penera = str(row['NIP'])
                st.session_state.golongan_penera = row.get('Golongan', '')
                
                # Tampilkan info
                st.caption(f"**NIP:** {row['NIP']}")
                st.caption(f"**Golongan:** {row.get('Golongan', '')}")
            else:
                # Jika belum memilih, tetap gunakan nilai session state (jika ada)
                st.session_state.nama_penera = st.session_state.get('nama_penera', '')
                st.session_state.nip_penera = st.session_state.get('nip_penera', '')
                
                # Opsi input manual
                if st.checkbox("Input manual"):
                    manual_nama = st.text_input(
                        "Nama Penera (manual)",
                        value=st.session_state.saved_data.get('nama_penera', '')
                    )
                    manual_nip = st.text_input(
                        "NIP Penera (manual)",
                        value=st.session_state.saved_data.get('nip_penera', '')
                    )
                    st.session_state.nama_penera = manual_nama
                    st.session_state.nip_penera = manual_nip
        else:
            # Jika file tidak ada, input manual
            st.info("📂 File data penera tidak ditemukan. Silakan input manual.")
            manual_nama = st.text_input(
                "Nama Penera",
                value=st.session_state.saved_data.get('nama_penera', '')
            )
            manual_nip = st.text_input(
                "NIP Penera",
                value=st.session_state.saved_data.get('nip_penera', '')
            )
            st.session_state.nama_penera = manual_nama
            st.session_state.nip_penera = manual_nip
        
        # Ambil nilai dari session state untuk digunakan di submit
        nama_penera = st.session_state.get('nama_penera', '')
        nip_penera = st.session_state.get('nip_penera', '')

    with col6:
        st.subheader("Informasi Tambahan")
        
        # Suhu ruangan selalu "Ambient" (tidak bisa diubah)
        suhu = st.text_input(
            "Suhu Ruangan",
            value="Ambient",
            disabled=True,
            help="Nilai tetap Ambient sesuai standar pengujian."
        )
        
        # Kelembaban selalu "Ambient" (tidak bisa diubah)
        kelembaban = st.text_input(
            "Kelembaban",
            value="Ambient",
            disabled=True,
            help="Nilai tetap Ambient sesuai standar pengujian."
        )
        
        # Metode pengujian tetap "Beban Substitusi Tunggal"
        metode = st.text_input(
            "Metode Pengujian",
            value="Beban Substitusi Tunggal",
            disabled=True,
        )

    st.markdown("---")
    st.subheader("Hasil Pengujian Kebenaran")

    # ======================== TABEL PENGUJIAN KEBENARAN ========================
    # Ambil nilai dari session state
    e = st.session_state.get('interval_skala_input', 20)
    cls = st.session_state.get('kelas', 'III')
    jns_uji = st.session_state.get('keterangan', 'Tera')

    # ======================== TABEL PENGUJIAN KEBENARAN ========================
    num_results = 8
    test_results = []

    st.write("**Masukkan Hasil Pengujian**")

    # Header kolom
    cols_header = st.columns([0.5, 1.6, 1.6, 1.2, 1.4, 1.6, 1.0, 1.0])
    for col, label in zip(cols_header, [
        "**No**", "**Standar (S)**", "**Balas (B)**",
        "**ΔL**", "**Kesalahan**", "**Penunjukan (I)**", "**BKD**", "**Hasil**"
    ]):
        col.write(label)

    for i in range(num_results):
        cols = st.columns([0.5, 1.6, 1.6, 1.2, 1.4, 1.6, 1.0, 1.0])

        with cols[0]:
            st.write(f"{i+1}")

        if i == 0:
            default_s = 20 * e
            default_b = 0
            default_hasil = "SAH"
        else:
            default_s = 0
            default_b = 0
            default_hasil = "SAH"

        default_dl = e / 2.0
        default_kes = 0

        # --- Standar ---
        with cols[1]:
            if i == 1:
                standar_val = st.number_input(
                    f"Standar {i+1}",
                    value=st.session_state.get(f"standar_{i}_{e}", default_s),
                    step=1,
                    format="%d",
                    key=f"standar_{i}_{e}",
                    on_change=copy_standar,
                    label_visibility="collapsed"
                )
            else:
                if i in [2, 4, 6]:
                    standar_val = 0
                elif i in [3, 5, 7]:
                    standar_val = st.session_state.get(f"standar_1_{e}", default_s)
                else:
                    standar_val = default_s

                st.number_input(
                    f"Standar {i+1}",
                    value=standar_val,
                    step=1,
                    format="%d",
                    key=f"standar_{i}_{e}",
                    disabled=True,
                    label_visibility="collapsed"
                )

        # --- Balas ---
        with cols[2]:
            if i in [2, 4, 6]:
                balas_val = st.number_input(
                    f"Balas {i+1}",
                    value=st.session_state.get(f"balas_{i}", 0),
                    step=1,
                    format="%d",
                    key=f"balas_{i}",
                    on_change=sync_balas,
                    args=(f"balas_{i}", f"balas_{i+1}"),
                    label_visibility="collapsed"
                )
            elif i in [3, 5, 7]:
                prev_idx = i - 1
                balas_val = st.session_state.get(f"balas_{prev_idx}", 0)

                st.number_input(
                    f"Balas {i+1}",
                    value=balas_val,
                    step=1,
                    format="%d",
                    key=f"balas_{i}",
                    disabled=True,
                    label_visibility="collapsed"
                )
            else:
                balas_val = 0

                st.number_input(
                    f"Balas {i+1}",
                    value=0,
                    step=1,
                    format="%d",
                    key=f"balas_{i}",
                    disabled=True,
                    label_visibility="collapsed"
                )

        # --- ΔL ---
        with cols[3]:
            delta_l_val = st.number_input(
                f"ΔL {i+1}",
                value=default_dl,
                step=0.1,
                format="%g",
                key=f"delta_l_{i}_{e}",
                disabled=True,
                label_visibility="collapsed"
            )

        # --- Kesalahan ---
        with cols[4]:
            kesalahan_val = st.number_input(
                f"Kesalahan {i+1}",
                value=default_kes,
                step=1,
                format="%d",
                disabled=True,
                key=f"kesalahan_{i}_{e}",
                label_visibility="collapsed"
            )

        # --- Penunjukan (I) ---
        with cols[5]:
            penunjukan_default = standar_val + balas_val
            penunjukan_val = st.number_input(
                f"Penunjukan {i+1}",
                value=penunjukan_default,
                step=1,
                format="%d",
                disabled=True,
                key=f"penunjukan_{i}_{e}_{penunjukan_default}",
                label_visibility="collapsed"
            )

        # --- BKD ---
        with cols[6]:
            muatan = standar_val + balas_val
            koef, bkd_kg = hitung_bkd(muatan, e, cls, jns_uji)
            if koef == 0.5:
                bkd_text = "±0.5e"
            elif koef == 1.0:
                bkd_text = "±1e"
            elif koef == 1.5:
                bkd_text = "±1.5e"
            elif koef == 2.0:
                bkd_text = "±2e"
            elif koef == 3.0:
                bkd_text = "±3e"
            else:
                bkd_text = f"±{koef:.1f}e"
            st.write(f"**{bkd_text}**")

        # --- Hasil ---
        with cols[7]:
            hasil_val = st.selectbox(
                f"Hasil {i+1}",
                ["SAH", "TIDAK SAH"],
                index=0 if default_hasil == "SAH" else 1,
                key=f"hasil_{i}_{e}",
                disabled=True,
                label_visibility="collapsed"
            )

        muatan_sb = standar_val + balas_val
        p_aktual = penunjukan_val + 0.5 * e - delta_l_val

        test_results.append({
            'standar': standar_val,
            'balas': balas_val,
            'muatan_sb': muatan_sb,
            'timbangan': penunjukan_val,
            'imbuh': delta_l_val,
            'p_aktual': p_aktual,
            'kesalahan': kesalahan_val,
            'bkd_koef': koef,
            'bkd_kg': bkd_kg,
            'bkd_text': bkd_text,
            'hasil': hasil_val == "SAH"
        })

    st.markdown("---")

    # ======================== PEMERIKSAAN VISUAL ========================
    st.markdown("---")
    st.subheader("Pemeriksaan Visual")
    visual_items = ["Tanda Tera", "Alat Penunjuk Kedataran", "Bersih dan Siap Uji", "Sesuai Persetujuan Tipe"]
    visual_results = {}
    cols_vis = st.columns(4)
    for idx, item in enumerate(visual_items):
        with cols_vis[idx % 4]:
            visual_results[item] = st.checkbox(item, value=True, key=f"vis_{item}")
    # ======================== REPETABILITY ========================
    st.markdown("---")
    st.subheader("Repetability (50% Maks)")

    kapasitas_max = st.session_state.kapasitas_max_input
    interval_skala = st.session_state.interval_skala_input
    kelas = st.session_state.get('kelas', 'III')
    keterangan = st.session_state.get('keterangan', 'Tera')

    half_max = int(kapasitas_max * 0.5)
    deltaL_default = interval_skala / 2.0

    # === Perbaikan: update nilai default jika kapasitas berubah ===
    if 'prev_kapasitas_max' not in st.session_state:
        st.session_state.prev_kapasitas_max = kapasitas_max

    if 'repet_I_1' not in st.session_state:
        st.session_state.repet_I_1 = half_max
    else:
        # Jika kapasitas berubah dan nilai saat ini masih sama dengan default lama, update
        if kapasitas_max != st.session_state.prev_kapasitas_max:
            half_max_old = int(st.session_state.prev_kapasitas_max * 0.5)
            if st.session_state.repet_I_1 == half_max_old:
                st.session_state.repet_I_1 = half_max
            st.session_state.prev_kapasitas_max = kapasitas_max

    # Header
    col_header = st.columns([1.2, 0.8, 1.5, 0.9, 1.0])
    with col_header[0]:
        st.write("**Penunjukan (I)**")
    with col_header[1]:
        st.write("**ΔL**")
    with col_header[2]:
        st.write("**P (I+0.5e-ΔL)**")
    with col_header[3]:
        st.write("**BKD**")
    with col_header[4]:
        st.write("**Hasil**")

    repet_data = []
    I_baris1 = st.session_state.repet_I_1  # acuan baris 1, di-refresh tiap iterasi i==1

    for i in range(1, 4):
        cols_repet = st.columns([1.2, 0.8, 1.5, 0.9, 1.0])

        with cols_repet[0]:
            if i == 1:
                I = st.number_input(
                    f"Penunjukan (I) {i}",
                    value=st.session_state.repet_I_1,
                    step=1,
                    format="%d",
                    key="repet_I_1",
                    label_visibility="collapsed"
                )
                I_baris1 = I  # tangkap nilai terbaru untuk dipakai baris 2 & 3
            else:
                # key disisipi I_baris1 supaya widget selalu "fresh" mengikuti
                # baris 1 tiap kali nilainya berubah (widget disabled dengan
                # key statis tidak akan ter-update lewat parameter value saja)
                I = st.number_input(
                    f"Penunjukan (I) {i}",
                    value=I_baris1,
                    step=1,
                    format="%d",
                    disabled=True,
                    key=f"repet_I_{i}_{I_baris1}",
                    label_visibility="collapsed"
                )
        with cols_repet[1]:
            deltaL = st.number_input(
                f"ΔL {i}",
                value=deltaL_default,
                step=0.1,
                format="%g",
                disabled=True,
                key=f"repet_dL_{i}_{interval_skala}",
                label_visibility="collapsed"
            )
        with cols_repet[2]:
            # key disisipi I supaya P ikut ter-update tiap kali I berubah
            P = st.number_input(
                f"P (I+0.5e-ΔL) {i}",
                value=I,
                step=1,
                format="%d",
                disabled=True,
                key=f"repet_P_{i}_{interval_skala}_{I}",
                label_visibility="collapsed"
            )
        with cols_repet[3]:
            muatan = I
            koef, bkd_kg = hitung_bkd(muatan, interval_skala, kelas, keterangan)
            bkd_text = "±0.5e" if koef == 0.5 else \
                       "±1e" if koef == 1.0 else \
                       "±1.5e" if koef == 1.5 else \
                       "±2e" if koef == 2.0 else \
                       "±3e" if koef == 3.0 else f"±{koef:.1f}e"
            st.write(f"**{bkd_text}**")
        with cols_repet[4]:
            hasil = st.selectbox(
                f"Hasil {i}",
                ["SAH", "TIDAK SAH"],
                 index=0,
                key=f"repet_hasil_{i}",
                disabled=True,
                label_visibility="collapsed"
            )

        repet_data.append({
            "penunjukan": I,
            "delta_l": deltaL,
            "p_value": P,
            "hasil": hasil == "SAH",
            "bkd_koef": koef,
            "bkd_kg": bkd_kg,
            "bkd_text": bkd_text
        })
# ======================== EKSENTRISITAS ========================
    st.markdown("---")
    st.subheader("Eksentrisitas (1/3 Maks)")

    kapasitas_max = st.session_state.kapasitas_max_input
    interval_skala = st.session_state.interval_skala_input
    kelas = st.session_state.get('kelas', 'III')
    keterangan = st.session_state.get('keterangan', 'Tera')

    one_third = int(kapasitas_max / 3.0)
    deltaL_eks = interval_skala / 2.0

    # === Perbaikan: update nilai default jika kapasitas berubah ===
    if 'prev_kapasitas_max_eks' not in st.session_state:
        st.session_state.prev_kapasitas_max_eks = kapasitas_max

    if 'eksen_I_1' not in st.session_state:
        st.session_state.eksen_I_1 = one_third
    else:
        if kapasitas_max != st.session_state.prev_kapasitas_max_eks:
            one_third_old = int(st.session_state.prev_kapasitas_max_eks / 3.0)
            if st.session_state.eksen_I_1 == one_third_old:
                st.session_state.eksen_I_1 = one_third
            st.session_state.prev_kapasitas_max_eks = kapasitas_max

    # Header
    col_header = st.columns([1.2, 0.8, 1.5, 0.9, 1.0])
    with col_header[0]:
        st.write("**Penunjukan (I)**")
    with col_header[1]:
        st.write("**ΔL**")
    with col_header[2]:
        st.write("**P (I+0.5e-ΔL)**")
    with col_header[3]:
        st.write("**BKD**")
    with col_header[4]:
        st.write("**Hasil**")

    eksen_data = []
    selisih_labels = ["3 & 1", "1 & 2", "2 & 3"]
    I_baris1 = st.session_state.eksen_I_1

    for i in range(1, 4):
        cols_eksen = st.columns([1.2, 0.8, 1.5, 0.9, 1.0])

        with cols_eksen[0]:
            if i == 1:
                I = st.number_input(
                    f"Penunjukan (I) {i}",
                    value=st.session_state.eksen_I_1,
                    step=1,
                    format="%d",
                    key="eksen_I_1",
                    label_visibility="collapsed"
                )
                I_baris1 = I
            else:
                I = st.number_input(
                    f"Penunjukan (I) {i}",
                    value=I_baris1,
                    step=1,
                    format="%d",
                    disabled=True,
                    key=f"eksen_I_{i}_{I_baris1}",
                    label_visibility="collapsed"
                )
        with cols_eksen[1]:
            deltaL = st.number_input(
                f"ΔL {i}",
                value=deltaL_eks,
                step=0.1,
                format="%g",
                disabled=True,
                key=f"eksen_dL_{i}_{interval_skala}",
                label_visibility="collapsed"
            )
        with cols_eksen[2]:
            P = st.number_input(
                f"P (I+0.5e-ΔL) {i}",
                value=I,
                step=1,
                format="%d",
                disabled=True,
                key=f"eksen_P_{i}_{interval_skala}_{I}",
                label_visibility="collapsed"
            )
        with cols_eksen[3]:
            muatan = I
            koef, bkd_kg = hitung_bkd(muatan, interval_skala, kelas, keterangan)
            bkd_text = "±0.5e" if koef == 0.5 else \
                       "±1e" if koef == 1.0 else \
                       "±1.5e" if koef == 1.5 else \
                       "±2e" if koef == 2.0 else \
                       "±3e" if koef == 3.0 else f"±{koef:.1f}e"
            st.write(f"**{bkd_text}**")
        with cols_eksen[4]:
            hasil = st.selectbox(
                f"Hasil {i}",
                ["SAH", "TIDAK SAH"],
                 index=0,
                key=f"eksen_hasil_{i}",
                disabled=True,
                label_visibility="collapsed"
            )

        eksen_data.append({
            "penunjukan": I,
            "delta_l": deltaL,
            "p_value": P,
            "selisih": selisih_labels[i-1],
            "hasil": hasil == "SAH",
            "bkd_koef": koef,
            "bkd_kg": bkd_kg,
            "bkd_text": bkd_text
        })

        # ======================== PENGUJIAN PENYETELAN NOL ========================
    st.markdown("---")
    st.subheader("Pengujian Penyetelan Nol")

    # Ambil interval_skala langsung dari session state (reaktif)
    e = st.session_state.get('interval_skala_input', 20)

    col_nol1, col_nol2, col_nol3, col_nol4, col_nol5 = st.columns(5)
    with col_nol1:
        setel_nol = st.number_input(
            "SETEL NOL",
            value=0,
            step=1,
            key=f"nol_setel_{e}",  # key dinamis
            disabled=True,
        )
    with col_nol2:
        muatan_10e = st.number_input(
            "MUATAN 10e (kg)",
            value=10 * e,
            step=1,
            key=f"nol_muatan_{e}",  # key dinamis
            disabled=True,
        )
    with col_nol3:
        awal = st.number_input(
            "AWAL",
            value=10 * e,
            step=1,
            key=f"nol_awal_{e}",  # key dinamis
            disabled=True,
        )
    with col_nol4:
        plus025e = st.number_input(
            "+0,25e",
            value=10 * e,
            step=1,
            key=f"nol_plus025_{e}",  # key dinamis
            disabled=True,
        )
    with col_nol5:
        plus05e = st.number_input(
            "+0,5e",
            value=10 * e + e,
            step=1,
            key=f"nol_plus05_{e}",  # key dinamis
            disabled=True,
        )

    nol_data = {
        "setel_nol": setel_nol,
        "muatan_10e": muatan_10e,
        "awal": awal,
        "plus025e": plus025e,
        "plus05e": plus05e
    }
        # ======================== PENGUJIAN PENYETEL TARA (TERA) ========================
    st.markdown("---")
    st.subheader("Pengujian Penyetel Tara (TERA)")

    # Hanya tampil jika jenis pengujian adalah "Tera"
    if st.session_state.get('keterangan', 'Tera') == "Tera":
        st.info("Tabel ini otomatis dihitung berdasarkan Kapasitas Maksimum dan Interval Skala.")

        kapasitas_max_tara = st.session_state.get('kapasitas_max_input', 60000)
        interval_skala_tara = st.session_state.get('interval_skala_input', 10)

        # Hitung nilai
        muatan_tara_val = int(0.2 * kapasitas_max_tara)
        muatan_10e_val = 10 * interval_skala_tara
        imbuh_025e_val = muatan_10e_val
        imbuh_05e_val = 11 * interval_skala_tara

        data_tara = {
            "KEGIATAN": ["SETEL NOL", "MUATAN TARA (20% MAKS)", "AKTIFKAN TARA", "+ muatan 10e", "+ imbuh 0,25e", "+ imbuh 0,5e"],
            "PENUNJUKKAN": [0, muatan_tara_val, 0, muatan_10e_val, imbuh_025e_val, imbuh_05e_val]
        }

        df_tara = pd.DataFrame(data_tara)
        st.dataframe(df_tara, use_container_width=True, hide_index=True)
    else:
        st.info("Pengujian Penyetel Tara hanya dilakukan pada Tera (bukan Tera Ulang).")
    # ======================== TOMBOL SIMPAN ========================
    col_submit1, col_submit2 = st.columns(2)
    with col_submit1:
        submit_btn = st.button("💾 Simpan Data", use_container_width=True, type="primary")
    with col_submit2:
        st.button("🔄 Reset Form", use_container_width=True)

    if submit_btn:
        # Ambil semua nilai dari session state (dengan default)
        kapasitas_max_final = st.session_state.get('kapasitas_max_input', 60000)
        daya_baca_final = st.session_state.get('daya_baca_input', 10)
        interval_skala_final = st.session_state.get('interval_skala_input', 10)
        kapasitas_min_final = st.session_state.get('kapasitas_min_input', 20 * interval_skala_final)
        kelas_final = st.session_state.get('kelas', 'III')
        keterangan_final = st.session_state.get('keterangan', 'Tera')
        st.session_state.generated_files = {}
        # Ambil nilai dari input yang masih berupa variabel lokal
        # (pemilik, alamat, merek, model, no_seri, suhu, kelembaban, metode, lokasi, nama_penera, nip_penera, tanggal)
        # Pastikan variabel-variabel ini sudah didefinisikan di atas (masih dalam scope yang sama)
        # Jika ada yang belum, gunakan session state atau default.

        st.session_state.saved_data = {
            'pemilik': pemilik,
            'alamat': alamat,
            'merek': merek,
            'model': model,
            'no_seri': no_seri,
            'kapasitas_max': kapasitas_max_final,
            'kapasitas_min': kapasitas_min_final,
            'daya_baca': daya_baca_final,
            'interval_skala': interval_skala_final,
            'kelas': kelas_final,
            'suhu': suhu,          # suhu sudah di-set "Ambient" (disabled)
            'kelembaban': kelembaban,  # kelembaban sudah di-set "Ambient"
            'metode': metode,      # metode sudah di-set "Beban Substitusi Tunggal"
            'lokasi': lokasi,      # lokasi sudah di-set "Perusahaan"
            'nama_penera': nama_penera,
            'nip_penera': nip_penera,
            'golongan_penera': st.session_state.get('golongan_penera', ''),
            'hasil_pengujian': test_results,
            'tanggal_penera': format_tanggal_indonesia(tanggal.strftime('%Y-%m-%d')),
            'tanggal_sertifikat': datetime.now().strftime('%Y-%m-%d'),
            'keterangan': keterangan_final,
            'berlaku_sampai': (datetime.strptime(tanggal.strftime('%Y-%m-%d'), '%Y-%m-%d').replace(
                year=datetime.now().year + 1)).strftime('%Y-%m-%d'),
            'repetability': repet_data,      # dari bagian repetability
            'eksentrisitas': eksen_data,     # dari bagian eksentrisitas
            'penyetelan_nol': nol_data,      # dari bagian penyetelan nol
            'visual': visual_results,        # dari bagian pemeriksaan visual
        }
        st.session_state.test_results = test_results
        st.success("✅ Data berhasil disimpan!")
        st.balloons()


# ===== MODE 2: GENERATE DOKUMEN =====
elif mode == "📄 Generate Dokumen":
    st.header("Generate Dokumen Cerapan & Sertifikat")
    
    if not st.session_state.saved_data:
        st.warning("⚠️ Silakan input data pengujian terlebih dahulu di menu 'Input Data Pengujian'")
    else:
        data = st.session_state.saved_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Preview Data")
            preview_cols = st.columns(2)
            
            with preview_cols[0]:
                st.write(f"**Pemilik:** {data.get('pemilik', '-')}")
                st.write(f"**Merek:** {data.get('merek', '-')}")
                st.write(f"**Model:** {data.get('model', '-')}")
                st.write(f"**No. Seri:** {data.get('no_seri', '-')}")
            
            with preview_cols[1]:
                st.write(f"**Penera:** {data.get('nama_penera', '-')}")
                st.write(f"**Tanggal:** {data.get('tanggal_penera', '-')}")
                st.write(f"**Kelas:** {data.get('kelas', '-')}")
                st.write(f"**Hasil Pengujian:** {len(data.get('hasil_pengujian', []))} data")
        
        with col2:
            st.subheader("📊 Nomor Dokumen")
            
            # Ambil tanggal dari saved_data
            tanggal_data = data.get('tanggal')
            
            # Jika tidak ada, coba dari tanggal_penera
            if not tanggal_data:
                tanggal_penera = data.get('tanggal_penera')
                if tanggal_penera:
                    # Parse tanggal dari format Indonesia (misal "30 Juni 2026")
                    try:
                        bulan_map = {"Januari":1, "Februari":2, "Maret":3, "April":4, "Mei":5, "Juni":6,
                                     "Juli":7, "Agustus":8, "September":9, "Oktober":10, "November":11, "Desember":12}
                        parts = tanggal_penera.split()
                        if len(parts) == 3:
                            day = int(parts[0])
                            month = bulan_map[parts[1]]
                            year = int(parts[2])
                            t = datetime(year, month, day)
                            tanggal_data = t.strftime('%Y-%m-%d')
                    except:
                        pass
            
            # Jika masih tidak ada, gunakan tanggal sekarang
            if not tanggal_data:
                tanggal_data = datetime.now().strftime('%Y-%m-%d')
            
            # Generate nomor berdasarkan tanggal
            default_sertifikat = generate_nomor_sertifikat(tanggal_data)
            default_order = generate_nomor_order(tanggal_data)
            
            nomor_sertifikat = st.text_input(
                "Nomor Sertifikat",
                value=default_sertifikat,
                placeholder="Format: XXX.X.X.XX/XXXX/XXX-X/X/XXXX"
            )
            
            nomor_order = st.text_input(
                "Nomor Order",
                value=default_order,
                placeholder="Format nomor order"
            )
            
            st.session_state.saved_data['nomor_order'] = nomor_order
        
        st.markdown("---")
        
        # Button untuk generate
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        # --- Tombol Generate Cerapan ---
        with col_btn1:
            if st.button("📝 Generate Cerapan", use_container_width=True):
                try:
                    output_path = Path("./output")
                    output_path.mkdir(exist_ok=True)
                    filename = output_path / f"Cerapan_{data.get('no_seri', 'UNKNOWN')}_{data.get('tanggal', '').replace('-', '')}.pdf"
                    generate_cerapan_pdf(st.session_state.saved_data, str(filename))
                    st.session_state.generated_files['cerapan'] = str(filename)
                    st.success("✅ Cerapan berhasil dibuat!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
         # --- Tombol Generate Sertifikat ---
        with col_btn2:
            if st.button("🎫 Generate Sertifikat", use_container_width=True):
                try:
                    output_path = Path("./output")
                    output_path.mkdir(exist_ok=True)
                    filename = output_path / f"Sertifikat_{data.get('no_seri', 'UNKNOWN')}_{data.get('tanggal', '').replace('-', '')}.pdf"
                    generate_sertifikat_pdf(st.session_state.saved_data, str(filename), nomor_sertifikat)
                    st.session_state.generated_files['sertifikat'] = str(filename)
                    st.success("✅ Sertifikat berhasil dibuat!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # --- Tombol Generate Kedua Dokumen ---
        with col_btn3:
            if st.button("📦 Generate Kedua Dokumen", use_container_width=True):
                try:
                    output_path = Path("./output")
                    output_path.mkdir(exist_ok=True)
                    
                    cerapan_file = output_path / f"Cerapan_{data.get('no_seri', 'UNKNOWN')}_{data.get('tanggal', '').replace('-', '')}.pdf"
                    generate_cerapan_pdf(st.session_state.saved_data, str(cerapan_file))
                    st.session_state.generated_files['cerapan'] = str(cerapan_file)
                    
                    sertifikat_file = output_path / f"Sertifikat_{data.get('no_seri', 'UNKNOWN')}_{data.get('tanggal', '').replace('-', '')}.pdf"
                    generate_sertifikat_pdf(st.session_state.saved_data, str(sertifikat_file), nomor_sertifikat)
                    st.session_state.generated_files['sertifikat'] = str(sertifikat_file)
                    
                    st.success("✅ Kedua dokumen berhasil dibuat!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # ===== TOMBOL DOWNLOAD BERDASARKAN SESSION STATE =====
        st.subheader("📥 Download Dokumen")
        
        cerapan_path = st.session_state.generated_files.get('cerapan')
        sertifikat_path = st.session_state.generated_files.get('sertifikat')
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            if cerapan_path and Path(cerapan_path).exists():
                with open(cerapan_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Cerapan",
                        data=f.read(),
                        file_name=Path(cerapan_path).name,
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.caption("Cerapan belum digenerate.")
        
        with col_dl2:
            if sertifikat_path and Path(sertifikat_path).exists():
                with open(sertifikat_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Sertifikat",
                        data=f.read(),
                        file_name=Path(sertifikat_path).name,
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.caption("Sertifikat belum digenerate.")
        
        st.markdown("---")
        

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Aplikasi Automasi Sertifikat Tera © 2026</p>
    <p>Match dengan Template Excel & Word</p>
    </div>
    """, unsafe_allow_html=True)
