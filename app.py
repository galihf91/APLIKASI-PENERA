import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="PENERA - Pengujian UTTP",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# =========================
# HAPUS / SEMBUNYIKAN SIDEBAR
# =========================
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="collapsedControl"] {
            display: none;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }

        .stApp {
            margin-left: 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)
logo_path = Path("assets/logo.png")

col_logo, col_title = st.columns([1, 5])

with col_logo:
    if logo_path.exists():
        st.markdown("<div style='margin-top:-8px;'>", unsafe_allow_html=True)
        st.image(str(logo_path), width=130)
        st.markdown("</div>", unsafe_allow_html=True)

with col_title:
    st.title("PENERA")
    st.markdown("### Pelayanan Elektronik Tera dan Tera Ulang")
    st.write("Aplikasi Pengujian UTTP")

st.divider()

st.subheader("Pengujian UTTP")
st.write("Silakan pilih jenis UTTP yang akan diuji:")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("## ⚖️ Timbangan Jembatan")
        st.write(
            "Aplikasi pengujian Timbangan Jembatan "
            "dengan output Cerapan PDF dan Sertifikat PDF."
        )

        if st.button("Masuk ke Timbangan Jembatan", use_container_width=True):
            st.switch_page("pages/1_timbangan_jembatan.py")

with col2:
    with st.container(border=True):
        st.markdown("## ⛽ PUBBM")
        st.write(
            "Aplikasi pengujian Pompa Ukur BBM "
            "dengan output Sertifikat PDF."
        )

        if st.button("Masuk ke PUBBM", use_container_width=True):
            st.switch_page("pages/2_pubbm.py")

st.divider()

st.caption("PENERA - Pengujian UTTP")
