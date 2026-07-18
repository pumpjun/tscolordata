import streamlit as st
import json
import numpy as np
import colour
import itertools
import pandas as pd
from scipy.optimize import minimize

# ==========================================
# 0. 세션 상태 초기화 (염료 선택 토글용)
# ==========================================
if "selected_dyes" not in st.session_state:
    st.session_state.selected_dyes = []

# 콜백 함수: 개별 염료 선택/해제 (내부적으로는 원래 이름인 raw_name 사용)
def toggle_dye(raw_name):
    if raw_name in st.session_state.selected_dyes:
        st.session_state.selected_dyes.remove(raw_name)
    else:
        st.session_state.selected_dyes.append(raw_name)

# 콜백 함수: 염료 선택 전체 초기화
def clear_dyes():
    st.session_state.selected_dyes = []

# ==========================================
# 1. 데이터 및 광원 로드
# ==========================================
@st.cache_data
def load_dye_data():
    with open('dye_data.json', 'r') as f:
        raw_data = json.load(f)
        valid_dye_db = {name: concs for name, concs in raw_data.items() if len(concs) > 0}
        return valid_dye_db

@st.cache_data
# 파라미터 이름을 valid_keys에서 _valid_keys로 변경했습니다.
def load_dye_mapping(_valid_keys):
    try:
        # header=None을 통해 1행부터 데이터로 읽어옵니다.
        df = pd.read_excel('dye_list.xlsx', header=None)
        mapping_list = []
        disp_dict = {}
        
        for _, row in df.iterrows():
            raw_name = str(row[0]).strip()
            display_name = str(row[1]).strip()
            
            # JSON 데이터에 실제로 존재하는 염료인지 확인
            if raw_name in _valid_keys:
                mapping_list.append((raw_name, display_name))
                disp_dict[raw_name] = display_name
                
        return mapping_list, disp_dict
    except Exception as e:
        st.error(f"엑셀 파일(dye_list.xlsx)을 읽는 중 오류가 발생했습니다: {e}")
        # 오류 시 기본 원래 이름으로 가나다순 정렬하여 반환
        default_list = [(k, k) for k in sorted(list(_valid_keys))]
        return default_list, {k: k for k in _valid_keys}

dye_db = load_dye_data()
# 엑셀 파일에서 맵핑 정보와 순서를 가져옵니다.
all_dyes_ordered, display_name_dict = load_dye_mapping(dye_db.keys())

datacolor_tl84_vals = [
    0.91, 0.63, 0.46, 0.37, 1.29, 12.68, 1.59, 1.79, 2.46, 3.38, 
    4.49, 33.94, 12.13, 6.95, 7.19, 7.12, 6.72, 6.13, 5.46, 4.79, 
    5.66, 14.29, 14.96, 8.97, 4.72, 2.33, 1.47, 1.10, 0.89, 0.83, 
    1.18, 4.90, 39.59, 72.84, 32.61, 7.52, 2.83, 1.96, 1.67, 4.43, 
    11.28, 14.76, 12.73, 9.74, 7.33, 9.72, 55.27, 42.58, 13.18, 13.16, 
    12.26, 5.11, 2.07, 2.34, 3.58, 3.01, 2.48, 2.14, 1.54, 1.33, 
    1.46, 1.94, 2.00, 1.20, 1.35, 4.10, 5.58, 2.51, 0.57, 0.27, 
    0.23, 0.21, 0.24, 0.24, 0.20, 0.24, 0.32, 0.26, 0.16, 0.12, 
    0.09
]
wls_tl84 = np.arange(380, 785, 5)
custom_tl84 = colour.SpectralDistribution(dict(zip(wls_tl84, datacolor_tl84_vals)), name='Datacolor_TL84')

LIGHT_MAP = {
    "D65": colour.SDS_ILLUMINANTS.get('D65'),
    "A": colour.SDS_ILLUMINANTS.get('A'),
    "CWF (FL2)": colour.SDS_ILLUMINANTS.get('FL2'),
    "TL84 (FL11)": custom_tl84
}

def get_ks(reflectance):
    return (1 - reflectance)**2 / (2 * reflectance)

def get_ks_normalized(spectrum_map):
    target_wls = np.arange(360, 710, 10)
    sorted_items = sorted(spectrum_map.items(), key=lambda x: int(x[0]))
    existing_wls = np.array([int(k) for k, v in sorted_items])
    existing_vals = np.array([float(v) for k, v in sorted_items])
    normalized_vals = np.interp(target_wls, existing_wls, existing_vals)
    return get_ks(normalized_vals)

blank_r_str = "61.487896,64.536758,67.636276,70.483246,73.516251,75.622711,77.759293,79.583626,80.990044,82.235336,83.458176,84.331772,85.404106,86.164101,86.926323,87.612724,88.086739,88.541801,88.927353,89.348244,89.645943,89.882187,90.113014,90.397278,90.583130,90.746536,90.858932,91.020134,91.199127,91.403587,91.537102,91.670677,91.884819,91.980095,92.083275"
blank_r = np.array([float(x.strip()) / 100.0 for x in blank_r_str.split(',') if x.strip()])
blank_ks = get_ks(blank_r)


# ==========================================
# 2. Streamlit 웹 UI 구성
# ==========================================
# 사이드바 고정
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="T/S Colordata")

# 사이드바 닫기 숨김 & 여백 조절
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] div.stButton { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------
# 왼쪽 사이드바 (염료 순정 버튼 리스트)
# ------------------------------------------
with st.sidebar:
    st.markdown("### 🎨 전체 염료 리스트")
    st.caption("클릭하여 선택 / 해제하세요.")
    
    # 엑셀 순서대로 출력하며, 표시명(display_name)을 버튼에 노출
    for raw_name, display_name in all_dyes_ordered:
        btn_type = "primary" if raw_name in st.session_state.selected_dyes else "secondary"
        st.button(
            display_name, # 화면엔 B열 이름
            key=f"dye_{raw_name}", # 고유 식별자는 A열 이름(오류 방지)
            use_container_width=True, 
            type=btn_type,
            on_click=toggle_dye,
            args=(raw_name,) # 처리도 A열 이름 기준으로 수행
        )

# 메인 화면 좌우 분할
col_menu, col_results = st.columns([1.2, 2], gap="large")

# ------------------------------------------
# 메인 좌측 컬럼 (옵션 설정 영역)
# ------------------------------------------
with col_menu:
    st.subheader("⚙️ 검색 옵션 설정")
    
    # 1. QTX 파일 업로드 및 색상 미리보기
    upload_col, color_col = st.columns([2.5, 1])
    
    with upload_col:
        uploaded_file = st.file_uploader(
            "QTX 파일 업로드", 
            type=['qtx'], 
            label_visibility="collapsed", 
            key="qtx_uploader"
        )
    
    target_r = None
    hex_color = None
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode('euc-kr') 
            r_part = content.split("STD_R=")[1].split("\n")[0]
            raw_r_vals = [float(x.strip()) / 100.0 for x in r_part.split(',') if x.strip()]
            
            start_wl = 400 if len(raw_r_vals) == 31 else 360
            for line in content.split('\n'):
                if "STD_REFLLOW=" in line:
                    start_wl = int(line.split("=")[1].replace(',', '').strip())
                    break
            
            current_wls = np.array([start_wl + i * 10 for i in range(len(raw_r_vals))])
            target_wls = np.arange(360, 710, 10)
            
            target_r = np.interp(target_wls, current_wls, raw_r_vals)
            
            shape_400 = colour.SpectralShape(400, 700, 10)
            wls_400 = np.arange(400, 710, 10)
            viz_wavelengths = dict(zip(wls_400, target_r[4:35])) 
            target_sd_viz = colour.SpectralDistribution(viz_wavelengths).align(shape_400)
            cmfs_viz = colour.MSDS_CMFS['CIE 1964 10 Degree Standard Observer'].copy().align(shape_400)
            ill_viz = LIGHT_MAP["D65"].copy().align(shape_400)
            
            XYZ_viz = colour.sd_to_XYZ(target_sd_viz, cmfs_viz, ill_viz) / 100.0
            white_sd = colour.SpectralDistribution(dict(zip(shape_400.range(), np.ones(len(shape_400))))).align(shape_400)
            wp_D65 = colour.XYZ_to_xy(colour.sd_to_XYZ(white_sd, cmfs_viz, ill_viz) / 100.0)
            RGB_viz = colour.XYZ_to_sRGB(XYZ_viz, illuminant=wp_D65)
            RGB_viz = np.clip(RGB_viz, 0, 1) 
            hex_color = "#{:02x}{:02x}{:02x}".format(int(RGB_viz[0]*255), int(RGB_viz[1]*255), int(RGB_viz[2]*255))
                
        except Exception as e:
            st.error(f"QTX 분석 오류: {e}")

    with color_col:
        if hex_color is not None:
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; margin-top: 5px;">
                    <div style="width: 100%; height: 50px; background-color: {hex_color}; border: 1px solid #ccc; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);"></div>
                    <div style="font-size: 11px; font-weight: bold; margin-top: 4px; color: #555;">{hex_color.upper()}</div>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; margin-top: 5px;">
                    <div style="width: 100%; height: 50px; background-color: #f0f2f6; border: 1px dashed #ccc; border-radius: 8px;"></div>
                    <div style="font-size: 11px; margin-top: 4px; color: #999;">미리보기</div>
                </div>
                """, unsafe_allow_html=True
            )

    st.markdown("**💡 광원 우선순위 설정**")
    light_options_all = list(LIGHT_MAP.keys())
    light_options_optional = list(LIGHT_MAP.keys()) + ["없음"]
    none_index = light_options_optional.index("없음")
    
    l_col1, l_col2, l_col3 = st.columns(3)
    light1_name = l_col1.selectbox("1차 광원", light_options_all, index=0)
    light2_name = l_col2.selectbox("2차 광원", light_options_optional, index=none_index) 
    light3_name = l_col3.selectbox("3차 광원", light_options_optional, index=none_index) 

    st.markdown("---")

    st.markdown("**🧪 염료 선택 현황 및 실행**")
    st.markdown(f"선택된 염료: **{len(st.session_state.selected_dyes)}개**")
    
    st.button(
        "🔄 선택 전체 초기화", 
        use_container_width=True, 
        disabled=(len(st.session_state.selected_dyes) == 0),
        on_click=clear_dyes
    )

    run_search = False
    
    if target_r is None:
        st.button("🚀 처방 탐색 시작 (QTX 업로드 필요)", type="primary", use_container_width=True, disabled=True)
    elif len(st.session_state.selected_dyes) < 3:
        st.button("🚀 처방 탐색 시작 (염료 3개 이상 필요)", type="primary", use_container_width=True, disabled=True)
    else:
        run_search = st.button("🚀 처방 탐색 시작", type="primary", use_container_width=True)

# ------------------------------------------
# 메인 우측 컬럼 (결과 영역)
# ------------------------------------------
with col_results:
    st.header("🧪 T/S Colordata")

    if run_search:
        selected_pool = st.session_state.selected_dyes
        combos = list(itertools.combinations(selected_pool, 3))
        
        active_lights = [light1_name]
        if light2_name != "없음": active_lights.append(light2_name)
        if light3_name != "없음": active_lights.append(light3_name)
        
        progress_text = "조합을 계산하고 있습니다..."
        my_bar = st.progress(0, text=progress_text)
        
        results = []
        
        for idx, combo in enumerate(combos):
            # 화면 안내에도 맵핑된 이름을 보여주기 위해 변환
            combo_display_names = [display_name_dict.get(name, name) for name in combo]
            my_bar.progress(
                (idx + 1) / len(combos), 
                text=f"계산 중: {combo_display_names[0]}, {combo_display_names[1]}, {combo_display_names[2]} ({idx+1}/{len(combos)})"
            )
            
            unit_ks_list = []
            valid_combo = True
            for name in combo:
                available_concs = np.array([float(k) for k in dye_db[name].keys() if float(k) > 0])
                if len(available_concs) == 0:
                    valid_combo = False
                    break
                ref_conc = available_concs[np.argmin(np.abs(available_concs - 1.0))]
                ref_key = [k for k in dye_db[name].keys() if float(k) == ref_conc][0]
                spectrum_map = dye_db[name][ref_key]
                ref_ks_total = get_ks_normalized(spectrum_map)
                ref_ks_net = np.maximum(ref_ks_total - blank_ks, 0)
                unit_ks_list.append(ref_ks_net / ref_conc)
            
            if not valid_combo:
                continue

            def evaluate_lights_local(conc, return_lab=False):
                total_ks = np.copy(blank_ks)
                for i in range(len(combo)):
                    total_ks += unit_ks_list[i] * conc[i]
                
                est_r = 1 + total_ks - np.sqrt(total_ks**2 + 2 * total_ks)
                shape_5nm = colour.SpectralShape(380, 780, 5)
                start_idx = 4 
                wls_400 = np.arange(400, 710, 10)
                wavelengths = dict(zip(wls_400, est_r[start_idx:35]))
                
                target_wavelengths = dict(zip(wls_400, target_r[start_idx:35]))
                
                est_sd = colour.SpectralDistribution(wavelengths).align(shape_5nm)
                target_sd = colour.SpectralDistribution(target_wavelengths).align(shape_5nm)
                white_sd = colour.SpectralDistribution(dict(zip(shape_5nm.range(), np.ones(len(shape_5nm.range())))))
                cmfs = colour.MSDS_CMFS['CIE 1964 10 Degree Standard Observer'].copy().align(shape_5nm)
                
                des = []
                labs = [] 
                for l_name in active_lights:
                    light_spd = LIGHT_MAP[l_name].copy().align(shape_5nm)
                    wp_XYZ = colour.sd_to_XYZ(white_sd, cmfs, light_spd, method='Integration') / 100.0
                    wp_xy = colour.XYZ_to_xy(wp_XYZ)
                    XYZ_est = colour.sd_to_XYZ(est_sd, cmfs, light_spd, method='Integration') / 100.0
                    XYZ_tgt = colour.sd_to_XYZ(target_sd, cmfs, light_spd, method='Integration') / 100.0
                    lab_est = colour.XYZ_to_Lab(XYZ_est, illuminant=wp_xy)
                    lab_tgt = colour.XYZ_to_Lab(XYZ_tgt, illuminant=wp_xy)
                    de = colour.delta_E(lab_est, lab_tgt, method='CMC', l=2, c=1)
                    des.append(de)
                    labs.append((lab_est, lab_tgt))
                    
                if return_lab:
                    return des, labs
                return des

            def objective_local(conc):
                des, labs = evaluate_lights_local(conc, return_lab=True)
                lab_est, lab_tgt = labs[0] 
                return (lab_est[0] - lab_tgt[0])**2 + (lab_est[1] - lab_tgt[1])**2 + (lab_est[2] - lab_tgt[2])**2

            bnds = [(0.0001, 10), (0.0001, 10), (0.0001, 10)]
            res = minimize(
                objective_local, 
                x0=[0.1, 0.1, 0.1], 
                bounds=bnds,
                method='SLSQP',
                options={'ftol': 1e-6, 'disp': False}
            )
            
            if res.success:
                final_des = evaluate_lights_local(res.x)
                if final_des[0] < 0.5:
                    metamerism_index = sum(final_des[1:]) if len(final_des) > 1 else 0
                    results.append({
                        'combo': combo,
                        'conc': res.x,
                        'des': final_des,
                        'metamerism': metamerism_index,
                        'total_conc': sum(res.x)
                    })

        my_bar.empty() 
        
        if len(results) > 0:
            st.success(f"총 {len(combos)}개의 조합 중 {len(results)}개의 유효한 처방을 찾았습니다!")
            
            results.sort(key=lambda x: x['metamerism'])
            top_results = results[:10]
            
            row_labels = [f"dE(CMC) {light1_name} (Primary)"]
            if light2_name != "없음": row_labels.append(f"Metamerism {light2_name}")
            if light3_name != "없음": row_labels.append(f"Metamerism {light3_name}")
            row_labels.append("Total concentration [%]")
            
            # 최종 데이터 표 헤더에도 엑셀의 표시명(display_name) 반영
            row_labels.extend([display_name_dict.get(dye, dye) for dye in selected_pool])
            
            df_dict = {"Property / Dyestuff": row_labels}
            
            for rank, res in enumerate(top_results):
                col_name = f"{rank+1}(3)"
                col_data = []
                
                col_data.append(f"{res['des'][0]:.2f}") 
                
                light_idx = 1
                if light2_name != "없음":
                    col_data.append(f"{res['des'][light_idx]:.2f}") 
                    light_idx += 1
                if light3_name != "없음":
                    col_data.append(f"{res['des'][light_idx]:.2f}") 
                    
                col_data.append(f"{res['total_conc']:.4f}") 
                
                for dye in selected_pool:
                    if dye in res['combo']:
                        dye_idx = res['combo'].index(dye)
                        col_data.append(f"{res['conc'][dye_idx]:.4f}")
                    else:
                        col_data.append("")
                        
                df_dict[col_name] = col_data
            
            df = pd.DataFrame(df_dict)
            df.set_index("Property / Dyestuff", inplace=True)
            
            st.markdown("### 🏆 추천 처방 Top 10 (메타머리즘 최소 순)")
            
            def color_rows(s):
                if s.name.startswith('dE(CMC)'):
                    return ['background-color: #e6f2ff; font-weight: bold'] * len(s)
                elif s.name.startswith('Metamerism'):
                    return ['background-color: #fff9e6; color: #d97706'] * len(s)
                elif s.name == 'Total concentration [%]':
                    return ['background-color: #f3f4f6; font-weight: bold'] * len(s)
                else:
                    return [''] * len(s)
            
            styled_df = df.style.apply(color_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
        else:
            st.error("⚠️ 유효한 처방을 찾지 못했습니다. 타깃 색상이 현재 염료 풀로 구현하기 어렵거나, 농도 스케일을 벗어났을 수 있습니다.")
            
    elif not run_search and uploaded_file is None:
        st.info("👈 설정 메뉴에서 QTX 파일을 업로드해주세요.")