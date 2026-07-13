import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="PENERA - Pengujian UTTP",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)
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
if "halaman" not in st.session_state:
    st.session_state.halaman = "home"


def home():
    # Sidebar disembunyikan hanya di halaman Home
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }

            [data-testid="collapsedControl"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    logo_path = Path("assets/logo.png")

    col_logo, col_title = st.columns([1, 5])

    with col_logo:
        if logo_path.exists():
            st.markdown("<div style='margin-top:-18px;'>", unsafe_allow_html=True)
            st.image(str(logo_path), width=130)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_title:
        st.title("PENERA")
        st.markdown("### Pelayanan Elektronik Tera dan Tera Ulang")
        st.write("Aplikasi Pengujian UTTP")

    st.divider()

    st.subheader("Pengujian UTTP")
    st.write("Silakan pilih jenis UTTP yang akan diuji:")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("## ⚖️ Timbangan Jembatan")
            st.write("Output: Cerapan PDF dan Sertifikat PDF")
    
            if st.button("Masuk ke Timbangan Jembatan", use_container_width=True):
                st.session_state.halaman = "tj"
                st.rerun()
    
    with col2:
        with st.container(border=True):
            st.markdown("## ⛽ PUBBM")
            st.write("Output: Sertifikat PDF")
    
            if st.button("Masuk ke PUBBM", use_container_width=True):
                st.session_state.halaman = "pubbm"
                st.rerun()
    
    with col3:
        with st.container(border=True):
            st.markdown("## ⚡ kWh Meter")
            st.write("Output: Sertifikat PDF")
    
            if st.button("Masuk ke kWh Meter", use_container_width=True):
                st.session_state.halaman = "kwh"
                st.rerun()

    st.divider()
    st.caption("PENERA - Pengujian UTTP")


if st.session_state.halaman == "home":
    home()

elif st.session_state.halaman == "tj":
    from pages.timbangan_jembatan import run
    run()

elif st.session_state.halaman == "pubbm":
    from pages.pubbm import run
    run()

elif st.session_state.halaman == "kwh":
    from pages.kwh_meter import run
    run()
