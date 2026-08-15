import streamlit as st

st.set_page_config(page_title="Filpower Fiyatlandırma Paneli", layout="wide", page_icon="⚡")

st.title("⚡ Filpower Akıllı Fiyatlandırma & Kâr Paneli")
st.write("Maliyetlerinizi girin, sistem sizin için en doğru site ve pazaryeri fiyatını hesaplasın.")

# Sol Yan Menü: Parametreler
st.sidebar.header("⚙️ Finansal Parametreler")
trendyol_komisyon = st.sidebar.slider("Trendyol Komisyonu (%)", 10, 25, 18) / 100
iyzico_pos = st.sidebar.slider("iyzico POS Oranı (%)", 1, 10, 7) / 100
fil_puan = st.sidebar.slider("Fil-Puan Bütçesi (%)", 1, 5, 3) / 100
hedef_kar = st.sidebar.slider("Hedef Kâr Marjı (%)", 10, 50, 20) / 100

# Ana Ekran: Ürün Veri Girişi
st.subheader("📦 Ürün Bilgileri")
col_in1, col_in2 = st.columns(2)

with col_in1:
    maliyet = st.number_input("Ürün Maliyeti (TL - KDV Dahil):", min_value=1.0, value=1000.0, step=50.0)
with col_in2:
    kargo = st.number_input("Kargo Maliyeti (TL):", min_value=0.0, value=70.0, step=5.0)

# Fiyat Hesaplama Algoritması
# 1. Trendyol Satış Fiyatı
ty_fiyat = (maliyet + kargo) * (1 + hedef_kar) / (1 - trendyol_komisyon)
ty_net_kar = ty_fiyat * (1 - trendyol_komisyon) - maliyet - kargo

# 2. Filpower.com.tr Satış Fiyatı (Trendyol'dan %8 Ucuz + Taksitli)
site_fiyat = ty_fiyat * 0.92
site_pos_kesinti = site_fiyat * iyzico_pos
site_puan_kesinti = site_fiyat * fil_puan
site_net_kar = site_fiyat - site_pos_kesinti - site_puan_kesinti - maliyet - kargo

st.markdown("---")

# Sonuç Ekranı
st.subheader("📊 Önerilen Satış Fiyatları ve Kâr Analizi")
col_out1, col_out2 = st.columns(2)

with col_out1:
    st.info("### 🛒 Trendyol / Hepsiburada")
    st.metric("Önerilen Satış Fiyatı", f"{ty_fiyat:,.2f} TL")
    st.metric("Tahmini Net Kâr", f"{ty_net_kar:,.2f} TL")
    st.caption("⏳ Tahsilat Süresi: **30 - 45 Gün**")

with col_out2:
    st.success("### 🌐 Filpower.com.tr (Kendi Siteniz)")
    st.metric("Önerilen Satış Fiyatı", f"{site_fiyat:,.2f} TL", delta=f"-{(ty_fiyat - site_fiyat):,.2f} TL Ucuz!")
    st.metric("Tahmini Net Kâr", f"{site_net_kar:,.2f} TL")
    st.caption("🚀 Tahsilat Süresi: **ERTESİ GÜN NAKİT**")
