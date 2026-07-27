import streamlit as st
import pandas as pd
from modules.pubbm.sertifikat_pubbm_generator import generate_sertifikat_pubbm
from datetime import date, datetime
import re
from pathlib import Path

def bulan_singkat_id(tanggal):
    bulan = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
        5: "MEI", 6: "JUN", 7: "JUL", 8: "AGS",
        9: "SEP", 10: "OKT", 11: "NOV", 12: "DES"
    }
    return bulan.get(tanggal.month, "")


def slug_filename(text):
    text = str(text).replace("/", "_").replace("\\", "_").replace(" ", "_")
    return "".join(ch for ch in text if ch.isalnum() or ch in ["_", "-", "."])


def parse_tanggal_file_pubbm(data):
    tanggal = (
        data.get("tanggal_pengujian")
        or data.get("tanggal")
        or data.get("tanggal_tera")
        or data.get("tanggal_penera")
    )

    if tanggal:
        if isinstance(tanggal, str):
            try:
                return datetime.strptime(tanggal, "%Y-%m-%d")
            except Exception:
                pass

        return tanggal

    return datetime.now()


def format_nama_file_pubbm(data):
    nama_spbu = (
        data.get("nama_spbu")
        or data.get("nomor_spbu")
        or data.get("nama_perusahaan")
        or data.get("pemilik")
        or "SPBU"
    )

    nama_penera = (
        data.get("penera_1")
        or data.get("nama_penera")
        or data.get("penera")
        or "PENERA"
    )

    tanggal = parse_tanggal_file_pubbm(data)
    tanggal_file = f"{tanggal.day:02d} {bulan_singkat_id(tanggal)}"

    nama_file = f"{nama_spbu}_{nama_penera}_{tanggal_file}"
    return slug_filename(nama_file)

@st.cache_data
def load_data_penera():
    try:
        df = pd.read_excel("data/data_penera.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Nama", "NIP", "Golongan"])

@st.cache_data
def load_data_spbu():
    try:
        df = pd.read_csv("data/data_spbu.csv", sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Nama SPBU", "Alamat"])
@st.cache_data
def load_data_bejana():
    try:
        df = pd.read_excel("data/data_bejana.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(
            columns=[
                "Standar Volume", "Merk", "Tipe", "Nomor Seri",
                "Kelas", "Kapasitas", "Daya Baca", "Telusuran"
            ]
        )
def get_kategori_spbu(nama_spbu):
    nama = str(nama_spbu).upper()

    if "SHELL" in nama:
        return "SPBU SHELL"

    elif "BP AKR" in nama or "BP" in nama:
        return "SPBU BP AKR"

    elif "VIVO" in nama:
        return "SPBU VIVO"

    elif "PERTASHOP" in nama:
        return "PERTASHOP"

    else:
        return "SPBU"


def get_media_options(nama_spbu, df_media):
    kategori = get_kategori_spbu(nama_spbu)

    if df_media is None or df_media.empty:
        return []

    row = df_media[
        df_media["NAMA SPBU"].astype(str).str.upper().str.strip()
        == kategori.upper()
    ]

    if row.empty:
        return []

    media_text = row.iloc[0]["MEDIA"]

    media_list = [
        m.strip()
        for m in str(media_text).split(",")
        if m.strip()
    ]

    return media_list
@st.cache_data
def load_data_media_spbu():
    try:
        df = pd.read_excel("data/data_media_spbu.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(
            {
                "NAMA SPBU": [
                    "SPBU",
                    "SPBU BP AKR",
                    "SPBU SHELL",
                    "SPBU VIVO",
                    "PERTASHOP"
                ],
                "MEDIA": [
                    "Pertalite, Pertamax, PERTAMAX GREEN, Pertamax Turbo, Solar, Pertamina Dex",
                    "BP 92, BP Ultimate, BP Diesel",
                    "Super, V-Power, Diesel",
                    "Revvo 90, Revvo 92, Revvo 95",
                    "Pertamax"
                ]
            }
        )
def update_spbu_terpilih():
    selected = st.session_state.get("spbu_select", "")
    df_spbu = st.session_state.get("data_spbu")

    if not selected or df_spbu is None or df_spbu.empty:
        return

    row = df_spbu[
        df_spbu["Nama SPBU"].astype(str) == str(selected)
    ]

    if row.empty:
        return

    data = row.iloc[0]

    st.session_state.nama_perusahaan = str(selected)
    st.session_state.alamat_input_pubbm = str(
        data.get("Alamat", "") or ""
    )

def run():
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 1])

    with col_nav1:
        if st.button("← Kembali ke Home", use_container_width=True):
            st.session_state.halaman = "home"
            st.rerun()
    
    with col_nav2:
        if st.button("⚖️ Ke Timbangan Jembatan", use_container_width=True):
            st.session_state.halaman = "tj"
            st.rerun()
    
    with col_nav3:
        if st.button("⚡ Ke kWh Meter", use_container_width=True):
            st.session_state.halaman = "kwh"
            st.rerun()

    with col_nav4:
        if st.button("⚖️ Ke Timbangan", use_container_width=True):
            st.session_state.halaman = "timbangan"
            st.rerun()
    
    def bulan_ke_romawi(bulan):
        romawi = {
            1: "I",
            2: "II",
            3: "III",
            4: "IV",
            5: "V",
            6: "VI",
            7: "VII",
            8: "VIII",
            9: "IX",
            10: "X",
            11: "XI",
            12: "XII"
        }
        return romawi.get(bulan, "")
    def generate_nomor_sertifikat(tanggal):
        if isinstance(tanggal, str):
            t = datetime.strptime(tanggal, "%Y-%m-%d")
        else:
            t = tanggal
    
        return f"500.2.3.15/0000/BID-K/{bulan_ke_romawi(t.month)}/{t.year}"
    
    
    def generate_nomor_order(tanggal):
        if isinstance(tanggal, str):
            t = datetime.strptime(tanggal, "%Y-%m-%d")
        else:
            t = tanggal
    
        return f"0000/SCD/{bulan_ke_romawi(t.month)}/{t.year}"
    
    # =========================
    # SESSION STATE AWAL
    # =========================
    if "data_penera" not in st.session_state:
        st.session_state.data_penera = load_data_penera()
    
    if "saved_data" not in st.session_state:
        st.session_state.saved_data = {}
    if "pubbm_dispenser" not in st.session_state:
        st.session_state.pubbm_dispenser = pd.DataFrame(
            columns=["No", "Posisi", "Merk", "Tipe", "No. Seri", "Media"]
        )
    if "data_spbu" not in st.session_state:
        st.session_state.data_spbu = load_data_spbu()
    if "data_bejana" not in st.session_state:
        st.session_state.data_bejana = load_data_bejana()
    if "data_media_spbu" not in st.session_state:
        st.session_state.data_media_spbu = load_data_media_spbu()
    if "data_pubbm" not in st.session_state:
        st.session_state.data_pubbm = {}
    # =========================
    # SIDEBAR
    # =========================
    mode = st.sidebar.radio(
        "Menu",
        [
            "📝 Input Data Pengujian",
            "📄 Preview & Generate Data"
        ]
    )
    
    
    # =========================
    # TITLE
    # =========================
    st.title("⛽ Aplikasi Automasi Sertifikat Tera PU BBM")
    st.markdown("---")
    
    
    # =========================
    # MODE INPUT
    # =========================
    if mode == "📝 Input Data Pengujian":
    
        st.header("Masukkan Data Pengujian PU BBM")
    
        # ======================== KOLOM 1-2 ========================
        col1, col2= st.columns(2)
    
        # ======================== KOLOM 1 ========================
        with col1:
            st.subheader("Identitas Pemilik / SPBU")
    
            df_spbu = st.session_state.get("data_spbu")
    
            if "nama_perusahaan" not in st.session_state:
                st.session_state.nama_perusahaan = st.session_state.saved_data.get("pemilik", "")
    
            if "nama_perusahaan" not in st.session_state:
                st.session_state.nama_perusahaan = ""
            
            if "alamat_input_pubbm" not in st.session_state:
                st.session_state.alamat_input_pubbm = ""
            
            if "input_manual_spbu" not in st.session_state:
                st.session_state.input_manual_spbu = False
    
            if df_spbu is not None and not df_spbu.empty:
                all_names = (
                    df_spbu["Nama SPBU"]
                    .dropna()
                    .astype(str)
                    .tolist()
                )
            
                st.selectbox(
                    "Cari & Pilih Nama SPBU",
                    options=[""] + all_names,
                    placeholder="Ketik nama SPBU...",
                    key="spbu_select",
                    on_change=update_spbu_terpilih
                )
            
                st.text_area(
                    "Alamat",
                    height=100,
                    key="alamat_input_pubbm",
                    help="Alamat ini dapat dilengkapi atau diedit."
                )
            
                st.checkbox(
                    "Input manual nama SPBU / perusahaan",
                    key="input_manual_spbu"
                )
            
                if st.session_state.input_manual_spbu:
                    st.text_input(
                        "Nama Pemilik / SPBU / Perusahaan",
                        key="nama_perusahaan"
                    )
            
            else:
                st.info(
                    "📂 File data perusahaan tidak ditemukan. "
                    "Silakan input manual."
                )
            
                st.text_input(
                    "Nama Pemilik / SPBU / Perusahaan",
                    key="nama_perusahaan",
                    placeholder=(
                        "Contoh: SPBU 34-15717 "
                        "PT. YASINCO INDO PRATAMA"
                    )
                )
            
                st.text_area(
                    "Alamat",
                    height=100,
                    key="alamat_input_pubbm",
                    placeholder=(
                        "Contoh: Jalan Aria Wasangkara Desa Tapos "
                        "Kecamatan Tigaraksa Kabupaten Tangerang"
                    )
                )
    
            pemilik = st.session_state.get("nama_perusahaan", "").strip()
            alamat = st.session_state.get("alamat_input_pubbm", "").strip()
    
            match_spbu = re.search(r"SPBU\s*[\d\.-]+", pemilik, re.IGNORECASE)
    
            if match_spbu:
                nomor_spbu = match_spbu.group(0).upper()
            else:
                nomor_spbu = ""
    
        # ======================== KOLOM 2 ========================
        with col2:
            st.subheader("Data Sertifikat")
            jenis_pengujian = st.selectbox(
            "Jenis Pengujian",
            ["Tera", "Tera Ulang"],
            index=1
    )
            tanggal_pengujian = st.date_input(
                "Tanggal Pengujian",
                value=date.today()
            )
            tanggal_cetak = st.date_input(
                "Tanggal Cetak / Tanggal Tanda Tangan",
                value=st.session_state.saved_data.get(
                    "tanggal_cetak",
                    date.today()
                ),
                key="tanggal_cetak_pubbm"
            )
            # Generate nomor berdasarkan tanggal
            tanggal_data = tanggal_pengujian
    
            default_sertifikat = generate_nomor_sertifikat(tanggal_data)
            default_order = generate_nomor_order(tanggal_data)
    
            nomor_sertifikat = st.text_input(
                "Nomor Sertifikat",
                value=st.session_state.saved_data.get(
                    "nomor_sertifikat",
                    default_sertifikat
                ),
                placeholder="Format: XXX.X.X.XX/XXXX/XXX-X/X/XXXX"
            )
    
            nomor_order = st.text_input(
                "Nomor Order",
                value=default_order,
                placeholder="Format nomor order"
            )
    
            st.session_state.saved_data["nomor_sertifikat"] = nomor_sertifikat
            st.session_state.saved_data["nomor_order"] = nomor_order
            st.session_state.saved_data["tanggal_pengujian"] = tanggal_pengujian
            st.session_state.saved_data["tanggal_cetak"] = tanggal_cetak
    
        st.markdown("---")
    
        # =========================
        # PENERA
        # =========================
        st.subheader("Penera / Pegawai Berhak")
    
        df_penera = st.session_state.get("data_penera")
    
        jumlah_penera = st.radio(
            "Jumlah Penera",
            [1, 2],
            horizontal=True,
            key="jumlah_penera"
        )
    
        col4, col5 = st.columns(2)
    
        # =========================
        # PENERA 1
        # =========================
        with col4:
    
            nama_penera_1 = st.selectbox(
                "Penera 1",
                options=[""] + df_penera["Nama"].tolist(),
                key="penera_1_select"
            )
    
            if nama_penera_1:
                row1 = df_penera[df_penera["Nama"] == nama_penera_1].iloc[0]
                penera_1 = row1["Nama"]
                nip_penera_1 = str(row1["NIP"])
                golongan_penera_1 = row1["Golongan"]
            else:
                penera_1 = ""
                nip_penera_1 = ""
                golongan_penera_1 = ""
    
            st.text_input(
                "NIP Penera 1",
                value=nip_penera_1,
                disabled=True
            )
    
            st.text_input(
                "Golongan Penera 1",
                value=golongan_penera_1,
                disabled=True
            )
    
    
        # =========================
        # PENERA 2
        # =========================
        if jumlah_penera == 2:
    
            with col5:
    
                nama_penera_2 = st.selectbox(
                    "Penera 2",
                    options=[""] + df_penera["Nama"].tolist(),
                    key="penera_2_select"
                )
    
                if nama_penera_2:
                    row2 = df_penera[df_penera["Nama"] == nama_penera_2].iloc[0]
                    penera_2 = row2["Nama"]
                    nip_penera_2 = str(row2["NIP"])
                    golongan_penera_2 = row2["Golongan"]
                else:
                    penera_2 = ""
                    nip_penera_2 = ""
                    golongan_penera_2 = ""
    
                st.text_input(
                    "NIP Penera 2",
                    value=nip_penera_2,
                    disabled=True
                )
    
                st.text_input(
                    "Golongan Penera 2",
                    value=golongan_penera_2,
                    disabled=True
                )
    
        else:
            penera_2 = ""
            nip_penera_2 = ""
            golongan_penera_2 = ""
    
        st.markdown("---")
    
        # =========================
        # BEJANA UKUR STANDAR
        # =========================
        st.subheader("Perangkat Bejana Ukur Standar 20L")

        df_bejana = st.session_state.get("data_bejana")

        jumlah_alat_standar = st.number_input(
            "Jumlah Alat Standar",
            min_value=1,
            max_value=10,
            value=int(
                st.session_state.saved_data.get(
                    "jumlah_alat_standar",
                    1
                )
            ),
            step=1,
            key="jumlah_alat_standar_pubbm"
        )

        st.session_state.saved_data[
            "jumlah_alat_standar"
        ] = jumlah_alat_standar

        data_alat_standar = []

        if df_bejana is not None and not df_bejana.empty:

            pilihan_bejana = (
                df_bejana["Merk"].astype(str)
                + " | No Seri : "
                + df_bejana["Nomor Seri"].astype(str)
            )
        
            jumlah_kolom = 2
        
            for awal in range(
                1,
                jumlah_alat_standar + 1,
                jumlah_kolom
            ):
        
                kolom_standar = st.columns(jumlah_kolom)
        
                for posisi_kolom in range(jumlah_kolom):
                    i = awal + posisi_kolom
        
                    if i > jumlah_alat_standar:
                        break
        
                    with kolom_standar[posisi_kolom]:
        
                        st.markdown(
                            f"**⚖️ Alat Standar {i}**"
                        )
        
                        selected_bejana = st.selectbox(
                            f"Pilih Bejana Ukur Standar {i}",
                            options=[""] + pilihan_bejana.tolist(),
                            index=0,
                            key=f"bejana_select_{i}",
                            label_visibility="collapsed"
                        )
        
                        if selected_bejana:
                            idx = pilihan_bejana[
                                pilihan_bejana == selected_bejana
                            ].index[0]
        
                            row_bejana = df_bejana.loc[idx]
        
                            merk_bus_item = str(
                                row_bejana.get("Merk", "")
                            )
        
                            nomor_seri_bus_item = str(
                                row_bejana.get("Nomor Seri", "")
                            )
        
                            telusuran_bus_item = str(
                                row_bejana.get("Telusuran", "")
                            )
        
                            data_alat_standar.append(
                                {
                                    "No": i,
                                    "Merk": merk_bus_item,
                                    "Nomor Seri": nomor_seri_bus_item,
                                    "Telusuran": telusuran_bus_item
                                }
                            )

        alat_standar_df = pd.DataFrame(
            data_alat_standar,
            columns=[
                "No",
                "Merk",
                "Nomor Seri",
                "Telusuran"
            ]
        )

        # Tetap siapkan variabel lama agar generator lama tidak error
        if not alat_standar_df.empty:
            alat_pertama = alat_standar_df.iloc[0]

            merk_bus = str(alat_pertama.get("Merk", ""))
            nomor_seri_bus = str(
                alat_pertama.get("Nomor Seri", "")
            )
            telusuran_bus = str(
                alat_pertama.get("Telusuran", "")
            )

        else:
            merk_bus = ""
            nomor_seri_bus = ""
            telusuran_bus = ""

        st.markdown("---")
        # =========================
        # DATA POMPA UKUR BBM
        # =========================
        st.subheader("Data Pompa Ukur BBM")
    
        df_media = st.session_state.get("data_media_spbu")
        media_options = get_media_options(pemilik, df_media)
    
        if media_options:
            st.success(
                "Pilihan media tersedia: " + ", ".join(media_options)
            )
        else:
            st.warning("Pilihan media belum tersedia. Periksa nama SPBU atau data_media_spbu.xlsx.")
            media_options = ["Pertalite", "Pertamax", "Solar"]
    
        # Sedikit styling agar lebih enak dilihat
        st.markdown(
            """
            <style>
            .pubbm-card {
                padding: 18px;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
                background-color: #fafafa;
                margin-bottom: 14px;
            }
            .pubbm-title {
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            .pubbm-help {
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 12px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
        # ==========================================
        # KELOLA JUMLAH DISPENSER
        # ==========================================
        if "jumlah_dispenser_pubbm" not in st.session_state:
            jumlah_awal = int(
                st.session_state.saved_data.get(
                    "jumlah_dispenser",
                    1
                )
            )
        
            st.session_state.jumlah_dispenser_pubbm = max(
                1,
                jumlah_awal
            )
        
        jumlah_dispenser = (
            st.session_state.jumlah_dispenser_pubbm
        )
        
        st.session_state.saved_data[
            "jumlah_dispenser"
        ] = jumlah_dispenser
        
        st.caption(
            f"Jumlah dispenser saat ini: {jumlah_dispenser}"
        )
        def tambah_dispenser():
            jumlah_sekarang = st.session_state.jumlah_dispenser_pubbm
        
            if jumlah_sekarang < 50:
                st.session_state.jumlah_dispenser_pubbm += 1
        
        
        def tambah_copy_dispenser():
            jumlah_lama = st.session_state.jumlah_dispenser_pubbm
        
            if jumlah_lama >= 50:
                return
        
            dispenser_asal = jumlah_lama
            dispenser_baru = jumlah_lama + 1
        
            # Salin identitas dispenser
            st.session_state[f"merk_{dispenser_baru}"] = (
                st.session_state.get(
                    f"merk_{dispenser_asal}",
                    ""
                )
            )
        
            st.session_state[f"tipe_{dispenser_baru}"] = (
                st.session_state.get(
                    f"tipe_{dispenser_asal}",
                    ""
                )
            )
        
            st.session_state[f"no_seri_{dispenser_baru}"] = (
                st.session_state.get(
                    f"no_seri_{dispenser_asal}",
                    ""
                )
            )
        
            jumlah_posisi_asal = int(
                st.session_state.get(
                    f"jumlah_posisi_{dispenser_asal}",
                    4
                )
            )
        
            st.session_state[
                f"jumlah_posisi_{dispenser_baru}"
            ] = jumlah_posisi_asal
        
            # Salin posisi dan media
            for idx_copy in range(
                1,
                jumlah_posisi_asal + 1
            ):
                st.session_state[
                    f"posisi_{dispenser_baru}_{idx_copy}"
                ] = st.session_state.get(
                    f"posisi_{dispenser_asal}_{idx_copy}",
                    ""
                )
        
                media_asal = st.session_state.get(
                    f"media_{dispenser_asal}_{idx_copy}",
                    ""
                )
        
                st.session_state[
                    f"media_{dispenser_baru}_{idx_copy}"
                ] = (
                    media_asal
                    if media_asal in media_options
                    else ""
                )
        
            st.session_state.jumlah_dispenser_pubbm = (
                dispenser_baru
            )
        
        
        def hapus_dispenser_terakhir():
            jumlah_sekarang = (
                st.session_state.jumlah_dispenser_pubbm
            )
        
            if jumlah_sekarang <= 1:
                return
        
            dispenser_hapus = jumlah_sekarang
        
            jumlah_posisi_hapus = int(
                st.session_state.get(
                    f"jumlah_posisi_{dispenser_hapus}",
                    4
                )
            )
        
            # Hapus identitas dispenser
            for key_hapus in [
                f"merk_{dispenser_hapus}",
                f"tipe_{dispenser_hapus}",
                f"no_seri_{dispenser_hapus}",
                f"jumlah_posisi_{dispenser_hapus}",
            ]:
                st.session_state.pop(
                    key_hapus,
                    None
                )
        
            # Hapus posisi dan media
            for idx_hapus in range(
                1,
                jumlah_posisi_hapus + 1
            ):
                st.session_state.pop(
                    f"posisi_{dispenser_hapus}_{idx_hapus}",
                    None
                )
        
                st.session_state.pop(
                    f"media_{dispenser_hapus}_{idx_hapus}",
                    None
                )
        
            st.session_state.jumlah_dispenser_pubbm -= 1
        data_rows = []

        for i in range(1, jumlah_dispenser + 1):

            with st.expander(
                f"⛽ Dispenser / Pompa Nomor {i}",
                expanded=(i == jumlah_dispenser)
            ):

                st.markdown(
                    f"""
                    <div class="pubbm-title">Dispenser {i}</div>
                    <div class="pubbm-help">
                        Isi spesifikasi dispenser, kemudian pilih media
                        untuk setiap posisi/nozzle.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # ==========================================
                # IDENTITAS DISPENSER
                # ==========================================
                col_b, col_c, col_d = st.columns(3)

                with col_b:
                    merk = st.text_input(
                        "Merk",
                        placeholder="",
                        key=f"merk_{i}"
                    )

                with col_c:
                    tipe = st.text_input(
                        "Tipe",
                        placeholder="",
                        key=f"tipe_{i}"
                    )

                with col_d:
                    no_seri = st.text_input(
                        "No. Seri",
                        placeholder="",
                        key=f"no_seri_{i}"
                    )

                st.markdown("**Posisi / Nozzle dan Media**")

                # Siapkan nilai awal jumlah posisi
                key_jumlah_posisi = f"jumlah_posisi_{i}"

                if key_jumlah_posisi not in st.session_state:
                    st.session_state[key_jumlah_posisi] = 4

                jumlah_posisi = st.number_input(
                    "Jumlah Posisi / Nozzle",
                    min_value=1,
                    max_value=20,
                    step=1,
                    key=key_jumlah_posisi
                )

                # ==========================================
                # DATA POSISI DAN MEDIA
                # ==========================================
                for idx in range(1, jumlah_posisi + 1):

                    col_posisi, col_media = st.columns([1, 2])

                    with col_posisi:
                        posisi = st.text_input(
                            f"Posisi {idx}",
                            placeholder="Contoh: 1, 1.1, 1.2, 3.4",
                            key=f"posisi_{i}_{idx}"
                        )

                    with col_media:
                        media = st.selectbox(
                            f"Media {idx}",
                            options=[""] + media_options,
                            key=f"media_{i}_{idx}"
                        )

                    if media.strip():
                        data_rows.append(
                            {
                                "No": i,
                                "Posisi": posisi.strip(),
                                "Merk": merk.strip(),
                                "Tipe": tipe.strip(),
                                "No. Seri": no_seri.strip(),
                                "Media": media.strip()
                            }
                        )
                if i == jumlah_dispenser:
                    st.markdown("---")
                    st.markdown("**Kelola Dispenser**")
                
                    col_tambah, col_copy, col_hapus = st.columns(3)
                
                    with col_tambah:
                        st.button(
                            "➕ Tambah Dispenser",
                            use_container_width=True,
                            key=f"tambah_dispenser_setelah_{i}",
                            on_click=tambah_dispenser,
                            disabled=(
                                st.session_state.jumlah_dispenser_pubbm >= 50
                            )
                        )
                
                    with col_copy:
                        st.button(
                            "📋 Tambah & Copy",
                            use_container_width=True,
                            key=f"copy_dispenser_setelah_{i}",
                            on_click=tambah_copy_dispenser,
                            disabled=(
                                st.session_state.jumlah_dispenser_pubbm >= 50
                            )
                        )
                
                    with col_hapus:
                        st.button(
                            "🗑️ Hapus Dispenser",
                            use_container_width=True,
                            key=f"hapus_dispenser_{i}",
                            on_click=hapus_dispenser_terakhir,
                            disabled=(
                                st.session_state.jumlah_dispenser_pubbm <= 1
                            )
                        )
        kolom_dispenser = ["No", "Posisi", "Merk", "Tipe", "No. Seri", "Media"]
    
        dispenser_df = pd.DataFrame(data_rows, columns=kolom_dispenser)
    
        # Bersihkan baris yang belum lengkap media-nya jika kolom tersedia
        if not dispenser_df.empty:
            dispenser_df = dispenser_df[
                (dispenser_df["Media"].astype(str).str.strip() != "")
            ]
    
        st.session_state.pubbm_dispenser = dispenser_df
    
        st.markdown("---")
    
        # =========================
        # SIMPAN DATA KE SESSION STATE
        # =========================
        data_pubbm = {
            "nomor_sertifikat": nomor_sertifikat,
            "nomor_order": nomor_order,
            "tanggal_pengujian": tanggal_pengujian,
            "tanggal_cetak": tanggal_cetak,
    
            "nama_alat": "Pompa Ukur BBM (Dispenser)",
    
            "pemilik": pemilik,
            "nama_spbu": nomor_spbu,
            "alamat": alamat,
    
            "jenis_pengujian": jenis_pengujian,
    
            "penera_1": penera_1,
            "nip_penera_1": nip_penera_1,
            "golongan_penera_1": golongan_penera_1,
    
            "penera_2": penera_2,
            "nip_penera_2": nip_penera_2,
            "golongan_penera_2": golongan_penera_2,
    
            "jumlah_penera": jumlah_penera,
            "jumlah_alat_standar": jumlah_alat_standar,
            "alat_standar": alat_standar_df,
            "merk_bus": merk_bus,
            "nomor_seri_bus": nomor_seri_bus,
            "telusuran_bus": telusuran_bus,
            "jumlah_dispenser": jumlah_dispenser,
            "dispenser": dispenser_df,
        }
    
        if st.button("💾 Simpan Data", type="primary"):
            st.session_state.data_pubbm = data_pubbm
    
            st.balloons()
    
            st.success(
                "Data PU BBM berhasil disimpan. Silakan buka menu Preview & Generate Data untuk mengecek dan generate sertifikat."
            )
    
    # =========================
    # MODE PREVIEW
    # =========================
    elif mode == "📄 Preview & Generate Data":
    
        st.header("Preview Data PU BBM")
    
        data_pubbm = st.session_state.get("data_pubbm")
    
        if not data_pubbm:
            st.warning("Belum ada data. Silakan isi data terlebih dahulu di menu Input Data Pengujian.")
            st.stop()
    
        st.subheader("Identitas Sertifikat")
    
        col1, col2, col3 = st.columns(3)
    
        with col1:
            st.write("**Nomor Sertifikat:**")
            st.write(data_pubbm.get("nomor_sertifikat", ""))
    
            st.write("**Nomor Order:**")
            st.write(data_pubbm.get("nomor_order", ""))
    
        with col2:
            st.write("**Tanggal Pengujian:**")
            st.write(data_pubbm.get("tanggal_pengujian", ""))
    
            st.write("**Jenis Pengujian:**")
            st.write(data_pubbm.get("jenis_pengujian", ""))
    
        with col3:
            st.write("**Nama Alat:**")
            st.write(data_pubbm.get("nama_alat", ""))
    
        st.markdown("---")
    
        st.subheader("Identitas Pemilik / SPBU")
    
        st.write("**Pemilik:**")
        st.write(data_pubbm.get("pemilik", ""))
    
        st.write("**Alamat:**")
        st.write(data_pubbm.get("alamat", ""))
    
        st.markdown("---")
    
        st.subheader("Penera / Pegawai Berhak")
    
        st.write("**Penera 1:**")
        st.write(
            f"{data_pubbm.get('penera_1', '')} / "
            f"NIP. {data_pubbm.get('nip_penera_1', '')} / "
            f"{data_pubbm.get('golongan_penera_1', '')}"
        )
    
        if data_pubbm.get("jumlah_penera") == 2:
            st.write("**Penera 2:**")
            st.write(
                f"{data_pubbm.get('penera_2', '')} / "
                f"NIP. {data_pubbm.get('nip_penera_2', '')} / "
                f"{data_pubbm.get('golongan_penera_2', '')}"
            )
    
        st.markdown("---")
    
        st.subheader("Perangkat Bejana Ukur Standar")

        alat_standar_df = data_pubbm.get("alat_standar")
        
        if (
            alat_standar_df is not None
            and isinstance(alat_standar_df, pd.DataFrame)
            and not alat_standar_df.empty
        ):
            st.dataframe(
                alat_standar_df,
                use_container_width=True,
                hide_index=True
            )
        
        else:
            col4, col5, col6 = st.columns(3)
        
            with col4:
                st.write("**Merk / Buatan:**")
                st.write(data_pubbm.get("merk_bus", ""))
        
            with col5:
                st.write("**Nomor Seri:**")
                st.write(data_pubbm.get("nomor_seri_bus", ""))
        
            with col6:
                st.write("**Telusuran:**")
                st.write(data_pubbm.get("telusuran_bus", ""))
    
        st.markdown("---")
    
        st.subheader("Data Pompa Ukur BBM")
    
        dispenser_df = data_pubbm.get("dispenser")
    
        if dispenser_df is None or dispenser_df.empty:
            st.warning("Data pompa ukur BBM belum diisi.")
        else:
            st.dataframe(
                dispenser_df,
                use_container_width=True,
                hide_index=True
            )
    
        st.markdown("---")
    
        st.subheader("Generate Sertifikat")
    
        if st.button("📄 Generate Sertifikat PU BBM", type="primary"):
            try:
                output_dir = Path("output/pubbm/sertifikat")
                output_dir.mkdir(parents=True, exist_ok=True)
        
                nama_file = format_nama_file_pubbm(data_pubbm)
                output_file = output_dir / f"{nama_file}.pdf"
        
                generate_sertifikat_pubbm(
                    data_pubbm,
                    str(output_file)
                )
        
                with open(output_file, "rb") as pdf:
                    st.download_button(
                        label="⬇️ Download Sertifikat PU BBM",
                        data=pdf.read(),
                        file_name=output_file.name,
                        mime="application/pdf"
                    )
        
                st.success("✅ Sertifikat PU BBM berhasil dibuat!")
        
            except Exception as e:
                st.error(f"Gagal membuat sertifikat PU BBM: {e}")
                import traceback
                st.code(traceback.format_exc())
