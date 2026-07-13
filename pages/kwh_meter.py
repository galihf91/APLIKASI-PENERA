import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path("data")
try:
    from modules.kwh_meter.sertifikat_kwh_generator import generate_sertifikat_kwh
except ModuleNotFoundError:
    # Fallback jika file generator diletakkan satu folder dengan halaman ini
    from sertifikat_kwh_generator import generate_sertifikat_kwh


# =========================
# HELPER DATA
# =========================
def bulan_singkat_id(tanggal):
    bulan = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
        5: "MEI", 6: "JUN", 7: "JUL", 8: "AGS",
        9: "SEP", 10: "OKT", 11: "NOV", 12: "DES"
    }
    return bulan.get(tanggal.month, "")


def format_nama_file_sertifikat(data):
    pemilik = data.get("pemilik", "KWH")
    penera = data.get("penera_1", "PENERA")
    tanggal = data.get("tanggal_pengujian") or date.today()

    if isinstance(tanggal, str):
        tanggal = datetime.strptime(tanggal, "%Y-%m-%d")

    tanggal_file = f"{tanggal.day:02d} {bulan_singkat_id(tanggal)}"

    nama_file = f"{pemilik}_{penera}_{tanggal_file}"
    return slug_filename(nama_file)
@st.cache_data
def load_data_penera():
    try:
        df = pd.read_excel("data/data_penera.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Nama", "NIP", "Golongan"])

def bulan_ke_romawi(bulan):
    romawi = {
        1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
        7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
    }
    return romawi.get(int(bulan), "")


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
    # Disesuaikan contoh SKHP kWh Meter: 0046/UAPV/SCD/X/2025
    return f"0000/UAPV/SCD/{bulan_ke_romawi(t.month)}/{t.year}"


def tambah_tahun(tanggal, tahun=10):
    try:
        return tanggal.replace(year=tanggal.year + tahun)
    except ValueError:
        return tanggal.replace(month=2, day=28, year=tanggal.year + tahun)


def slug_filename(text):
    text = str(text).replace("/", "_").replace("\\", "_").replace(" ", "_")
    return "".join(ch for ch in text if ch.isalnum() or ch in ["_", "-", "."])


def init_state():
    defaults = {
        "data_penera": load_data_penera(),
        "saved_data_kwh": {},
        "data_kwh": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =========================
# KONFIGURASI HALAMAN
def run():
    init_state()

    st.title("⚡ Pengujian kWh Meter")
    import inspect

    col_nav1, col_nav2, col_nav3 = st.columns(3)

    with col_nav1:
        if st.button("← Kembali ke Home", use_container_width=True):
            st.session_state.halaman = "home"
            st.rerun()

    with col_nav2:
        if st.button("⚖️ Ke Timbangan Jembatan", use_container_width=True):
            st.session_state.halaman = "tj"
            st.rerun()

    with col_nav3:
        if st.button("⛽ Ke PUBBM", use_container_width=True):
            st.session_state.halaman = "pubbm"
            st.rerun()

    st.markdown("---")

    mode = st.sidebar.radio(
        "Menu kWh Meter",
        [
            "📝 Input Data Pengujian",
            "📄 Preview & Generate Data"
        ],
        key="menu_kwh"
    )

    # =========================
    # MODE INPUT
    # =========================
    if mode == "📝 Input Data Pengujian":
        st.header("Masukkan Data Pengujian kWh Meter")

        saved = st.session_state.get("saved_data_kwh", {})

        # ========================
        # DATA UMUM ALAT
        # ========================
        st.subheader("Data Umum Alat")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            nama_alat = st.text_input(
                "Nama Alat",
                value="kWh Meter",
                disabled=True,
                key="nama_alat_kwh",
            )

        with col_a2:
            pilihan_merk_buatan = [
                "SMART / INDONESIA",
                "CANNET / INDONESIA",
            ]

            merk_buatan = st.selectbox(
                "Merk / Buatan",
                options=pilihan_merk_buatan,
                index=pilihan_merk_buatan.index(
                    saved.get("merk_buatan", "SMART / INDONESIA")
                ) if saved.get("merk_buatan", "SMART / INDONESIA") in pilihan_merk_buatan else 0,
                key="merk_buatan_kwh",
            )

        with col_a3:
            model_tipe = st.text_input(
                "Model / Tipe",
                value=saved.get("model_tipe", ""),
                placeholder="Contoh: SMI810V3",
                key="model_tipe_kwh",
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        # ======================== KOLOM 1: PEMILIK ========================
        with col1:
            st.subheader("Identitas Pemilik / Pengguna")

            saved = st.session_state.get("saved_data_kwh", {})

            if merk_buatan == "SMART / INDONESIA":
                pemilik = "PT. SMART METER INDONESIA"
                alamat = (
                    "Jalan Karet Utara II Zona Industri Mekarjaya No. 07, Kelurahan Mekar Jaya "
                    "Kecamatan Sepatan, Kabupaten Tangerang - Banten"
                )

            elif merk_buatan == "CANNET / INDONESIA":
                pemilik = "PT. CANNET ELEKTRIK INDONESIA"
                alamat = (
                    "Jalan Bhumimas VIII No. 16 Talagasari Kecamatan Cikupa, "
                    "Kabupaten Tangerang - Banten"
                )

            else:
                pemilik = ""
                alamat = ""

            st.text_input(
                "Nama Pemilik / Perusahaan",
                value=pemilik,
                disabled=True
            )

            st.text_area(
                "Alamat",
                value=alamat,
                height=90,
                disabled=True
            )

            if merk_buatan == "SMART / INDONESIA":
                untuk_pengguna = st.text_input(
                    "Untuk / Tujuan Penggunaan",
                    value=saved.get("untuk_pengguna", ""),
                    placeholder="Contoh: PT. PLN (Persero) LHOKSEUMAWE",
                )
            else:
                untuk_pengguna = ""

        # ======================== KOLOM 2: SERTIFIKAT ========================
        with col2:
            st.subheader("Data Sertifikat")

            jenis_pengujian = st.selectbox(
                "Jenis Pengujian",
                ["Tera", "Tera Ulang"],
                index=0,
            )

            tanggal_pengujian = st.date_input("Tanggal Pengujian", value=date.today())
            default_sertifikat = generate_nomor_sertifikat(tanggal_pengujian)
            default_order = generate_nomor_order(tanggal_pengujian)

            nomor_sertifikat = st.text_input(
                "Nomor Sertifikat",
                value=saved.get("nomor_sertifikat", default_sertifikat),
                placeholder="500.2.3.15/0000/BID-K/X/2026",
            )

            nomor_order = st.text_input(
                "Nomor Order",
                value=saved.get("nomor_order", default_order),
                placeholder="0000/UAPV/SCD/X/2026",
            )

            berlaku_sampai = st.date_input(
                "Berlaku Sampai",
                value=saved.get("berlaku_sampai", tambah_tahun(tanggal_pengujian, 10)),
                disabled=True,
            )

        st.markdown("---")

        # =========================
        # PENERA
        # =========================
        st.subheader("Penera / Pegawai Berhak")

        df_penera = st.session_state.get("data_penera")
        if df_penera is None or df_penera.empty:
            st.warning("Data penera tidak ditemukan. Input manual nama dan NIP.")
            jumlah_penera = 1
            col4, col5, col6 = st.columns(3)
            with col4:
                penera_1 = st.text_input("Nama Penera 1")
            with col5:
                nip_penera_1 = st.text_input("NIP Penera 1")
            with col6:
                golongan_penera_1 = st.text_input("Golongan Penera 1")
            penera_2 = nip_penera_2 = golongan_penera_2 = ""
        else:
            jumlah_penera = st.radio("Jumlah Penera", [1, 2], horizontal=True, key="jumlah_penera_kwh")
            col4, col5 = st.columns(2)

            with col4:
                nama_penera_1 = st.selectbox(
                    "Penera 1",
                    options=[""] + df_penera["Nama"].dropna().astype(str).tolist(),
                    key="penera_1_kwh_select",
                )
                if nama_penera_1:
                    row1 = df_penera[df_penera["Nama"].astype(str) == nama_penera_1].iloc[0]
                    penera_1 = str(row1.get("Nama", ""))
                    nip_penera_1 = str(row1.get("NIP", ""))
                    golongan_penera_1 = str(row1.get("Golongan", ""))
                else:
                    penera_1 = nip_penera_1 = golongan_penera_1 = ""

                st.text_input("NIP Penera 1", value=nip_penera_1, disabled=True)
                st.text_input("Golongan Penera 1", value=golongan_penera_1, disabled=True)

            if jumlah_penera == 2:
                with col5:
                    nama_penera_2 = st.selectbox(
                        "Penera 2",
                        options=[""] + df_penera["Nama"].dropna().astype(str).tolist(),
                        key="penera_2_kwh_select",
                    )
                    if nama_penera_2:
                        row2 = df_penera[df_penera["Nama"].astype(str) == nama_penera_2].iloc[0]
                        penera_2 = str(row2.get("Nama", ""))
                        nip_penera_2 = str(row2.get("NIP", ""))
                        golongan_penera_2 = str(row2.get("Golongan", ""))
                    else:
                        penera_2 = nip_penera_2 = golongan_penera_2 = ""

                    st.text_input("NIP Penera 2", value=nip_penera_2, disabled=True)
                    st.text_input("Golongan Penera 2", value=golongan_penera_2, disabled=True)
            else:
                penera_2 = nip_penera_2 = golongan_penera_2 = ""

        st.markdown("---")

        # =========================
        # DATA KWH METER
        # =========================
        st.subheader("Data kWh Meter")

        st.markdown(
            """
            <style>
            .kwh-card {
                padding: 18px;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
                background-color: #fafafa;
                margin-bottom: 14px;
            }
            .kwh-title {
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 4px;
            }
            .kwh-help {
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 12px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="kwh-card">
                <div class="kwh-title">Data Utama kWh Meter</div>
                <div class="kwh-help">
                    Isi data sesuai kolom pada sertifikat: UNIT, TEGANGAN, ARUS, PHS, KLS, KONST.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            unit = st.text_input(
                "UNIT",
                value=saved.get("unit", "1"),
                key="kwh_unit"
            )

            tegangan = st.text_input(
                "TEGANGAN",
                value=saved.get("tegangan", "230 V"),
                key="kwh_tegangan"
            )

        with c2:
            arus = st.text_input(
                "ARUS",
                value=saved.get("arus", "5(60) A"),
                key="kwh_arus"
            )

            phs = st.selectbox(
                "PHS",
                ["1", "3"],
                index=0 if saved.get("phs", "1") == "1" else 1,
                key="kwh_phs"
            )

        with c3:
            kelas = st.text_input(
                "KLS",
                value=saved.get("kelas", "1"),
                key="kwh_kls"
            )

            konstanta = st.text_input(
                "KONST",
                value=saved.get("konstanta", "1600 imp/kWh"),
                key="kwh_konst"
            )

        kwh_df = pd.DataFrame(
            [
                {
                    "UNIT": str(unit).strip(),
                    "TEGANGAN": str(tegangan).strip(),
                    "ARUS": str(arus).strip(),
                    "PHS": str(phs).strip(),
                    "KLS": str(kelas).strip(),
                    "KONST": str(konstanta).strip(),
                }
            ],
            columns=["UNIT", "TEGANGAN", "ARUS", "PHS", "KLS", "KONST"]
        )
        
        st.markdown("---")

        data_kwh = {
            "nomor_sertifikat": nomor_sertifikat,
            "nomor_order": nomor_order,
            "tanggal_pengujian": tanggal_pengujian,
            "tanggal_cetak": date.today(),
            "berlaku_sampai": berlaku_sampai,
            "jenis_pengujian": jenis_pengujian,
            "nama_alat": nama_alat,
            "merk_buatan": merk_buatan,
            "model_tipe": model_tipe,
            "pemilik": pemilik,
            "alamat": alamat,
            "untuk_pengguna": untuk_pengguna,
            "penera_1": penera_1,
            "nip_penera_1": nip_penera_1,
            "golongan_penera_1": golongan_penera_1,
            "penera_2": penera_2,
            "nip_penera_2": nip_penera_2,
            "golongan_penera_2": golongan_penera_2,
            "jumlah_penera": jumlah_penera,
            "jumlah_unit": 1,
            "kwh_meter": kwh_df,
            "unit": unit,
            "tegangan": tegangan,
            "arus": arus,
            "phs": phs,
            "kelas": kelas,
            "konstanta": konstanta,
        }

        if st.button("💾 Simpan Data", type="primary"):
            st.session_state.data_kwh = data_kwh
            st.session_state.saved_data_kwh = data_kwh
            st.success("Data kWh Meter berhasil disimpan. Silakan buka menu Preview & Generate Data.")


    # =========================
    # MODE PREVIEW
    # =========================
    elif mode == "📄 Preview & Generate Data":

        st.header("Preview Data kWh Meter")

        data_kwh = st.session_state.get("data_kwh", {})

        if not data_kwh:
            st.warning("Belum ada data. Silakan isi data terlebih dahulu di menu Input Data Pengujian.")
            st.stop()

        st.subheader("Data Umum Alat")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            st.write("**Nama Alat:**")
            st.write(data_kwh.get("nama_alat", ""))

        with col_a2:
            st.write("**Merk / Buatan:**")
            st.write(data_kwh.get("merk_buatan", ""))

        with col_a3:
            st.write("**Model / Tipe:**")
            st.write(data_kwh.get("model_tipe", ""))

        st.markdown("---")

        st.subheader("Identitas Pemilik / Pengguna")
        st.write("**Pemilik:**")
        st.write(data_kwh.get("pemilik", ""))
        st.write("**Alamat:**")
        st.write(data_kwh.get("alamat", ""))
        st.write("**Untuk:**")
        st.write(data_kwh.get("untuk_pengguna", ""))

        st.markdown("---")

        st.subheader("Penera / Pegawai Berhak")
        st.write("**Penera 1:**")
        st.write(
            f"{data_kwh.get('penera_1', '')} / "
            f"NIP. {data_kwh.get('nip_penera_1', '')} / "
            f"{data_kwh.get('golongan_penera_1', '')}"
        )

        if data_kwh.get("jumlah_penera") == 2:
            st.write("**Penera 2:**")
            st.write(
                f"{data_kwh.get('penera_2', '')} / "
                f"NIP. {data_kwh.get('nip_penera_2', '')} / "
                f"{data_kwh.get('golongan_penera_2', '')}"
            )

        st.markdown("---")

        st.subheader("Data kWh Meter")
        kwh_df = data_kwh.get("kwh_meter")
        if kwh_df is None or kwh_df.empty:
            st.warning("Data kWh Meter belum diisi.")
        else:
            st.dataframe(kwh_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        hasil_uji_df = data_kwh.get("hasil_uji")
        if hasil_uji_df is not None and not hasil_uji_df.empty:
            st.dataframe(hasil_uji_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.subheader("Generate Sertifikat")

        if st.button("📄 Generate Sertifikat kWh Meter", type="primary"):
            try:
                output_dir = Path("output/kwh_meter/sertifikat")
                output_dir.mkdir(parents=True, exist_ok=True)

                nama_file = format_nama_file_sertifikat(data_kwh)
                output_file = output_dir / f"{nama_file}.pdf"

                generate_sertifikat_kwh(data_kwh, str(output_file))

                with open(output_file, "rb") as pdf:
                    st.download_button(
                        label="⬇️ Download Sertifikat kWh Meter",
                        data=pdf,
                        file_name=output_file.name,
                        mime="application/pdf",
                    )

                st.success(f"Sertifikat berhasil dibuat: {output_file}")

            except Exception as e:
                st.error(f"Gagal membuat sertifikat: {e}")
                import traceback
                st.code(traceback.format_exc())
