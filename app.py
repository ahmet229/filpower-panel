import os
import re
import urllib.parse
import pandas as pd
import streamlit as st

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
    if pd.isna(val): return 0.0
    val_str = str(val).strip().replace('TL', '').replace('₺', '').replace(' ', '').replace('\xa0', '')
    if not val_str: return 0.0
    if '.' in val_str and ',' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

def trendyol_link_olustur(row, col_ad, col_barkod, mod):
    barkod = str(row[col_barkod]).strip() if pd.notna(row[col_barkod]) and str(row[col_barkod]).strip().lower() not in ['none', 'nan', '0'] else ''
    ad = str(row[col_ad]).strip() if pd.notna(row[col_ad]) else ''
    ad_temiz = re.sub(r'SKU:.*', '', ad, flags=re.IGNORECASE).strip()
    
    if mod == 'Sadece Ürün Adı İle': sorgu = ad_temiz
    elif mod == 'Sadece Barkod İle': sorgu = barkod
    else:
        if len(barkod) >= 12 and barkod.isdigit(): sorgu = barkod
        else: sorgu = ad_temiz
    if not sorgu: return ''
    return f'https://www.trendyol.com/sr?q={urllib.parse.quote(sorgu)}'

# --- TAB 1: TEKLİ HESAPLAMA ---
with tab1:
    st.subheader('📦 Tekli Ürün Veri Girişi')
    col_in1, col_in2 = st.columns(2)
    with col_in1: maliyet = st.number_input('Ürün Maliyeti (TL - KDV Dahil):', min_value=1.0, value=1000.0, step=50.0)
    with col_in2: kargo = st.number_input('Kargo Maliyeti (TL):', min_value=0.0, value=70.0, step=5.0)

    ty_fiyat = (maliyet + kargo) * (1 + hedef_kar) / (1 - trendyol_komisyon)
    ty_net_kar = ty_fiyat * (1 - trendyol_komisyon) - maliyet - kargo
    site_fiyat = ty_fiyat * 0.92
    site_pos_kesinti = site_fiyat * iyzico_pos
    site_puan_kesinti = site_fiyat * fil_puan
    site_net_kar = site_fiyat - site_pos_kesinti - site_puan_kesinti - maliyet - kargo

    st.markdown('---')
    col_out1, col_out2 = st.columns(2)
    with col_out1:
        st.info('### 🛒 Trendyol / Hepsiburada')
        st.metric('Önerilen Satış Fiyatı', f'{ty_fiyat:,.2f} TL')
        st.metric('Tahmini Net Kâr', f'{ty_net_kar:,.2f} TL')
    with col_out2:
        st.success('### 🌐 Filpower.com.tr (Kendi Siteniz)')
        st.metric('Önerilen Satış Fiyatı', f'{site_fiyat:,.2f} TL', delta=f'-{(ty_fiyat - site_fiyat):,.2f} TL Ucuz!')
        st.metric('Tahmini Net Kâr', f'{site_net_kar:,.2f} TL')

# --- TAB 2: EXCEL TOPLU HESAPLAMA ---
with tab2:
    st.subheader('📊 IdeaSoft Ürün Listesi')

    existing_default = None
    for file in os.listdir('.'):
        if file.endswith('.xls') or file.endswith('.xlsx'):
            existing_default = file
            break

    uploaded_file = st.file_uploader('Farklı bir dosya yüklemek isterseniz buraya sürükleyin', type=['xls', 'xlsx'])
    kargo_toplu = st.number_input('Ürün Başı Ortalama Kargo Maliyeti (TL):', min_value=0.0, value=120.0, step=5.0, key='kargo_toplu')

    target_file = None
    if uploaded_file is not None:
        target_file = uploaded_file
    elif existing_default is not None:
        target_file = existing_default
        st.info(f'📌 Kalıcı dosya devrede: **{existing_default}** (Her girişte otomatik hesaplanır)')

    if target_file is not None:
        try:
            df = pd.read_excel(target_file)
            cols_list = list(df.columns)

            def_ad_idx, def_maliyet_idx, def_barkod_idx = 0, 0, 0
            for idx, col in enumerate(cols_list):
                col_lower = str(col).lower()
                if 'label' in col_lower or 'ürün adı' in col_lower: def_ad_idx = idx
                elif any(x in col_lower for x in ['pricewithtax', 'buyingprice', 'maliyet', 'alış']): def_maliyet_idx = idx
                elif 'barcode' in col_lower or 'barkod' in col_lower: def_barkod_idx = idx

            st.markdown('---')
            with st.expander('🛠️ Sütun ve Arama Ayarlarını Değiştir (İsteğe Bağlı)'):
                c1, c2, c3, c4 = st.columns(4)
                with c1: sel_ad = st.selectbox('Ürün Adı Sütunu:', cols_list, index=def_ad_idx)
                with c2: sel_maliyet = st.selectbox('Alış Fiyatı / Maliyet Sütunu:', cols_list, index=def_maliyet_idx)
                with c3: sel_barkod = st.selectbox('Barkod Sütunu:', cols_list, index=def_barkod_idx)
                with c4: arama_modu = st.selectbox('Trendyol Arama Tipi:', ['Otomatik (Akıllı)', 'Sadece Ürün Adı İle', 'Sadece Barkod İle'])
            st.markdown('---')

            # Canlı Maliyet Değişimini Hafızada Tutma
            file_key = f"{getattr(target_file, 'name', target_file)}_{sel_maliyet}"
            if st.session_state.get("file_key") != file_key or "user_maliyetler" not in st.session_state:
                st.session_state["file_key"] = file_key
                st.session_state["user_maliyetler"] = df[sel_maliyet].apply(fiyat_temizle).values

            # Hesaplama Tablosu
            calc_df = pd.DataFrame()
            calc_df['Ürün Adı'] = df[sel_ad]
            calc_df['Barkod'] = df[sel_barkod]
            calc_df['Ürün Maliyeti'] = st.session_state["user_maliyetler"]

            calc_df['Trendyol Satış Fiyatı'] = (calc_df['Ürün Maliyeti'] + kargo_toplu) * (1 + hedef_kar) / (1 - trendyol_komisyon)
            calc_df['Trendyol Net Kâr'] = calc_df['Trendyol Satış Fiyatı'] * (1 - trendyol_komisyon) - calc_df['Ürün Maliyeti'] - kargo_toplu
            calc_df['Site Satış Fiyatı'] = calc_df['Trendyol Satış Fiyatı'] * 0.92
            calc_df['Site Net Kâr'] = calc_df['Site Satış Fiyatı'] - (calc_df['Site Satış Fiyatı'] * iyzico_pos) - (calc_df['Site Satış Fiyatı'] * fil_puan) - calc_df['Ürün Maliyeti'] - kargo_toplu

            calc_df["Trendyol'da İncele"] = df.apply(lambda r: trendyol_link_olustur(r, sel_ad, sel_barkod, arama_modu), axis=1)

            calc_df['Ürün Maliyeti'] = calc_df['Ürün Maliyeti'].round(2)
            calc_df['Trendyol Satış Fiyatı'] = calc_df['Trendyol Satış Fiyatı'].round(2)
            calc_df['Trendyol Net Kâr'] = calc_df['Trendyol Net Kâr'].round(2)
            calc_df['Site Satış Fiyatı'] = calc_df['Site Satış Fiyatı'].round(2)
            calc_df['Site Net Kâr'] = calc_df['Site Net Kâr'].round(2)

            st.caption("💡 **Aşağıdaki tablodan 'Ürün Maliyeti' hücresine çift tıklayıp fiyat yazabilirsiniz. Tüm satış fiyatları ve kârlar anında yenilenir:**")

            edited_df = st.data_editor(
                calc_df,
                column_config={
                    "Ürün Adı": st.column_config.Column(disabled=True),
                    "Barkod": st.column_config.Column(disabled=True),
                    "Ürün Maliyeti": st.column_config.NumberColumn("Ürün Maliyeti (TL)", min_value=0.0, step=10.0, format="%.2f TL"),
                    "Trendyol Satış Fiyatı": st.column_config.NumberColumn(disabled=True, format="%.2f TL"),
                    "Trendyol Net Kâr": st.column_config.NumberColumn(disabled=True, format="%.2f TL"),
                    "Site Satış Fiyatı": st.column_config.NumberColumn(disabled=True, format="%.2f TL"),
                    "Site Net Kâr": st.column_config.NumberColumn(disabled=True, format="%.2f TL"),
                    "Trendyol'da İncele": st.column_config.LinkColumn('Trendyol Canlı Arama', display_text="🔍 Trendyol'da Gör")
                },
                use_container_width=True,
                key="canli_maliyet_editor"
            )

            # Hücre değiştiğinde anında tekrar hesapla
            if not edited_df['Ürün Maliyeti'].equals(pd.Series(st.session_state["user_maliyetler"])):
                st.session_state["user_maliyetler"] = edited_df['Ürün Maliyeti'].values
                st.rerun()

        except Exception as e:
            st.error(f'Dosya işleme hatası: {e}')
