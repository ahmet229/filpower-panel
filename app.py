import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Filpower Akıllı Fiyatlandırma", layout="wide", page_icon="⚡")

st.title("⚡ Filpower Akıllı Fiyatlandırma & Kâr Paneli")

# Sol Yan Menü: Parametreler
st.sidebar.header("⚙️ Finansal Parametreler")
trendyol_komisyon = st.sidebar.slider("Trendyol Komisyonu (%)", 10, 25, 18) / 100
iyzico_pos = st.sidebar.slider("iyzico POS Oranı (%)", 1, 10, 7) / 100
fil_puan = st.sidebar.slider("Fil-Puan Bütçesi (%)", 1, 5, 3) / 100
hedef_kar = st.sidebar.slider("Hedef Kâr Marjı (%)", 10, 100, 20) / 100

tab1, tab2 = st.tabs(["🧮 Tekli Ürün Hesaplama", "📁 IdeaSoft Excel Toplu Hesaplama"])

def fiyat_temizle(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().replace('TL', '').replace('₺', '').replace(' ', '').replace('\xa0', '')
    if not val_str:
        return 0.0
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except:
        return 0.0

def trendyol_link_olustur(row, col_ad, col_barkod):
    barkod = str(row[col_barkod]).strip() if pd.notna(row[col_barkod]) and str(row[col_barkod]).strip().lower() != 'none' else ""
    ad = str(row[col_ad]).strip() if pd.notna(row[col_ad]) else ""
    
    sorgu = barkod if (barkod and len(barkod) > 3) else ad
    if not sorgu:
        return ""
    return f"https://www.trendyol.com/sr?q={urllib.parse.quote(sorgu)}"

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
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            row0_is_header = False
            sample_headers = ["label", "buyingprice", "barcode", "eans", "stockcode", "price", "maliyet", "barkod", "ürün adı"]
            first_row_str = " ".join([str(x).lower() for x in df_raw.iloc[0].values])
            if any(h in first_row_str for h in sample_headers):
                row0_is_header = True

            if row0_is_header:
                df = pd.read_excel(uploaded_file)
            else:
                df = df_raw.copy()
                df.columns = [f"Sütun {i+1} (Örn: {df_raw.iloc[0, i]})" for i in range(len(df_raw.columns))]

            st.markdown("---")
            st.markdown("### 🛠️ Sütun Eşleştirme")
            
            cols_list = list(df.columns)
            
            default_ad = 1 if len(cols_list) > 1 else 0
            default_maliyet = 2 if len(cols_list) > 2 else 0
            default_barkod = 6 if len(cols_list) > 6 else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                sel_ad = st.selectbox("Ürün Adı Sütunu:", cols_list, index=default_ad)
            with c2:
                sel_maliyet = st.selectbox("Alış Fiyatı / Maliyet Sütunu:", cols_list, index=default_maliyet)
            with c3:
                sel_barkod = st.selectbox("Barkod Sütunu:", cols_list, index=default_barkod)

            calc_df = pd.DataFrame()
            calc_df["Ürün Adı"] = df[sel_ad]
            calc_df["Barkod"] = df[sel_barkod]
            calc_df["Ürün Maliyeti"] = df[sel_maliyet].apply(fiyat_temizle)
            
            calc_df["Trendyol Satış Fiyatı"] = (calc_df["Ürün Maliyeti"] + kargo_toplu) * (1 + hedef_kar) / (1 - trendyol_komisyon)
            calc_df["Trendyol Net Kâr"] = calc_df["Trendyol Satış Fiyatı"] * (1 - trendyol_komisyon) - calc_df["Ürün Maliyeti"] - kargo_toplu
            
            calc_df["Site Satış Fiyatı"] = calc_df["Trendyol Satış Fiyatı"] * 0.92
            calc_df["Site Net Kâr"] = calc_df["Site Satış Fiyatı"] - (calc_df["Site Satış Fiyatı"] * iyzico_pos) - (calc_df["Site Satış Fiyatı"] * fil_puan) - calc_df["Ürün Maliyeti"] - kargo_toplu

            # Trendyol Canlı Arama Linki
            calc_df["Trendyol'da İncele"] = df.apply(lambda r: trendyol_link_olustur(r, sel_ad, sel_barkod), axis=1)

            calc_df["Ürün Maliyeti"] = calc_df["Ürün Maliyeti"].round(2)
            calc_df["Trendyol Satış Fiyatı"] = calc_df["Trendyol Satış Fiyatı"].round(2)
            calc_df["Trendyol Net Kâr"] = calc_df["Trendyol Net Kâr"].round(2)
            calc_df["Site Satış Fiyatı"] = calc_df["Site Satış Fiyatı"].round(2)
            calc_df["Site Net Kâr"] = calc_df["Site Net Kâr"].round(2)

            st.markdown("---")
            st.success(f"✅ Toplam {len(calc_df)} ürün başarıyla hesaplandı!")
            
            st.dataframe(
                calc_df,
                column_config={
                    "Trendyol'da İncele": st.column_config.LinkColumn(
                        "Trendyol Canlı Arama",
                        display_text="🔍 Trendyol'da Gör"
                    )
                },
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Dosya işleme hatası: {e}")
