import streamlit as st
import json
import numpy as np
import colour
import itertools
import pandas as pd
from scipy.optimize import minimize, nnls
from scipy.interpolate import PchipInterpolator
import base64
import os
import re
import pyperclip

# ==========================================
# 0. 다국어 지원 (번역 딕셔너리 및 함수)
# ==========================================
LANG_DICT = {
    "title_disp": {"ko": "백포 선택 (Disperse)", "en": "Select Blank (Disperse)"},
    "desc_disp": {"ko": "분산염료처방 탐색에 사용할 백포를 선택해주세요.", "en": "Please select the blank for Disperse dye recipe search."},
    "confirm": {"ko": "확인", "en": "Confirm"},
    "company_all": {"ko": "전체 보기", "en": "All Companies"},
    "company_sel": {"ko": "업체 선택", "en": "Select Company"},
    "dye_list": {"ko": "염료 리스트", "en": "Dye List"},
    "click_guide": {"ko": "클릭하여 선택 / 해제하세요.", "en": "Click to select / deselect."},
    "paste_ph": {"ko": "복사한 텍스트를 붙여넣으세요 (Ctrl+V)", "en": "Paste copied text here (Ctrl+V)"},
    "load_ohyoung": {"ko": "Ohyoung Dye Finder에서 불러오기", "en": "Load from Ohyoung Dye Finder"},
    "search_dye": {"ko": "염료 검색", "en": "Search Dye"},
    "search_ph": {"ko": "검색어 입력 후 Enter ↵", "en": "Type and press Enter ↵"},
    "reset": {"ko": "초기화", "en": "Reset"},
    "step1_title": {"ko": "Step 1. 타겟 색상 업로드 (QTX)", "en": "Step 1. Upload Target Color (QTX)"},
    "upload_qtx": {"ko": "QTX 파일 업로드", "en": "Upload QTX File"},
    "target_sel": {"ko": "타겟 색상 선택", "en": "Select Target Color"},
    "preview_wait": {"ko": "미리보기 대기중", "en": "Waiting for Preview"},
    "step2_title": {"ko": "Step 2. 검색 옵션 설정", "en": "Step 2. Search Options"},
    "auto_brand": {"ko": "브랜드별 광원 자동 세팅", "en": "Auto Light Setting by Brand"},
    "auto_brand_desc": {"ko": "브랜드를 선택하면 광원이 자동으로 지정됩니다.", "en": "Lights are auto-set when a brand is selected."},
    "light_detail": {"ko": "광원 세부 설정 (수정 가능)", "en": "Light Details (Editable)"},
    "light_1": {"ko": "1차 광원", "en": "1st Light"},
    "light_2": {"ko": "2차 광원", "en": "2nd Light"},
    "light_3": {"ko": "3차 광원", "en": "3rd Light"},
    "step3_title": {"ko": "Step 3. 실행 및 상태", "en": "Step 3. Execution & Status"},
    "selected_count": {"ko": "현재 사이드바에서 선택된 염료: **{count}개**", "en": "Currently selected dyes: **{count}**"},
    "clear_all": {"ko": "선택 전체 초기화", "en": "Clear All Selections"},
    "btn_need_qtx": {"ko": "처방 탐색 시작 (QTX 업로드 필요)", "en": "Start Search (Upload QTX First)"},
    "btn_need_dye": {"ko": "처방 탐색 시작 (염료 1개 이상 선택 필요)", "en": "Start Search (Select 1+ Dye)"},
    "btn_start": {"ko": "처방 탐색 시작", "en": "Start Recipe Search"},
    "result_title": {"ko": "처방 탐색 결과", "en": "Recipe Search Results"},
    "finding": {"ko": "최적의 염료를 찾고있습니다..", "en": "Finding the optimal dyes.."},
    "finding_desc": {"ko": "조합을 탐색하고 정밀 분석을 수행하는 중입니다.<br>화면이 멈춘 것이 아니니 잠시만 기다려주세요.", "en": "Searching combinations and performing precise analysis.<br>Please wait, the screen is not frozen."},
    "fastness_title": {"ko": "탐색된 처방 예상 견뢰도 분석", "en": "Predicted Fastness Analysis"},
    "fastness_sel": {"ko": "견뢰도를 확인할 처방 순위 선택:", "en": "Select recipe rank to check fastness:"},
    "fastness_desc": {"ko": "※ S/D 1/1 대비 농도 패널티 반영 수치입니다.", "en": "※ Fastness is adjusted based on concentration vs S/D 1/1."},
    "req_target": {"ko": "좌측 패널에서 타겟 색상을 업로드하고 처방 탐색을 시작해주세요.", "en": "Please upload a target color and start the search."},
    "no_recipe": {"ko": "유효한 처방을 찾지 못했습니다.", "en": "No valid recipe found."},
    "missing_dyes": {"ko": "데이터 부족으로 제외된 염료 {count}개:\n{dyes}", "en": "{count} dyes excluded due to missing data:\n{dyes}"},
    "success_add": {"ko": "성공적으로 {count}개의 염료를 추가했습니다!", "en": "Successfully added {count} dyes!"},
    "fail_add": {"ko": "추가할 수 있는 새로운 염료가 없습니다 (이미 있거나 매칭 실패).", "en": "No new dyes to add (already exist or matching failed)."},
    "warn_paste": {"ko": "먼저 텍스트창에 복사한 내용을 붙여넣어 주세요.", "en": "Please paste text in the input box first."},
    "target_found": {"ko": "인식된 타겟: **{name}**", "en": "Recognized Target: **{name}**"},
    "qtx_error": {"ko": "QTX 파일에서 데이터를 찾을 수 없습니다.", "en": "No data found in the QTX file."},
    "qtx_parse_error": {"ko": "QTX 분석 오류: {e}", "en": "QTX Parse Error: {e}"}
}

if "lang" not in st.session_state:
    st.session_state.lang = "ko"

def t(key, **kwargs):
    text = LANG_DICT.get(key, {}).get(st.session_state.lang, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def set_lang(lang_code):
    st.session_state.lang = lang_code

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="T/S Colordata", page_icon="logo.png")

# ==========================================
# 1. 세션 상태 초기화
# ==========================================
if "dye_mode" not in st.session_state: st.session_state.dye_mode = "Reactive"
if "disperse_sub" not in st.session_state: st.session_state.disperse_sub = "Jersey"
if "selected_dyes" not in st.session_state: st.session_state.selected_dyes = []
if "top_results" not in st.session_state: st.session_state.top_results = None
if "qtx_filename" not in st.session_state: st.session_state.qtx_filename = ""
if "qtx_excel_color" not in st.session_state: st.session_state.qtx_excel_color = 14211288
if "brand_selector" not in st.session_state: st.session_state.brand_selector = "직접 선택 (Manual)"
if "l1" not in st.session_state: st.session_state.l1 = "D65"
if "l2" not in st.session_state: st.session_state.l2 = "없음"
if "l3" not in st.session_state: st.session_state.l3 = "없음"

def set_dye_mode(mode):
    if st.session_state.dye_mode != mode:
        st.session_state.dye_mode = mode
        st.session_state.selected_dyes = []
        st.session_state.top_results = None

def toggle_dye(raw_name):
    if raw_name in st.session_state.selected_dyes: st.session_state.selected_dyes.remove(raw_name)
    else: st.session_state.selected_dyes.append(raw_name)

def clear_dyes(): st.session_state.selected_dyes = []
dye_mode = st.session_state.dye_mode

# ==========================================
# 2. 공통 UI 스타일 및 상단 고정 헤더 구성
# ==========================================
try:
    with open("logo.png", "rb") as image_file: logo_base64 = base64.b64encode(image_file.read()).decode()
except Exception: logo_base64 = ""

header_mode_text = dye_mode
if dye_mode == "Disperse": header_mode_text += f" - {st.session_state.disperse_sub}"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
<style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    .stApp {{ opacity: 1 !important; filter: none !important; }}
    [data-testid="stAppViewBlockContainer"] {{ opacity: 1 !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    
    .fixed-header {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 60px;
        background-color: #ffffff; box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
        z-index: 999998; display: flex; align-items: center;
        padding-left: 20px; border-bottom: 1px solid #eaeaea;
    }}
    .fixed-header img {{ width: 45px; margin-right: 12px; }}
    .fixed-header h2 {{ margin: 0; padding: 0; font-size: 24px; font-weight: 700; color: #31333F; }}
    
    .block-container {{ padding-top: 80px !important; }}
    .material-symbols-outlined {{ line-height: 1 !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    [data-testid="stSidebar"] div.stButton {{ margin-bottom: -10px; }}

    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) {{
        position: fixed !important; top: 10px !important; 
        left: 360px !important; right: 20px !important; width: auto !important; 
        z-index: 999999 !important; align-items: center !important; 
    }}
    div.element-container:has(#top-menu-marker) {{
        display: none !important; margin: 0 !important; padding: 0 !important; height: 0 !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) div[data-baseweb="select"] {{
        border: none !important; background-color: transparent !important; box-shadow: none !important; cursor: pointer;
    }}
    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) div[data-baseweb="select"] > div {{
        border: none !important; background-color: transparent !important; padding-left: 8px; padding-right: 8px;
    }}
    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) div[data-baseweb="select"] * {{
        color: #1f325c !important; font-weight: 700 !important; font-size: 15px !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) div[data-baseweb="select"]:hover {{
        background-color: rgba(0,0,0,0.04) !important; border-radius: 6px;
    }}
    div[data-testid="stHorizontalBlock"]:has(#top-menu-marker) div.stButton > button {{
        border-radius: 8px; padding: 0px 10px; height: 38px; min-height: 38px; margin: 0 !important; 
    }}
</style>
<div class="fixed-header">
    <img src="data:image/png;base64,{logo_base64}" onerror="this.style.display='none'">
    <h2>T/S Colordata <span style="font-size: 16px; color: #666;">({header_mode_text})</span></h2>
</div>
""", unsafe_allow_html=True)

# ==========================================
# [데이터 로드] 브랜드 및 광원 매핑
# ==========================================
@st.cache_data
def load_brand_ill():
    try:
        df = pd.read_excel('brand ill.xlsx', header=None)
        df.columns = ['Brand', 'Light1', 'Light2', 'Light3']
        return df
    except Exception:
        return pd.DataFrame(columns=['Brand', 'Light1', 'Light2', 'Light3'])

brand_df = load_brand_ill()

def map_light_name(brand_light_str):
    if pd.isna(brand_light_str): return "없음"
    s = str(brand_light_str).strip().upper()
    if "D65" in s: return "D65"
    if "A" == s or "AEO" in s: return "A" 
    if "F02" in s or "CWF" in s: return "CWF (F02)"
    if "F11" in s or "TL84" in s: return "TL84 (F11)"
    if "TL83" in s: return "TL83"
    if "U30" in s: return "U3000 (F12)"
    if "U35" in s: return "U3500"
    if "LED35" in s: return "LED35K"
    if "LED_B1" in s or "B1" in s: return "LED_B1"
    if "LED_T8G" in s or "T8G" in s: return "LED_T8G"
    return "없음"

def on_brand_change():
    selected_brand = st.session_state.brand_selector
    if selected_brand != "직접 선택 (Manual)":
        brand_row = brand_df[brand_df['Brand'] == selected_brand].iloc[0]
        l1 = map_light_name(brand_row['Light1'])
        l2 = map_light_name(brand_row['Light2'])
        l3 = map_light_name(brand_row['Light3'])
        if l1 == "없음": l1 = "D65"
        st.session_state.l1 = l1
        st.session_state.l2 = l2
        st.session_state.l3 = l3

def apply_dc_correction(light_name, de_val):
    if "TL84" in light_name:
        if de_val <= 2.0: return max(0.01, -0.1226 * (de_val**2) + 0.6539 * de_val + 0.1873)
        else: return max(0.01, 1.0047 + 0.1635 * (de_val - 2.0))
    return de_val

# ==========================================
# 4. 데이터 및 염료 매핑 로드
# ==========================================
@st.cache_data
def load_dye_data(mode):
    file_map = {"Reactive": 'dye_data.json', "Disperse": 'dye_data_disperse.json', "Reactive (CPB)": 'dye_data_cpb.json', "CDP": 'dye_data_CDP.json', "Acid": 'dye_data_acid.json'}
    file_name = file_map.get(mode, 'dye_data.json')
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            return {name.strip(): concs for name, concs in raw_data.items() if len(concs) > 0}
    except FileNotFoundError: return {}

@st.cache_data
def load_dye_mapping(mode, _valid_keys):
    file_map = {"Reactive": 'dye_list.xlsx', "Disperse": 'dis_dye_list.xlsx', "Reactive (CPB)": 'cpb_dye_list.xlsx', "CDP": 'CDP_dye_list.xlsx', "Acid": 'acid_dye_list.xlsx'}
    file_name = file_map.get(mode, 'dye_list.xlsx')
    try:
        df = pd.read_excel(file_name, header=None)
        mapping_list, disp_dict, missing_dyes, all_companies, sort_order_dict = [], {}, [], set(), {}
        for _, row in df.iterrows():
            try: sort_val = float(row[0]) if pd.notna(row[0]) else 999.0
            except: sort_val = 999.0
            raw_name, display_name = str(row[1]).strip(), str(row[2]).strip()
            companies = [str(row[i]).strip() for i in range(3, len(row)) if pd.notna(row[i]) and str(row[i]).strip()]
            all_companies.update(companies)
            if raw_name in _valid_keys:
                mapping_list.append((raw_name, display_name, companies))
                disp_dict[raw_name] = display_name
                sort_order_dict[raw_name] = sort_val
            else: missing_dyes.append(raw_name)
        return mapping_list, disp_dict, missing_dyes, sorted(list(all_companies)), sort_order_dict
    except Exception: return [(k, k, []) for k in sorted(list(_valid_keys))], {k: k for k in _valid_keys}, [], [], {}

dye_db = load_dye_data(dye_mode)
all_dyes_ordered, display_name_dict, missing_dyes, all_companies, sort_order_dict = load_dye_mapping(dye_mode, dye_db.keys())

# --- 스펙트럼/광원 데이터 (변경 없음) ---
wls_astm = np.arange(360, 790, 10)
astm_a_x_vals = [0.000, 0.000, 0.000, 0.002, 0.025, 0.134, 0.377, 0.686, 0.964, 1.080, 1.006, 0.731, 0.343, 0.078, 0.022, 0.218, 0.750, 1.642, 2.842, 4.336, 6.200, 8.262, 10.227, 11.945, 12.746, 12.337, 10.817, 8.560, 6.014, 3.887, 2.309, 1.276, 0.666, 0.336, 0.166, 0.082, 0.040, 0.020, 0.010, 0.005, 0.003, 0.001, 0.001]
astm_a_y_vals = [0.000, 0.000, 0.000, 0.000, 0.003, 0.014, 0.039, 0.084, 0.156, 0.259, 0.424, 0.696, 1.082, 1.616, 2.422, 3.529, 4.840, 6.100, 7.250, 8.114, 8.758, 8.988, 8.760, 8.304, 7.468, 6.323, 5.033, 3.744, 2.506, 1.560, 0.911, 0.499, 0.259, 0.130, 0.065, 0.032, 0.016, 0.008, 0.004, 0.002, 0.001, 0.001, 0.000]
astm_a_z_vals = [0.000, 0.000, 0.000, 0.008, 0.110, 0.615, 1.792, 3.386, 4.944, 5.806, 5.812, 4.919, 3.300, 1.973, 1.152, 0.658, 0.382, 0.211, 0.102, 0.032, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_a_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_a_x_vals) / 100.0)), name='ASTM_A_X')
custom_a_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_a_y_vals) / 100.0)), name='ASTM_A_Y')
custom_a_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_a_z_vals) / 100.0)), name='ASTM_A_Z')

astm_d65_x_vals = [0.000, 0.000, 0.001, 0.005, 0.097, 0.616, 1.660, 2.377, 3.512, 3.789, 3.103, 1.937, 0.747, 0.110, 0.007, 0.314, 1.027, 2.174, 3.380, 4.735, 6.081, 7.310, 8.393, 8.603, 8.771, 7.996, 6.476, 4.635, 3.074, 1.814, 1.031, 0.557, 0.261, 0.114, 0.057, 0.028, 0.011, 0.006, 0.003, 0.001, 0.000, 0.000, 0.000]
astm_d65_y_vals = [0.000, 0.000, 0.000, 0.000, 0.010, 0.064, 0.171, 0.283, 0.549, 0.888, 1.277, 1.817, 2.545, 3.164, 4.309, 5.631, 6.896, 8.136, 8.684, 8.903, 8.614, 7.950, 7.164, 5.945, 5.110, 4.067, 2.990, 2.020, 1.275, 0.724, 0.407, 0.218, 0.102, 0.044, 0.022, 0.011, 0.004, 0.002, 0.001, 0.000, 0.000, 0.000, 0.000]
astm_d65_z_vals = [0.000, -0.001, 0.004, 0.020, 0.436, 2.808, 7.868, 11.703, 17.958, 20.358, 17.861, 13.085, 7.510, 3.743, 2.003, 1.004, 0.529, 0.271, 0.116, 0.030, -0.003, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_d65_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_d65_x_vals) / 100.0)), name='ASTM_D65_X')
custom_d65_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_d65_y_vals) / 100.0)), name='ASTM_D65_Y')
custom_d65_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_d65_z_vals) / 100.0)), name='ASTM_D65_Z')

astm_tl84_x_vals = [0.000, 0.000, 0.000, -0.010, 0.099, 0.182, 0.098, 2.796, 4.103, 1.534, 1.314, 0.681, 0.343, 0.176, 0.009, 0.034, 0.005, -0.145, 10.852, 12.320, 1.096, 1.157, 7.036, 8.982, 6.204, 26.264, 13.228, 3.797, 0.794, 0.481, 0.264, 0.084, 0.038, 0.023, 0.011, 0.014, 0.002, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_tl84_y_vals = [0.000, 0.000, 0.000, -0.001, 0.010, 0.019, 0.003, 0.372, 0.625, 0.388, 0.554, 0.578, 1.380, 2.955, 1.506, 0.564, 0.257, 0.170, 25.656, 24.661, 1.274, 1.214, 5.881, 6.382, 3.629, 13.321, 6.279, 1.631, 0.329, 0.192, 0.104, 0.033, 0.015, 0.009, 0.004, 0.005, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_tl84_z_vals = [0.000, 0.000, 0.000, -0.044, 0.451, 0.829, 0.415, 13.964, 20.873, 8.310, 7.586, 4.498, 3.625, 3.789, 0.773, 0.074, 0.028, 0.027, 0.293, 0.148, -0.010, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_tl84_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_tl84_x_vals) / 100.0)), name='ASTM_TL84_X')
custom_tl84_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_tl84_y_vals) / 100.0)), name='ASTM_TL84_Y')
custom_tl84_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_tl84_z_vals) / 100.0)), name='ASTM_TL84_Z')

astm_f02_x_vals = [0.000, 0.000, 0.001, -0.009, 0.133, 0.311, 0.310, 2.977, 4.074, 1.393, 1.402, 0.946, 0.401, 0.081, 0.019, 0.169, 0.543, 1.093, 3.562, 6.166, 7.209, 10.967, 14.182, 13.453, 11.997, 9.183, 6.075, 3.517, 1.767, 0.808, 0.339, 0.133, 0.049, 0.019, 0.007, 0.003, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_f02_y_vals = [0.000, 0.000, 0.000, -0.001, 0.014, 0.032, 0.025, 0.395, 0.617, 0.354, 0.593, 0.900, 1.261, 1.671, 2.165, 2.764, 3.517, 4.262, 8.685, 11.838, 10.117, 11.867, 12.191, 9.357, 7.032, 4.707, 2.825, 1.537, 0.736, 0.324, 0.134, 0.052, 0.019, 0.007, 0.003, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_f02_z_vals = [0.000, 0.000, -0.001, -0.041, 0.603, 1.425, 1.418, 14.861, 20.711, 7.553, 8.103, 6.363, 3.852, 2.039, 1.030, 0.515, 0.277, 0.154, 0.107, 0.055, -0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_f02_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_f02_x_vals) / 100.0)), name='ASTM_F02_X')
custom_f02_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_f02_y_vals) / 100.0)), name='ASTM_F02_Y')
custom_f02_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_f02_z_vals) / 100.0)), name='ASTM_F02_Z')

astm_u3000_x_vals = [0.000, 0.000, 0.001, -0.017, 0.092, 0.135, -0.257, 2.069, 3.204, 0.062, 0.415, 0.198, 0.169, 0.155, -0.009, 0.021, 0.042, -1.201, 10.840, 11.869, 0.387, 1.128, 8.214, 11.944, 3.319, 38.861, 13.839, 4.211, 0.499, 0.616, 0.285, 0.080, 0.033, 0.029, 0.007, 0.021, -0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_u3000_y_vals = [0.000, 0.000, 0.000, -0.002, 0.010, 0.015, -0.041, 0.286, 0.465, 0.057, 0.174, 0.076, 0.770, 2.519, 0.931, 0.270, 0.251, -2.280, 25.526, 23.924, -0.403, 1.412, 6.935, 8.375, 2.227, 19.551, 6.592, 1.737, 0.201, 0.245, 0.113, 0.031, 0.013, 0.011, 0.003, 0.008, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
astm_u3000_z_vals = [0.000, 0.000, 0.003, -0.077, 0.418, 0.624, -1.329, 10.392, 16.211, 0.482, 2.392, 1.212, 1.918, 3.301, 0.337, -0.006, 0.020, 0.002, 0.284, 0.145, -0.024, 0.001, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_u3000_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_u3000_x_vals) / 100.0)), name='ASTM_U3000_X')
custom_u3000_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_u3000_y_vals) / 100.0)), name='ASTM_U3000_Y')
custom_u3000_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(astm_u3000_z_vals) / 100.0)), name='ASTM_U3000_Z')

ul3500_x_vals = [0.0, 0.0, 0.001, -0.013, 0.074, 0.129, -0.06, 1.922, 3.113, 0.608, 0.749, 0.391, 0.204, 0.171, -0.001, 0.035, 0.118, -1.131, 9.623, 13.034, 0.665, 0.883, 8.961, 13.446, 3.616, 30.592, 15.72, 2.992, 0.621, 0.489, 0.222, 0.095, 0.034, 0.022, 0.006, 0.017, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
ul3500_y_vals = [0.0, 0.0, 0.0, 0.0, 0.008, 0.014, -0.017, 0.258, 0.461, 0.177, 0.312, 0.28, 0.778, 3.286, 1.667, 0.472, 0.679, -2.022, 22.425, 26.094, 0.051, 1.14, 7.526, 9.48, 2.306, 15.347, 7.474, 1.204, 0.255, 0.193, 0.087, 0.037, 0.013, 0.008, 0.002, 0.007, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
ul3500_z_vals = [0.0, 0.0, 0.002, -0.061, 0.336, 0.592, -0.373, 9.612, 15.792, 3.386, 4.32, 2.543, 2.182, 4.053, 0.763, -0.007, 0.051, 0.01, 0.238, 0.155, -0.023, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
custom_u35_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(ul3500_x_vals) / 100.0)), name='U35_X')
custom_u35_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(ul3500_y_vals) / 100.0)), name='U35_Y')
custom_u35_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(ul3500_z_vals) / 100.0)), name='U35_Z')

led35k_x_vals = [0.000, 0.000, -0.001, -0.003, 0.067, 0.502, 1.921, 3.207, 1.815, 0.549, 0.145, 0.030, -0.004, 0.177, 0.760, 1.755, 3.060, 4.666, 6.746, 9.120, 11.333, 13.126, 13.468, 12.086, 9.393, 6.322, 3.612, 1.837, 0.834, 0.343, 0.131, 0.048, 0.017, 0.006, 0.002, 0.001, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
led35k_y_vals = [0.000, 0.000, 0.000, -0.001, 0.005, 0.052, 0.297, 0.766, 0.758, 0.568, 0.535, 0.893, 1.891, 3.445, 5.184, 6.664, 7.921, 8.832, 9.607, 9.959, 9.706, 9.089, 7.838, 6.142, 4.333, 2.747, 1.495, 0.731, 0.328, 0.135, 0.051, 0.019, 0.007, 0.003, 0.001, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
led35k_z_vals = [0.000, 0.000, -0.005, -0.020, 0.301, 2.435, 9.825, 17.238, 10.477, 3.800, 1.544, 1.105, 0.922, 0.644, 0.403, 0.224, 0.107, 0.030, -0.002, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_led35k_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led35k_x_vals) / 100.0)), name='LED35K_X')
custom_led35k_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led35k_y_vals) / 100.0)), name='LED35K_Y')
custom_led35k_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led35k_z_vals) / 100.0)), name='LED35K_Z')

tl83_x_vals = [0.000, 0.000, 0.001, -0.023, 0.116, 0.220, -0.345, 2.825, 3.128, 0.088, 0.425, 0.200, 0.211, 0.173, -0.005, 0.025, -0.054, -0.727, 10.438, 11.409, 0.085, 0.105, 8.146, 11.772, 5.545, 39.852, 12.832, 4.259, 0.458, 0.509, 0.241, 0.077, 0.026, 0.028, 0.010, 0.020, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
tl83_y_vals = [0.000, 0.000, 0.000, -0.002, 0.012, 0.023, -0.051, 0.379, 0.455, 0.063, 0.179, 0.063, 0.891, 2.936, 1.452, 0.247, -0.078, -1.095, 25.187, 22.505, -0.583, 0.238, 6.881, 8.368, 3.334, 20.260, 6.010, 1.784, 0.183, 0.202, 0.095, 0.030, 0.010, 0.011, 0.004, 0.008, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
tl83_z_vals = [0.000, 0.000, 0.005, -0.103, 0.524, 1.010, -1.757, 14.132, 15.823, 0.625, 2.450, 1.207, 2.328, 3.766, 0.610, -0.034, 0.006, 0.018, 0.306, 0.122, -0.020, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_tl83_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(tl83_x_vals) / 100.0)), name='TL83_X')
custom_tl83_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(tl83_y_vals) / 100.0)), name='TL83_Y')
custom_tl83_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(tl83_z_vals) / 100.0)), name='TL83_Z')

led_b1_x_vals = [0.000031, -0.000150, 0.000821, 0.002442, 0.062461, 0.258701, 1.035811, 2.049991, 1.240149, 0.519537, 0.176468, 0.038238, 0.000851, 0.138360, 0.580319, 1.404661, 2.610123, 4.229513, 6.502809, 9.286454, 12.038819, 14.566985, 15.432352, 14.243251, 11.357891, 7.900749, 4.640313, 2.465327, 1.155391, 0.498470, 0.198411, 0.075966, 0.028191, 0.010117, 0.003703, 0.001346, 0.000499, 0.000189, 0.000074, 0.000032, 0.000005]
led_b1_y_vals = [0.000003, -0.000014, 0.000081, 0.000270, 0.006370, 0.029938, 0.151953, 0.480331, 0.531082, 0.515223, 0.599201, 0.916287, 1.595039, 2.627616, 3.963429, 5.317968, 6.764593, 8.014659, 9.290737, 10.155148, 10.333176, 10.104026, 8.990918, 7.246063, 5.242298, 3.442575, 1.922385, 0.984252, 0.455777, 0.194748, 0.077209, 0.029507, 0.010942, 0.003930, 0.001441, 0.000525, 0.000195, 0.000074, 0.000029, 0.000013, 0.000002]
led_b1_z_vals = [0.000154, -0.000752, 0.003986, 0.010087, 0.295446, 1.262904, 5.264653, 11.005986, 7.185076, 3.555155, 1.772876, 1.137199, 0.766148, 0.485631, 0.310660, 0.180641, 0.093317, 0.028323, -0.002627, 0.000692, -0.000182, 0.000048, -0.000013, 0.000003, -0.000001, 0.000000, -0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000]
custom_led_b1_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_b1_x_vals) / 100.0)), name='LED_B1_X')
custom_led_b1_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_b1_y_vals) / 100.0)), name='LED_B1_Y')
custom_led_b1_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_b1_z_vals) / 100.0)), name='LED_B1_Z')

led_t8g_x_vals = [0.000, 0.000, -0.001, 0.001, 0.058, 0.352, 1.901, 4.418, 2.477, 0.806, 0.248, 0.056, -0.002, 0.240, 0.905, 1.943, 3.242, 4.768, 6.573, 8.403, 9.858, 10.737, 10.262, 11.835, 7.666, 9.501, 3.489, 0.999, 0.425, 0.167, 0.061, 0.021, 0.007, 0.003, 0.001, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
led_t8g_y_vals = [0.000, 0.000, -0.000, 0.000, 0.004, 0.029, 0.287, 1.057, 1.022, 0.822, 0.891, 1.543, 2.871, 4.526, 6.115, 7.342, 8.365, 9.001, 9.337, 9.156, 8.422, 7.426, 5.989, 5.998, 3.570, 4.117, 1.454, 0.389, 0.167, 0.065, 0.023, 0.008, 0.003, 0.001, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
led_t8g_z_vals = [0.000, 0.000, -0.003, -0.002, 0.267, 1.680, 9.698, 23.749, 14.273, 5.567, 2.607, 1.895, 1.374, 0.831, 0.468, 0.244, 0.112, 0.030, -0.002, -0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]
custom_led_t8g_X = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_t8g_x_vals) / 100.0)), name='LED_T8G_X')
custom_led_t8g_Y = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_t8g_y_vals) / 100.0)), name='LED_T8G_Y')
custom_led_t8g_Z = colour.SpectralDistribution(dict(zip(wls_astm, np.array(led_t8g_z_vals) / 100.0)), name='LED_T8G_Z')

LIGHT_MAP = {
    "D65": (custom_d65_X, custom_d65_Y, custom_d65_Z), "A": (custom_a_X, custom_a_Y, custom_a_Z),
    "CWF (F02)": (custom_f02_X, custom_f02_Y, custom_f02_Z), "TL84 (F11)": (custom_tl84_X, custom_tl84_Y, custom_tl84_Z),
    "TL83": (custom_tl83_X, custom_tl83_Y, custom_tl83_Z), "U3000 (F12)": (custom_u3000_X, custom_u3000_Y, custom_u3000_Z),
    "U3500": (custom_u35_X, custom_u35_Y, custom_u35_Z), "LED35K": (custom_led35k_X, custom_led35k_Y, custom_led35k_Z),
    "LED_B1": (custom_led_b1_X, custom_led_b1_Y, custom_led_b1_Z), "LED_T8G": (custom_led_t8g_X, custom_led_t8g_Y, custom_led_t8g_Z)
}

def get_ks(reflectance): return (1 - reflectance)**2 / (2 * reflectance)

def get_ks_normalized(spectrum_map):
    target_wls = np.arange(360, 710, 10)
    sorted_items = sorted(spectrum_map.items(), key=lambda x: int(x[0]))
    existing_wls = np.array([int(k) for k, v in sorted_items])
    existing_vals = np.array([float(v) for k, v in sorted_items])
    normalized_vals = np.interp(target_wls, existing_wls, existing_vals)
    return get_ks(normalized_vals)

def parse_datacolor_to_ks(block_text, is_batch=False):
    prefix = "BAT_" if is_batch else "STD_"
    points_match = re.search(fr'{prefix}REFLPOINTS=(\d+)', block_text)
    interval_match = re.search(fr'{prefix}REFLINTERVAL=(\d+)', block_text)
    low_match = re.search(fr'{prefix}REFLLOW=(\d+)', block_text)
    r_match = re.search(fr'{prefix}R=([\d\.,\s]+)', block_text)
    if not r_match: raise ValueError(t("qtx_error"))
        
    refl_points = int(points_match.group(1)) if points_match else 31
    refl_interval = int(interval_match.group(1)) if interval_match else 10
    refl_low = int(low_match.group(1)) if low_match else 400
    wls = np.arange(refl_low, refl_low + refl_points * refl_interval, refl_interval)
    r_str = r_match.group(1)
    r_vals = [float(x.strip()) / 100.0 for x in r_str.split(',') if x.strip()]
    if len(r_vals) > refl_points: r_vals = r_vals[:refl_points]
    spectrum_map = {str(w): r for w, r in zip(wls, r_vals)}
    return get_ks_normalized(spectrum_map)

def get_preview_hex(target_r_array, light_name):
    shape_10nm = colour.SpectralShape(400, 700, 10)
    cmfs = colour.MSDS_CMFS['CIE 1964 10 Degree Standard Observer'].copy().align(shape_10nm)
    cmfs_values = cmfs.values
    light_data = LIGHT_MAP[light_name]
    if isinstance(light_data, tuple):
        W_X = light_data[0].copy().align(shape_10nm).values
        W_Y = light_data[1].copy().align(shape_10nm).values
        W_Z = light_data[2].copy().align(shape_10nm).values
        W = np.column_stack((W_X, W_Y, W_Z))
    else:
        light_spd = light_data.copy().align(shape_10nm)
        light_values = light_spd.values
        dw = 10
        k = np.sum(light_values * cmfs_values[:, 1]) * dw
        W = (light_values[:, np.newaxis] * cmfs_values) * dw / k
        
    wp_XYZ = np.sum(W, axis=0)
    wp_xy = colour.XYZ_to_xy(wp_XYZ)
    XYZ_tgt = np.dot(target_r_array, W)
    RGB_viz = colour.XYZ_to_sRGB(XYZ_tgt, illuminant=wp_xy)
    RGB_viz = np.clip(RGB_viz, 0, 1)
    hex_col = "#{:02x}{:02x}{:02x}".format(int(RGB_viz[0]*255), int(RGB_viz[1]*255), int(RGB_viz[2]*255))
    return hex_col, [int(RGB_viz[0]*255), int(RGB_viz[1]*255), int(RGB_viz[2]*255)]

@st.cache_data
def get_all_dye_hex_dict(dye_mode):
    hex_dict = {}
    try:
        dye_data = load_dye_data(dye_mode)
        for dye_name, conc_data in dye_data.items():
            available_concs = sorted([float(k) for k in conc_data.keys() if float(k) > 0])
            if not available_concs:
                hex_dict[dye_name] = "#FFFFFF"
                continue
            max_c_key = [k for k in conc_data.keys() if float(k) == available_concs[-1]][0]
            spectrum_map = conc_data[max_c_key]
            target_wls = np.arange(400, 710, 10)
            sorted_items = sorted(spectrum_map.items(), key=lambda x: int(x[0]))
            existing_wls = np.array([int(k) for k, v in sorted_items])
            existing_vals = np.array([float(v) for k, v in sorted_items])
            r_array_31 = np.interp(target_wls, existing_wls, existing_vals)
            hex_col, _ = get_preview_hex(r_array_31, "D65")
            hex_dict[dye_name] = hex_col
    except Exception: pass
    return hex_dict

@st.cache_data
def load_fastness_db():
    try:
        file_path = "color_fastness.xlsx"
        df = pd.read_excel(file_path)
        return df
    except Exception: return None

def predict_color_fastness(recipe, db_df):
    if db_df is None: return {"Error": "color_fastness.xlsx not found."}
    recipe_dyes = db_df[db_df['염료명'].isin(recipe.keys())].copy()
    if recipe_dyes.empty: return {"Error": "No matching dyes in DB."}

    recipe_dyes['처방농도'] = recipe_dyes['염료명'].map(recipe)
    recipe_dyes['비율'] = recipe_dyes['처방농도'] / recipe_dyes['S/D\n1/1']
    grade_columns = recipe_dyes.columns[2:-2] 
    max_ratio = recipe_dyes['비율'].max()
    
    predicted_results = {}
    for col in grade_columns:
        min_grade = recipe_dyes[col].min()
        if max_ratio >= 1.5 and any(keyword in col for keyword in ['마찰', '세탁', '땀']): min_grade -= 0.5
        elif max_ratio <= 0.5 and '일광견뢰도' in col and '1/6' not in col: min_grade -= 0.5
        predicted_results[col] = max(1.0, min_grade)
    return predicted_results

blank_r_str_reactive = "61.487896,64.536758,67.636276,70.483246,73.516251,75.622711,77.759293,79.583626,80.990044,82.235336,83.458176,84.331772,85.404106,86.164101,86.926323,87.612724,88.086739,88.541801,88.927353,89.348244,89.645943,89.882187,90.113014,90.397278,90.583130,90.746536,90.858932,91.020134,91.199127,91.403587,91.537102,91.670677,91.884819,91.980095,92.083275"
blank_r_reactive = np.array([float(x.strip()) / 100.0 for x in blank_r_str_reactive.split(',') if x.strip()])
blank_ks_reactive = get_ks(blank_r_reactive)

disperse_blank_text = "[STANDARD_DATA 0]\nSTD_REFLPOINTS=31,\nSTD_REFLINTERVAL=10,\nSTD_REFLLOW=400,\nSTD_R=83.435000,84.975000,84.604500,83.743500,82.880500,82.520000,82.496500,82.684500,83.045000,83.254500,83.411000,83.424500,83.473500,83.565500,83.673000,83.827000,83.952000,84.098000,84.095000,84.015500,84.072500,84.145000,84.288500,84.341000,84.453000,84.588000,84.811500,84.936000,85.228500,85.319000,85.334000,"
try: blank_ks_disperse = parse_datacolor_to_ks(disperse_blank_text, is_batch=False)
except Exception: blank_ks_disperse = blank_ks_reactive

blank_r_str_disp_woven = "12.550282,12.662358,13.128991,15.679015,22.198656,49.159801,90.868118,115.976440,119.316971,108.527847,99.793015,95.301094,93.386421,90.213654,88.579010,86.774918,85.229942,84.013969,83.225197,82.656410,82.167915,82.044777,81.931137,81.882439,82.200607,82.416222,82.896469,83.570839,84.365234,85.158195,85.765289,86.293983,86.519203,86.480919,86.653557"
blank_r_disp_woven = np.array([float(x.strip()) / 100.0 for x in blank_r_str_disp_woven.split(',') if x.strip()])
blank_ks_disp_woven = get_ks(blank_r_disp_woven)

blank_r_str_cpb = "65.391068,67.093147,68.937622,70.637802,72.489166,74.245972,75.516464,76.748680,77.643394,78.417038,79.229340,79.835594,80.472313,81.005417,81.598862,82.127090,82.478500,82.846130,83.165131,83.535942,83.806923,84.017708,84.260544,84.523628,84.728180,84.964073,85.149178,85.394760,85.695389,86.005653,86.231079,86.412338,86.664047,86.753532,86.915657"
blank_r_cpb = np.array([float(x.strip()) / 100.0 for x in blank_r_str_cpb.split(',') if x.strip()])
blank_ks_cpb = get_ks(blank_r_cpb)

blank_r_str_cdp = "66.642869, 69.331771, 71.930599, 73.894465, 75.701308, 77.198517, 78.580475, 79.721862, 80.800241, 81.569093, 82.308775, 82.936382, 83.379400, 83.891529, 84.177935, 84.593368, 84.832168, 85.117948, 85.361063, 85.496897, 85.857874, 85.970598, 86.050570, 86.297560, 86.426288, 86.583924, 86.748540, 86.945128, 87.095481, 87.011909, 87.268311"
blank_r_cdp_raw = np.array([float(x.strip()) / 100.0 for x in blank_r_str_cdp.split(',') if x.strip()])
wls_31 = np.arange(400, 710, 10)
wls_35 = np.arange(360, 710, 10)
blank_r_cdp = np.interp(wls_35, wls_31, blank_r_cdp_raw)
blank_ks_cdp = get_ks(blank_r_cdp)

blank_r_str_acid = "31.696901, 46.754527, 60.104591, 69.332457, 74.595761, 77.676672, 79.372197, 80.702138, 81.639552, 82.371908, 83.169580, 83.820981, 84.401035, 84.760123, 85.150397, 85.437840, 85.618544, 85.783499, 85.906208, 86.081845, 86.177695, 86.249357, 86.376613, 86.540455, 86.633664, 86.740136, 86.842757, 86.998326, 87.199730, 87.414002, 87.491035, 87.494141, 87.475324, 87.320161, 87.079161"
blank_r_acid = np.array([float(x.strip()) / 100.0 for x in blank_r_str_acid.split(',') if x.strip()])
blank_ks_acid = get_ks(blank_r_acid)

if dye_mode == "Reactive": blank_ks = blank_ks_reactive; option_letter = "R"
elif dye_mode == "Disperse": blank_ks = blank_ks_disp_woven if st.session_state.disperse_sub == "Woven" else blank_ks_disperse; option_letter = "D"
elif dye_mode == "Reactive (CPB)": blank_ks = blank_ks_cpb; option_letter = "R"
elif dye_mode == "CDP": blank_ks = blank_ks_cdp; option_letter = "Ac"
elif dye_mode == "Acid": blank_ks = blank_ks_acid; option_letter = "A"

# ==========================================
# 4.5 백포 선택 팝업 (Disperse 전용)
# ==========================================
def set_temp_disp(val): st.session_state.temp_disp = val
def confirm_disp_action():
    st.session_state.disperse_sub = st.session_state.temp_disp
    st.session_state.dye_mode = "Disperse"
    st.session_state.selected_dyes = []
    st.session_state.top_results = None

@st.dialog(t("title_disp"))
def disperse_dialog():
    st.markdown(t("desc_disp"))
    if "temp_disp" not in st.session_state: st.session_state.temp_disp = st.session_state.disperse_sub
    col1, col2 = st.columns(2)
    with col1: st.button("Jersey", use_container_width=True, type="primary" if st.session_state.temp_disp == "Jersey" else "secondary", on_click=set_temp_disp, args=("Jersey",), key="btn_dlg_jersey")
    with col2: st.button("Woven", use_container_width=True, type="primary" if st.session_state.temp_disp == "Woven" else "secondary", on_click=set_temp_disp, args=("Woven",), key="btn_dlg_woven")
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    if st.button(t("confirm"), use_container_width=True, type="primary", on_click=confirm_disp_action, key="btn_dlg_confirm"): st.rerun()

# ==========================================
# 5. Streamlit 웹 UI 구성 (메뉴 컬럼 추가)
# ==========================================
# 👉 앞의 5개 버튼(Reactive ~ Acid)의 비율을 [1, 1, 1, 1, 1]로 똑같이 맞추어 가로 크기를 통일했습니다.
top_menu_cols = st.columns([1, 1, 1, 1, 1, 1.5, 3.2, 0.7, 0.7])
with top_menu_cols[0]:
    st.button("Reactive", use_container_width=True, type="primary" if dye_mode == "Reactive" else "secondary", on_click=set_dye_mode, args=("Reactive",), key="btn_react_top")
    st.markdown('<div id="top-menu-marker"></div>', unsafe_allow_html=True)
with top_menu_cols[1]:
    if st.button("Disperse", use_container_width=True, type="primary" if dye_mode == "Disperse" else "secondary", key="btn_disp_top"):
        st.session_state.temp_disp = st.session_state.disperse_sub
        disperse_dialog()
with top_menu_cols[2]: st.button("Reactive (CPB)", use_container_width=True, type="primary" if dye_mode == "Reactive (CPB)" else "secondary", on_click=set_dye_mode, args=("Reactive (CPB)",), key="btn_cpb_top")
with top_menu_cols[3]: st.button("CDP", use_container_width=True, type="primary" if dye_mode == "CDP" else "secondary", on_click=set_dye_mode, args=("CDP",), key="btn_cdp_top")
with top_menu_cols[4]: st.button("Acid", use_container_width=True, type="primary" if dye_mode == "Acid" else "secondary", on_click=set_dye_mode, args=("Acid",), key="btn_acid_top")

# 업체 선택 박스 (다국어 맵핑)
with top_menu_cols[5]:
    company_options = [t("company_all")] + all_companies
    selected_company = st.selectbox(t("company_sel"), options=company_options, index=None, placeholder=t("company_sel"), label_visibility="collapsed", key="company_select_top")

# (top_menu_cols[6] 은 빈 공간으로 남겨둡니다 - 버튼들을 우측으로 밀어내는 역할)

# 언어 변환 버튼을 우측 끝(7번째, 8번째 컬럼)에 배치
with top_menu_cols[7]:
    st.button("🇰🇷 KO", use_container_width=True, type="primary" if st.session_state.lang == "ko" else "secondary", on_click=set_lang, args=("ko",), key="btn_lang_ko")
with top_menu_cols[8]:
    st.button("🇺🇸 EN", use_container_width=True, type="primary" if st.session_state.lang == "en" else "secondary", on_click=set_lang, args=("en",), key="btn_lang_en")

# ------------------------------------------
# 왼쪽 사이드바 (염료 리스트)
# ------------------------------------------
with st.sidebar:
    st.markdown(f"<h3 style='display: flex; align-items: center;'><span class='material-symbols-outlined' style='margin-right:8px;'>palette</span>{t('dye_list')} ({header_mode_text})</h3>", unsafe_allow_html=True)
    if missing_dyes: st.warning(t("missing_dyes", count=len(missing_dyes), dyes=', '.join(missing_dyes)), icon=":material/warning:")
    st.caption(t("click_guide"))
    
    pasted_text = st.text_input(t("paste_ph"), label_visibility="collapsed", placeholder=t("paste_ph"))
    if st.button(t("load_ohyoung"), use_container_width=True, type="primary"):
        if pasted_text:
            current_dye_db = load_dye_data(st.session_state.dye_mode)
            current_all_dyes, _, _, _, _ = load_dye_mapping(st.session_state.dye_mode, current_dye_db.keys())
            copied_names = [x.strip() for x in pasted_text.split(',')]
            added_count = 0
            for name in copied_names:
                if not name: continue
                for raw_name, display_name, _ in current_all_dyes:
                    if name == raw_name or name == display_name:
                        if raw_name not in st.session_state.selected_dyes:
                            st.session_state.selected_dyes.append(raw_name)
                            added_count += 1
                        break
            if added_count > 0: st.success(t("success_add", count=added_count))
            else: st.info(t("fail_add"))
        else: st.warning(t("warn_paste"))
            
    st.markdown("---")
    def clear_search(): st.session_state.search_query_input = ""
    st.markdown(f"<div style='font-size: 14px; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center;'><span class='material-symbols-outlined' style='margin-right:6px; font-size:18px;'>search</span>{t('search_dye')}</div>", unsafe_allow_html=True)
    
    col_search, col_clear = st.columns([7.5, 2.5], vertical_alignment="center")
    with col_search:
        search_query = st.text_input(t("search_dye"), placeholder=t("search_ph"), label_visibility="collapsed", key="search_query_input")
    with col_clear:
        st.button(t("reset"), use_container_width=True, on_click=clear_search)
        
    dye_hex_dict = get_all_dye_hex_dict(st.session_state.dye_mode)
    filtered_dyes = []
    for raw_name, display_name, companies in all_dyes_ordered:
        company_match = (selected_company is None or selected_company == t("company_all") or selected_company in companies)
        search_match = True
        if search_query: search_match = (search_query.lower() in raw_name.lower()) or (search_query.lower() in display_name.lower())
        if company_match and search_match: filtered_dyes.append((raw_name, display_name))
            
    st.markdown("""
    <style>
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button {
            border: none !important; box-shadow: none !important; padding-left: 8px !important; height: 35px !important; min-height: 35px !important;
        }
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"] { background-color: transparent !important; }
        section[data-testid="stSidebar"] { min-width: 390px !important; }
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"]:hover { background-color: rgba(0,0,0,0.04) !important; }
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button div,
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button p {
            display: flex !important; justify-content: flex-start !important; text-align: left !important; width: 100% !important; margin: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    for idx, (raw_name, display_name) in enumerate(filtered_dyes):
        btn_type = "primary" if raw_name in st.session_state.selected_dyes else "secondary"
        hex_col = dye_hex_dict.get(raw_name, "#FFFFFF")
        col_color, col_btn = st.columns([0.7, 9.3], gap="small", vertical_alignment="center") 
        with col_color:
            st.markdown(f"""<div style="background-color: {hex_col}; height: 35px; width: 8px; border-radius: 4px; margin-top: -8px; float: right;"></div>""", unsafe_allow_html=True)
        with col_btn:
            st.button(display_name, key=f"dye_{raw_name}_{idx}", use_container_width=True, type=btn_type, on_click=toggle_dye, args=(raw_name,))

# ------------------------------------------
# 메인 화면 (좌우 패널 구성)
# ------------------------------------------
col_menu, col_results = st.columns([1.2, 2], gap="large")

with col_menu:
    with st.container(border=True):
        st.markdown(f"<strong style='display: flex; align-items: center; font-size: 16px;'><span class='material-symbols-outlined' style='margin-right:6px;'>folder_open</span>{t('step1_title')}</strong>", unsafe_allow_html=True)
        upload_col, color_col = st.columns([1.2, 1.8])
        with upload_col:
            uploaded_file = st.file_uploader(t("upload_qtx"), type=['qtx'], label_visibility="collapsed", key="qtx_uploader")
        
        target_r = None
        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode('euc-kr', errors='ignore') 
                standards = []
                blocks = re.split(r'\[(STANDARD_DATA|BATCH_DATA)[^\]]*\]', content)
                for i in range(1, len(blocks), 2):
                    block_type = blocks[i]
                    block_content = blocks[i+1]
                    if block_type == 'STANDARD_DATA':
                        name_match = re.search(r'STD_NAME=(.*?)\n', block_content)
                        r_match = re.search(r'STD_R=([\d\.,\s]+)', block_content)
                        low_match = re.search(r'STD_REFLLOW=(\d+)', block_content)
                        if r_match:
                            name = name_match.group(1).strip().rstrip(',') if name_match else "Unknown Standard"
                            r_vals = [float(x.strip()) / 100.0 for x in r_match.group(1).split(',') if x.strip()]
                            start_wl = int(low_match.group(1)) if low_match else 400
                            standards.append({'name': f"[STD] {name}", 'r_vals': r_vals, 'start_wl': start_wl})
                    elif block_type == 'BATCH_DATA':
                        name_match = re.search(r'BAT_NAME=(.*?)\n', block_content)
                        r_match = re.search(r'BAT_R=([\d\.,\s]+)', block_content)
                        low_match = re.search(r'BAT_REFLLOW=(\d+)', block_content)
                        if r_match:
                            name = name_match.group(1).strip().rstrip(',') if name_match else "Unknown Batch"
                            r_vals = [float(x.strip()) / 100.0 for x in r_match.group(1).split(',') if x.strip()]
                            start_wl = int(low_match.group(1)) if low_match else 400
                            standards.append({'name': f"[BAT] {name}", 'r_vals': r_vals, 'start_wl': start_wl})
                
                if not standards:
                    st.error(t("qtx_error"), icon=":material/error:")
                else:
                    if len(standards) > 1:
                        std_names = [s['name'] for s in standards]
                        selected_std_idx = st.selectbox(t("target_sel"), range(len(std_names)), format_func=lambda x: std_names[x])
                    else:
                        selected_std_idx = 0
                        st.info(t("target_found", name=standards[0]['name']), icon=":material/check_circle:")
                    
                    selected_std = standards[selected_std_idx]
                    st.session_state.qtx_filename = selected_std['name'].replace('[STD] ', '').replace('[BAT] ', '')
                    raw_r_vals, start_wl = selected_std['r_vals'], selected_std['start_wl']

                    current_wls = np.array([start_wl + i * 10 for i in range(len(raw_r_vals))])
                    target_wls = np.arange(360, 710, 10)
                    target_r = np.interp(target_wls, current_wls, raw_r_vals)
                    
                    active_lights_ui = [st.session_state.l1]
                    if st.session_state.l2 != "없음": active_lights_ui.append(st.session_state.l2)
                    if st.session_state.l3 != "없음": active_lights_ui.append(st.session_state.l3)
                    
                    with color_col:
                        preview_cols = st.columns(len(active_lights_ui))
                        for i, ln in enumerate(active_lights_ui):
                            hc, rgb = get_preview_hex(target_r[4:35], ln)
                            if i == 0: st.session_state.qtx_excel_color = rgb[0] + (rgb[1] * 256) + (rgb[2] * 65536)
                            with preview_cols[i]: st.markdown(f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 5px;"><div style="width: 100%; height: 50px; background-color: {hc}; border: 1px solid #ccc; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);"></div><div style="font-size: 11px; font-weight: bold; margin-top: 4px; color: #555;">{ln.split()[0]}</div></div>""", unsafe_allow_html=True)
            except Exception as e: st.error(t("qtx_parse_error", e=str(e)), icon=":material/error:")
        else:
            with color_col: st.markdown(f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 5px;"><div style="width: 100%; height: 50px; background-color: #f0f2f6; border: 1px dashed #ccc; border-radius: 8px;"></div><div style="font-size: 11px; margin-top: 4px; color: #999;">{t("preview_wait")}</div></div>""", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"<strong style='display: flex; align-items: center; font-size: 16px;'><span class='material-symbols-outlined' style='margin-right:6px;'>settings</span>{t('step2_title')}</strong>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-top: 10px; display: flex; align-items: center;'><span class='material-symbols-outlined' style='margin-right:4px; font-size:16px;'>label</span>{t('auto_brand')}</div>", unsafe_allow_html=True)
        brand_list = ["직접 선택 (Manual)"] + sorted(brand_df['Brand'].dropna().unique().tolist())
        st.selectbox(t("auto_brand_desc"), brand_list, key="brand_selector", on_change=on_brand_change, label_visibility="collapsed", format_func=lambda x: "Manual" if x=="직접 선택 (Manual)" and st.session_state.lang=="en" else x)

        st.markdown(f"<div style='font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-top: 15px; display: flex; align-items: center;'><span class='material-symbols-outlined' style='margin-right:4px; font-size:16px;'>lightbulb</span>{t('light_detail')}</div>", unsafe_allow_html=True)
        light_options_all = list(LIGHT_MAP.keys())
        light_options_optional = list(LIGHT_MAP.keys()) + ["없음"]
        
        l_col1, l_col2, l_col3 = st.columns(3)
        fmt_light = lambda x: "None" if x=="없음" and st.session_state.lang=="en" else x
        light1_name = l_col1.selectbox(t("light_1"), light_options_all, key="l1")
        light2_name = l_col2.selectbox(t("light_2"), light_options_optional, key="l2", format_func=fmt_light) 
        light3_name = l_col3.selectbox(t("light_3"), light_options_optional, key="l3", format_func=fmt_light) 

    with st.container(border=True):
        st.markdown(f"<strong style='display: flex; align-items: center; font-size: 16px;'><span class='material-symbols-outlined' style='margin-right:6px;'>science</span>{t('step3_title')}</strong>", unsafe_allow_html=True)
        st.markdown(t("selected_count", count=len(st.session_state.selected_dyes)))
        st.button(t("clear_all"), use_container_width=True, disabled=(len(st.session_state.selected_dyes) == 0), on_click=clear_dyes, icon=":material/refresh:")

        run_search = False
        if target_r is None: st.button(t("btn_need_qtx"), type="primary", use_container_width=True, disabled=True, icon=":material/rocket_launch:")
        elif len(st.session_state.selected_dyes) < 1: st.button(t("btn_need_dye"), type="primary", use_container_width=True, disabled=True, icon=":material/rocket_launch:")
        else: run_search = st.button(t("btn_start"), type="primary", use_container_width=True, icon=":material/rocket_launch:")

# ==========================================
# [우측 패널] 검색 결과 화면
# ==========================================
with col_results:
    st.markdown(f"### <span class='material-symbols-outlined' style='font-size:26px; vertical-align: middle; margin-right:8px;'>search</span>{t('result_title')}", unsafe_allow_html=True)
    feedback_results = st.empty()
    
    if run_search:
        loading_overlay = st.empty()
        loading_overlay.markdown(f"""<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(255, 255, 255, 0.8); z-index: 9999999; display: flex; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(2px);"><div style="background: white; padding: 40px 60px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); text-align: center; display: flex; flex-direction: column; align-items: center;"><span class="material-symbols-outlined" style="font-size: 56px; color: #1f325c; animation: spin 1.2s linear infinite;">sync</span><h2 style="margin-top: 20px; font-size: 26px; color: #333; font-weight: bold;">{t("finding")}</h2><p style="margin-top: 10px; color: #666; font-size: 16px; line-height: 1.5;">{t("finding_desc")}</p></div></div>""", unsafe_allow_html=True)
        
        selected_pool = sorted(st.session_state.selected_dyes, key=lambda x: sort_order_dict.get(x, 999))
        combos = []
        max_dyes = min(3, len(selected_pool))
        for r in range(1, max_dyes + 1):
            combos.extend(list(itertools.combinations(selected_pool, r)))
        
        active_lights = [light1_name]
        if light2_name != "없음": active_lights.append(light2_name)
        if light3_name != "없음": active_lights.append(light3_name)
        
        my_bar = st.progress(0, text=f"Total {len(combos)} combinations...")
        results = []
        
        shape_10nm = colour.SpectralShape(400, 700, 10)
        cmfs = colour.MSDS_CMFS['CIE 1964 10 Degree Standard Observer'].copy().align(shape_10nm)
        cmfs_values = cmfs.values
        start_idx = 4 
        target_r_31 = target_r[start_idx:35]
        
        precalc_lights = []
        for l_name in active_lights:
            light_data = LIGHT_MAP[l_name]
            if isinstance(light_data, tuple):
                W_X, W_Y, W_Z = light_data[0].copy().align(shape_10nm).values, light_data[1].copy().align(shape_10nm).values, light_data[2].copy().align(shape_10nm).values
                W = np.column_stack((W_X, W_Y, W_Z))
            else:
                light_values = light_data.copy().align(shape_10nm).values
                dw = 10
                k = np.sum(light_values * cmfs_values[:, 1]) * dw
                W = (light_values[:, np.newaxis] * cmfs_values) * dw / k 
            
            wp_XYZ = np.sum(W, axis=0) 
            wp_xy = colour.XYZ_to_xy(wp_XYZ)
            XYZ_tgt = np.dot(target_r_31, W)
            lab_tgt = colour.XYZ_to_Lab(XYZ_tgt, illuminant=wp_xy)
            precalc_lights.append({'W': W, 'wp_xy': wp_xy, 'lab_tgt': lab_tgt})
            
        target_ks_31 = get_ks(target_r_31)
        blank_ks_31 = blank_ks[start_idx:35]
        net_target_ks = np.maximum(target_ks_31 - blank_ks_31, 0)
        
        candidates = []
        for idx, combo in enumerate(combos):
            if idx % 50 == 0:
                my_bar.progress((idx + 1) / len(combos), text=f"Fast Filtering... ({idx+1}/{len(combos)})")
                
            dye_ks_interpolators = [] 
            valid_combo = True
            for name in combo:
                available_concs = sorted([float(k) for k in dye_db[name].keys() if float(k) > 0])
                if len(available_concs) == 0:
                    valid_combo = False
                    break
                
                concs_with_zero = [0.0]
                ks_matrix = [np.zeros(len(blank_ks))]
                for c in available_concs:
                    concs_with_zero.append(c)
                    c_key = [k for k in dye_db[name].keys() if float(k) == c][0]
                    spectrum_map = dye_db[name][c_key]
                    ref_ks_total = get_ks_normalized(spectrum_map)
                    ref_ks_net = np.maximum(ref_ks_total - blank_ks, 0)
                    ks_matrix.append(ref_ks_net)

                concs_array = np.array(concs_with_zero)
                ks_matrix = np.array(ks_matrix)
                interp_func = PchipInterpolator(concs_array, ks_matrix, axis=0)
                dye_ks_interpolators.append((concs_array[-1], interp_func)) 
            
            if not valid_combo: continue

            unit_ks_list_for_nnls = []
            for i, name in enumerate(combo):
                max_c, interp_func = dye_ks_interpolators[i]
                available_concs = sorted([float(k) for k in dye_db[name].keys() if float(k) > 0])
                lowest_c = available_concs[0] if available_concs else max_c
                eval_c = min(0.1, lowest_c)
                unit_ks = interp_func(eval_c) / eval_c if eval_c > 0 else np.zeros(len(blank_ks))
                unit_ks_list_for_nnls.append(unit_ks)

            A = np.column_stack([u[start_idx:35] for u in unit_ks_list_for_nnls])
            approx_conc, _ = nnls(A, net_target_ks)
            
            total_ks = np.copy(blank_ks)
            for i in range(len(combo)):
                c = approx_conc[i]
                max_c, interp_func = dye_ks_interpolators[i]
                if c <= max_c: dye_ks = interp_func(c)
                else: 
                    if dye_mode == "Acid":
                        excess_ratio = (c - max_c) / max_c if max_c > 0 else 0
                        damping = max(0.2, 0.85 - (0.2 * excess_ratio))
                        dye_ks = interp_func(max_c) + (interp_func(max_c) / max_c) * (c - max_c) * damping
                    else: dye_ks = interp_func(max_c) + (interp_func(max_c) / max_c) * (c - max_c) * 0.85 
                total_ks += np.maximum(dye_ks, 0)
            
            est_r = 1 + total_ks - np.sqrt(total_ks**2 + 2 * total_ks)
            est_r_31 = est_r[start_idx:35] 
            
            light1_data = precalc_lights[0]
            XYZ_est_1 = np.dot(est_r_31, light1_data['W']) 
            lab_est_1 = colour.XYZ_to_Lab(XYZ_est_1, illuminant=light1_data['wp_xy'])
            approx_dE = colour.delta_E(lab_est_1, light1_data['lab_tgt'], method='CMC', l=2, c=1)
            
            if approx_dE <= 15.0:
                candidates.append({'combo': combo, 'approx_conc': approx_conc, 'approx_dE': approx_dE, 'interpolators': dye_ks_interpolators})

        candidates.sort(key=lambda x: x['approx_dE'])
        top_candidates = candidates[:200]
        total_cands = len(top_candidates)
        
        for idx, cand in enumerate(top_candidates):
            combo = cand['combo']
            approx_conc = cand['approx_conc']
            dye_ks_interpolators = cand['interpolators']
            
            combo_display_names = [display_name_dict.get(name, name) for name in combo]
            names_text = ", ".join(combo_display_names)
            my_bar.progress((idx + 1) / total_cands, text=f"Precise Search: {names_text} ({idx+1}/{total_cands})")

            def evaluate_lights_local(conc, return_lab=False):
                total_ks_local = np.copy(blank_ks)
                for i in range(len(combo)):
                    c = conc[i]
                    max_c, interp_func = dye_ks_interpolators[i]
                    if c <= max_c: dye_ks = interp_func(c)
                    else: 
                        if dye_mode == "Acid":
                            excess_ratio = (c - max_c) / max_c if max_c > 0 else 0
                            damping = max(0.2, 0.85 - (0.2 * excess_ratio))
                            dye_ks = interp_func(max_c) + (interp_func(max_c) / max_c) * (c - max_c) * damping
                        else: dye_ks = interp_func(max_c) + (interp_func(max_c) / max_c) * (c - max_c) * 0.85 
                    total_ks_local += np.maximum(dye_ks, 0)
                
                est_r_local = 1 + total_ks_local - np.sqrt(total_ks_local**2 + 2 * total_ks_local)
                est_r_31_local = est_r_local[start_idx:35] 
                
                des = []
                labs = []
                l1_data = precalc_lights[0]
                XYZ_est_1_local = np.dot(est_r_31_local, l1_data['W']) 
                lab_est_1_local = colour.XYZ_to_Lab(XYZ_est_1_local, illuminant=l1_data['wp_xy'])
                lab_tgt_1_local = l1_data['lab_tgt']
                
                for idx_l, light_data in enumerate(precalc_lights):
                    XYZ_est_local = np.dot(est_r_31_local, light_data['W']) 
                    lab_est_local = colour.XYZ_to_Lab(XYZ_est_local, illuminant=light_data['wp_xy'])
                    if idx_l == 0: de = colour.delta_E(lab_est_local, light_data['lab_tgt'], method='CMC', l=2, c=1)
                    else:
                        lab_est_corr = lab_est_local + (lab_tgt_1_local - lab_est_1_local)
                        de = colour.delta_E(lab_est_corr, light_data['lab_tgt'], method='CMC', l=2, c=1)
                        de = apply_dc_correction(active_lights[idx_l], de)
                    des.append(de)
                    labs.append((lab_est_local, light_data['lab_tgt']))
                if return_lab: return des, labs
                return des

            def objective_local(conc):
                des = evaluate_lights_local(conc)
                weight_obj = des[0] 
                if len(des) > 1: weight_obj += 0.01 * des[1] 
                if len(des) > 2: weight_obj += 0.01 * des[2]
                return weight_obj 

            max_bound = 150.0 if dye_mode == "Reactive (CPB)" else 15.0
            bnds = [(0.0, max_bound) for _ in range(len(combo))]
            x0_start = np.clip(approx_conc, 0.0, max_bound)
            res = minimize(objective_local, x0=x0_start, bounds=bnds, method='SLSQP', options={'ftol': 1e-7, 'disp': False})
            
            if res.success:
                conc = res.x
                cleaned_conc = [c if c >= 0.0005 else 0.0 for c in conc]
                total_conc = sum(cleaned_conc)
                if total_conc == 0: continue
                
                final_des = evaluate_lights_local(cleaned_conc)
                if final_des[0] < 20.0:
                    active_dyes_count = sum(1 for c in cleaned_conc if c > 0.0)
                    metamerism_index = 0
                    if len(final_des) > 1: metamerism_index += final_des[1]
                    if len(final_des) > 2: metamerism_index += final_des[2]
                    results.append({
                        'combo': combo, 'conc': [round(c, 4) for c in cleaned_conc],
                        'des': final_des, 'metamerism': metamerism_index,
                        'total_conc': round(total_conc, 4), 'active_count': active_dyes_count 
                    })

        loading_overlay.empty()
        my_bar.empty() 
        
        if len(results) > 0:
            def sort_key(x):
                return (round(x['des'][0], 4), round(x['des'][1] if len(x['des']) > 1 else 999, 4), round(x['des'][2] if len(x['des']) > 2 else 999, 4), round(x['total_conc'], 4))
            results.sort(key=sort_key)
            unique_results = []
            seen_combinations = set()
            for res in results:
                active_dyes = [dye_name for i, dye_name in enumerate(res['combo']) if res['conc'][i] > 0]
                combo_sig = "|".join(sorted(active_dyes))
                if combo_sig not in seen_combinations:
                    seen_combinations.add(combo_sig)
                    unique_results.append(res)
            st.session_state.top_results = unique_results[:10]
        else:
            st.session_state.top_results = []
            st.error(t("no_recipe"), icon=":material/error:")

    if st.session_state.top_results:
        top_results = st.session_state.top_results
        selected_pool = sorted(st.session_state.selected_dyes, key=lambda x: sort_order_dict.get(x, 999))
        used_dyes_in_top10 = set(dye_raw for res in top_results for i, dye_raw in enumerate(res['combo']) if res['conc'][i] > 0)
        active_pool = [dye for dye in selected_pool if dye in used_dyes_in_top10]
        
        row_labels = [f"dE(CMC) {light1_name} (Primary)"]
        if light2_name != "없음": row_labels.append(f"Metamerism {light2_name}")
        if light3_name != "없음": row_labels.append(f"Metamerism {light3_name}")
        row_labels.append("Total concentration [%]")
        row_labels.extend([display_name_dict.get(dye, dye) for dye in active_pool])
        
        df_dict = {"Property / Dyestuff": row_labels}
        for rank, res in enumerate(top_results):
            col_name = f"{rank+1}(3)"
            col_data = [f"{max(res['des'][0], 0.01):.2f}"]
            light_idx = 1
            if light2_name != "없음":
                col_data.append(f"{max(res['des'][light_idx], 0.01):.2f}") 
                light_idx += 1
            if light3_name != "없음":
                col_data.append(f"{max(res['des'][light_idx], 0.01):.2f}") 
            col_data.append(f"{res['total_conc']:.4f}") 
            for dye in active_pool:
                if dye in res['combo']:
                    dye_idx = res['combo'].index(dye)
                    val = res['conc'][dye_idx]
                    col_data.append(f"{val:.4f}" if val > 0 else "")
                else: col_data.append("")
            df_dict[col_name] = col_data
        
        df = pd.DataFrame(df_dict)
        df.set_index("Property / Dyestuff", inplace=True)
        def color_rows(s):
            if s.name.startswith('dE(CMC)'): return ['background-color: #e6f2ff; font-weight: bold'] * len(s)
            elif s.name.startswith('Metamerism'): return ['background-color: #fff9e6; color: #d97706'] * len(s)
            elif s.name == 'Total concentration [%]': return ['background-color: #f3f4f6; font-weight: bold'] * len(s)
            else: return [''] * len(s)
        styled_df = df.style.apply(color_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=(len(df) + 1) * 36)

        with st.container(border=True):
            st.markdown(f"<h4 style='display: flex; align-items: center; margin-bottom: 0;'><span class='material-symbols-outlined' style='margin-right:8px;'>science</span>{t('fastness_title')}</h4>", unsafe_allow_html=True)
            available_ranks = list(range(1, len(top_results) + 1))
            selected_rank = st.radio(t("fastness_sel"), options=available_ranks, horizontal=True)
            
            res = top_results[selected_rank - 1]
            fastness_db = load_fastness_db()
            recipe_for_pred = {display_name_dict.get(dye_raw, dye_raw): res['conc'][i] for i, dye_raw in enumerate(res['combo']) if res['conc'][i] > 0}
            pred_result = predict_color_fastness(recipe_for_pred, fastness_db)
            
            if "Error" in pred_result:
                st.warning(pred_result["Error"], icon=":material/warning:")
            else:
                st.markdown(f"<div style='font-size: 12px; color: #666; margin-bottom: 5px;'>{t('fastness_desc')}</div>", unsafe_allow_html=True)
                pred_df = pd.DataFrame({k.replace('\n', ' '): [v] for k, v in pred_result.items()})
                st.dataframe(pred_df, hide_index=True, use_container_width=True)

    elif not run_search:
        st.info(t("req_target"), icon=":material/info:")