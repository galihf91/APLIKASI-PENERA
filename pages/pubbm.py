import streamlit as st
import pandas as pd
from modules.pubbm.sertifikat_pubbm_generator import generate_sertifikat_pubbm
from datetime import date, datetime
import re

def run():
    st.title("Pengujian PUBBM")

    if st.button("← Kembali ke Home"):
        st.session_state.halaman = "home"
        st.rerun()
    st.divider()

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
    
    
    # =========================
    # KONFIGURASI HALAMAN
    # =========================
    st.set_page_config(
        page_title="PENERA - Sertifikat PU BBM",
        layout="wide"
    )
    
    
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
    
            if "alamat_perusahaan" not in st.session_state:
                st.session_state.alamat_perusahaan = st.session_state.saved_data.get("alamat", "")
    
            if "alamat_edit" not in st.session_state:
                st.session_state.alamat_edit = st.session_state.alamat_perusahaan
    
            if "last_company" not in st.session_state:
                st.session_state.last_company = None
    
            if df_spbu is not None and not df_spbu.empty:
                all_names = df_spbu["Nama SPBU"].tolist()
    
                selected = st.selectbox(
                    "Cari & Pilih Nama SPBU",
                    options=[""] + all_names,
                    index=0,
                    placeholder="Ketik nama SPBU...",
                    key="spbu_select"
                )
    
                if selected:
                    row = df_spbu[df_spbu["Nama SPBU"] == selected].iloc[0]
                    st.session_state.nama_perusahaan = selected
                    st.session_state.alamat_perusahaan = row["Alamat"]
                    st.session_state.alamat_edit = row["Alamat"]
    
                st.text_area(
                    "Alamat",
                    value=st.session_state.alamat_edit,
                    height=90,
                    key="alamat_edit"
                )
    
                st.session_state.alamat_perusahaan = st.session_state.alamat_edit
    
                if st.checkbox("Input manual nama SPBU / perusahaan"):
                    manual_nama = st.text_input(
                        "Nama Pemilik / SPBU / Perusahaan",
                        value=st.session_state.nama_perusahaan
                    )
                    if manual_nama:
                        st.session_state.nama_perusahaan = manual_nama
    
            else:
                st.info("📂 File data perusahaan tidak ditemukan. Silakan input manual.")
    
                manual_nama = st.text_input(
                    "Nama Pemilik / SPBU / Perusahaan",
                    value=st.session_state.nama_perusahaan,
                    placeholder="Contoh: SPBU 34-15717 PT. YASINCO INDO PRATAMA"
                )
    
                manual_alamat = st.text_area(
                    "Alamat",
                    value=st.session_state.alamat_perusahaan,
                    height=80,
                    placeholder="Contoh: Jalan Aria Wasangkara Desa Tapos Kecamatan Tigaraksa Kabupaten Tangerang"
                )
    
                st.session_state.nama_perusahaan = manual_nama
                st.session_state.alamat_perusahaan = manual_alamat
                st.session_state.alamat_edit = manual_alamat
    
            pemilik = st.session_state.get("nama_perusahaan", "")
            alamat = st.session_state.get("alamat_perusahaan", "")
    
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
    
            # Generate nomor berdasarkan tanggal
            tanggal_data = tanggal_pengujian
    
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
    
            st.session_state.saved_data["nomor_sertifikat"] = nomor_sertifikat
            st.session_state.saved_data["nomor_order"] = nomor_order
    
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
    
        if df_bejana is not None and not df_bejana.empty:
    
            pilihan_bejana = (
                df_bejana["Merk"].astype(str)
                + " | No Seri : "
                + df_bejana["Nomor Seri"].astype(str)
            )
    
            selected_bejana = st.selectbox(
                "Pilih Bejana Ukur Standar",
                options=[""] + pilihan_bejana.tolist(),
                index=0,
                key="bejana_select"
            )
    
            if selected_bejana:
                idx = pilihan_bejana[pilihan_bejana == selected_bejana].index[0]
                row = df_bejana.loc[idx]
    
                merk_bus = row["Merk"]
                nomor_seri_bus = str(row["Nomor Seri"])
                telusuran_bus = row["Telusuran"]
    
            else:
                merk_bus = ""
                nomor_seri_bus = ""
                telusuran_bus = ""
    
            col8, col9, col10 = st.columns(3)
    
            with col8:
                st.text_input(
                    "Merk / Buatan",
                    value=merk_bus,
                    disabled=True
                )
    
            with col9:
                st.text_input(
                    "Nomor Seri",
                    value=nomor_seri_bus,
                    disabled=True
                )
    
            with col10:
                st.text_input(
                    "Telusuran",
                    value=telusuran_bus,
                    disabled=True
                )
    
        else:
            st.warning("Data bejana ukur tidak ditemukan.")
    
            col8, col9, col10 = st.columns(3)
    
            with col8:
                merk_bus = st.text_input("Merk / Buatan")
    
            with col9:
                nomor_seri_bus = st.text_input("Nomor Seri")
    
            with col10:
                telusuran_bus = st.text_input("Telusuran")
        st.markdown("---")
    
        # =========================
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
    
        jumlah_dispenser = st.number_input(
            "Jumlah Dispenser / Pompa",
            min_value=1,
            max_value=50,
            value=st.session_state.saved_data.get("jumlah_dispenser", 1),
            step=1
        )
    
        st.session_state.saved_data["jumlah_dispenser"] = jumlah_dispenser
    
        data_rows = []
    
        for i in range(1, jumlah_dispenser + 1):
    
            with st.expander(f"⛽ Dispenser / Pompa Nomor {i}", expanded=True if i == 1 else False):
    
                st.markdown(
                    f"""
                    <div class="pubbm-title">Dispenser {i}</div>
                    <div class="pubbm-help">
                        Isi spesifikasi dispenser, kemudian pilih media untuk setiap posisi/nozzle.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
                col_b, col_c, col_d = st.columns(3)
    
                no_dispenser = i
    
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
    
                jumlah_posisi = st.number_input(
                    "Jumlah Posisi / Nozzle",
                    min_value=1,
                    max_value=20,
                    value=4,
                    step=1,
                    key=f"jumlah_posisi_{i}"
                )
    
                for idx in range(1, jumlah_posisi + 1):
    
                    col_posisi, col_media = st.columns([1, 2])
    
                    with col_posisi:
                        posisi = st.text_input(
                            f"Posisi {idx}",
                            value="",
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
            "tanggal_cetak": date.today(),
    
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
    
            "merk_bus": merk_bus,
            "nomor_seri_bus": nomor_seri_bus,
            "telusuran_bus": telusuran_bus,
    
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
    
            nomor_order = data_pubbm.get("nomor_order", "PUBBM").replace("/", "_")
            output_file = f"PUBBM_{nomor_order}.pdf"
    
            generate_sertifikat_pubbm(
                data_pubbm,
                output_file
            )
    
            with open(output_file, "rb") as pdf:
                st.download_button(
                    label="⬇️ Download Sertifikat PU BBM",
                    data=pdf,
                    file_name=output_file,
                    mime="application/pdf"
                )
