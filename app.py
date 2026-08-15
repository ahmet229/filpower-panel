import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Filpower Akıllı Fiyatlandırma", layout="wide", page_icon="⚡")

st.title("⚡ Filpower Akıllı Fiyatlandırma & Kâr Paneli")

# Sol Yan Menü: Parametreler
st.sidebar.header("⚙️ Finansal Parametreler")
trendyol_komisyon = st.sidebar.slider("Trendyol Komisyonu (%)", 10, 25, 18) / 100
iyzico_pos = st.sidebar.slider("iyzico POS Oranı (%)", 1, 10, 7) / 100
fil_puan = st.sidebar.slider("Fil-Puan Bütçesi (%)", 1, 5, 3) / 100
hedef_kar = st.sidebar.slider("Hedef Kâr Marjı (%)", 10, 100, 20) / 100

tab1, tab2 = st.tabs(["🧮 Tekli Ürün Hesaplama", "📁 IdeaSoft Excel Toplu Hesaplama"])

# Metin içindeki Türkçe para formatını temizleme fonksiyonu
def fiyat_temizle(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().replace('TL', '').replace('₺', '').replace(' ', '')
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except:
        return 0.0

# --- TAB 1: TEKLİ HESAPLAMA ---
with tab1:
    st.subheader("📦 Tekli Ürün Veri Girişi")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        maliyet = st.number_input("Ürün Maliyeti (TL - KDV Dahil):", min_value=1.0, value=1000.0, step=50.0)
    with col_in2:
        kargo = st.number_input("Kargo Maliyeti (TL):", min_value=0.0, value=70.0, step=5.0)

    ty_fiyat = (maliyet + kargo) * (1 + hedef_kar) / (1 - trendyol_komisyon)
    ty_net_kar = ty_fiyat * (1 - trendyol_komisyon) - maliyet - kargo

    site_fiyat = ty_fiyat * 0.92
    site_pos_kesinti = site_fiyat * iyzico_pos
    site_puan_kesinti = site_fiyat * fil_puan
    site_net_kar = site_fiyat - site_pos_kesinti - site_puan_kesinti - maliyet - kargo

    st.markdown("---")
    col_out1, col_out2 = st.columns(2)
    with col_out1:
        st.info("### 🛒 Trendyol / Hepsiburada")
        st.metric("Önerilen Satış Fiyatı", f"{ty_fiyat:,.2f} TL")
        st.metric("Tahmini Net Kâr", f"{ty_net_kar:,.2f} TL")
    with col_out2:
        st.success("### 🌐 Filpower.com.tr (Kendi Siteniz)")
        st.metric("Önerilen Satış Fiyatı", f"{site_fiyat:,.2f} TL", delta=f"-{(ty_fiyat - site_fiyat):,.2f} TL Ucuz!")
        st.metric("Tahmini Net Kâr", f"{site_net_kar:,.2f} TL")

# --- TAB 2: EXCEL TOPLU HESAPLAMA ---
with tab2:
    st.subheader("📊 IdeaSoft Excel Dosyası Yükle")
    uploaded_file = st.file_uploader("IdeaSoft'tan indirdiğiniz XLS / XLSX dosyasını sürükleyin", type=["xls", "xlsx"])
    kargo_toplu = st.number_input("Ürün Başı Ortalama Kargo Maliyeti (TL):", min_value=0.0, value=70.0, step=5.0, key="kargo_toplu")

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            col_map = {}
            for col in df.columns:
                c_lower = str(col).lower()
                if "label" in c_lower or "adı" in c_lower or "title" in c_lower:
                    col_map["ad"] = col
                elif "buyingprice" in c_lower or "alış" in c_lower or "maliyet" in c_lower or "price" in c_lower:
                    if "maliyet" not in col_map:
                        col_map["maliyet"] = col
                elif "ean" in c_lower or "barkod" in c_lower or "barcode" in c_lower:
                    col_map["barkod"] = col

            maliyet_col = col_map.get("maliyet")
            
            if maliyet_col:
                # Sayısal Temizleme
                df["Ürün Maliyeti"] = df[maliyet_col].apply(fiyat_temizle)
                
                # Hesaplama Algoritmaları
                df["Trendyol Satış Fiyatı"] = (df["Ürün Maliyeti"] + kargo_toplu) * (1 + hedef_kar) / (1 - trendyol_komisyon)
                df["Trendyol Net Kâr"] = df["Trendyol Satış Fiyatı"] * (1 - trendyol_komisyon) - df["Ürün Maliyeti"] - kargo_toplu
                
                df["Site Satış Fiyatı"] = df["Trendyol Satış Fiyatı"] * 0.92
                df["Site Net Kâr"] = df["Site Satış Fiyatı"] - (df["Site Satış Fiyatı"] * iyzico_pos) - (df["Site Satış Fiyatı"] * fil_puan) - df["Ürün Maliyeti"] - kargo_toplu

                # Formatlama
                df["Trendyol Satış Fiyatı"] = df["Trendyol Satış Fiyatı"].round(2)
                df["Trendyol Net Kâr"] = df["Trendyol Net Kâr"].round(2)
                df["Site Satış Fiyatı"] = df["Site Satış Fiyatı"].round(2)
                df["Site Net Kâr"] = df["Site Net Kâr"].round(2)

                st.success(f"✅ Toplam {len(df)} ürün başarıyla hesaplandı!")
                
                show_cols = []
                if "ad" in col_map: show_cols.append(col_map["ad"])
                if "barkod" in col_map: show_cols.append(col_map["barkod"])
                show_cols.extend(["Ürün Maliyeti", "Trendyol Satış Fiyatı", "Trendyol Net Kâr", "Site Satış Fiyatı", "Site Net Kâr"])
                
                st.dataframe(df[show_cols], use_container_width=True)
            else:
                st.error("❌ Excel dosyasında 'Alış Fiyatı' sütunu tespit edilemedi.")
        except Exception as e:
            st.error(f"Dosya okuma hatası: {e}")
