import streamlit as st
from pathlib import Path


# =========================================================
# KONFIGURASI UTAMA
# Hanya dipanggil satu kali di aplikasi utama
# =========================================================
st.set_page_config(
    page_title="PENERA - Pengujian UTTP",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# PATH PROYEK
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


# =========================================================
# SEMBUNYIKAN NAVIGASI OTOMATIS STREAMLIT
# =========================================================
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stSidebarNavItems"] {
            display: none !important;
        }

        [data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE NAVIGASI UTAMA
# =========================================================
if "halaman" not in st.session_state:
    st.session_state.halaman = "home"


def pindah_halaman(nama_halaman):
    """Memindahkan halaman aplikasi utama."""
    st.session_state.halaman = nama_halaman
    st.rerun()


# =========================================================
# HALAMAN HOME
# =========================================================
def home():
    # Sidebar hanya disembunyikan pada halaman Home
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }

            [data-testid="collapsedControl"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    col_logo, col_title = st.columns([1, 5])

    with col_logo:
        if LOGO_PATH.exists():
            st.markdown(
                "<div style='margin-top:-18px;'>",
                unsafe_allow_html=True
            )

            st.image(
                str(LOGO_PATH),
                width=130
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

    with col_title:
        st.title("PENERA")
        st.markdown(
            "### Pelayanan Elektronik Tera dan Tera Ulang"
        )
        st.write("Aplikasi Pengujian UTTP")

    st.divider()

    st.subheader("Pengujian UTTP")
    st.write(
        "Silakan pilih jenis UTTP yang akan diuji:"
    )

    # =====================================================
    # BARIS PERTAMA
    # =====================================================
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("## ⚖️ Timbangan Jembatan")
            st.write(
                "Pengujian Timbangan Jembatan."
            )
            st.write(
                "**Output:** Cerapan PDF dan Sertifikat PDF"
            )

            if st.button(
                "Masuk ke Timbangan Jembatan",
                use_container_width=True,
                key="app_menu_tj"
            ):
                pindah_halaman("tj")

    with col2:
        with st.container(border=True):
            st.markdown("## ⚖️ Timbangan")
            st.write(
                "Pengujian Timbangan Elektronik, Timbangan "
                "Bobot Ingsut, Neraca Obat, Sentisimal, "
                "dan Timbangan Pegas."
            )
            st.write(
                "**Output:** Cerapan PDF dan Sertifikat PDF"
            )

            if st.button(
                "Masuk ke Pengujian Timbangan",
                use_container_width=True,
                key="app_menu_timbangan"
            ):
                pindah_halaman("timbangan")

    # =====================================================
    # BARIS KEDUA
    # =====================================================
    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown("## ⛽ PUBBM")
            st.write(
                "Pengujian Pompa Ukur Bahan Bakar Minyak."
            )
            st.write(
                "**Output:** Sertifikat PDF"
            )

            if st.button(
                "Masuk ke PUBBM",
                use_container_width=True,
                key="app_menu_pubbm"
            ):
                pindah_halaman("pubbm")

    with col4:
        with st.container(border=True):
            st.markdown("## ⚡ kWh Meter")
            st.write(
                "Pengujian alat ukur energi listrik."
            )
            st.write(
                "**Output:** Sertifikat PDF"
            )

            if st.button(
                "Masuk ke kWh Meter",
                use_container_width=True,
                key="app_menu_kwh"
            ):
                pindah_halaman("kwh")

    st.divider()
    st.caption("PENERA - Pengujian UTTP")


# =========================================================
# ROUTER HALAMAN
# =========================================================
halaman_aktif = st.session_state.halaman


if halaman_aktif == "home":
    home()


elif halaman_aktif == "tj":
    from pages.timbangan_jembatan import (
        run as run_timbangan_jembatan
    )

    run_timbangan_jembatan()


elif halaman_aktif == "timbangan":
    from pages.timbangan import run as run_timbangan

    run_timbangan()


elif halaman_aktif == "pubbm":
    from pages.pubbm import run as run_pubbm

    run_pubbm()


elif halaman_aktif == "kwh":
    from pages.kwh_meter import run as run_kwh_meter

    run_kwh_meter()


else:
    # Fallback jika nilai halaman tidak dikenali
    st.session_state.halaman = "home"
    st.rerun()
