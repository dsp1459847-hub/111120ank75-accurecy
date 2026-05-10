import pandas as pd
import streamlit as st
import io

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="MAYA AI: DUAL MASTER v35.1")

# --- Custom Styling (STRICTLY NO LOGIC CHANGE) ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 11px; padding: 4px; text-align: center; border: 1px solid #444; border-radius: 3px; font-weight: bold; }
    .v33-box { background: #1A237E; color: white; border-left: 3px solid #FFD700; }
    .v24-box { background: #263238; color: #00E676; border-left: 3px solid #00E676; }
    .super-hit { background: radial-gradient(circle, #FFD700, #FFA000) !important; color: black !important; box-shadow: 0px 0px 8px #FFD700; }
    .vvip-match { border: 2px solid #FF5252 !important; background: #FFEBEE !important; color: #B71C1C !important; }
    .conf-meter { background: #111; color: gold; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 15px; border: 1px solid gold; font-size: 18px; }
    .accuracy-tag { background: #004D40; color: #00E676; padding: 4px 10px; border-radius: 4px; font-size: 14px; margin-bottom: 10px; display: inline-block; border: 1px solid #00E676;}
    </style>
    """, unsafe_allow_html=True)

# --- INTERNAL LOGIC DATA (UNCHANGED) ---
MASTER_RULES = {
    'DS': {1:['0','5'], 2:['1','6','9'], 3:['2','7','3'], 4:['4','8','0']},
    'FD': {1:['4','9','2'], 2:['0','5','7'], 3:['1','6','3'], 4:['8','2','9']},
    'GD': {1:['1','6','0'], 2:['3','8','5'], 3:['4','9','7'], 4:['2','7','1']},
    'GL': {1:['7','2','4'], 2:['1','6','0'], 3:['5','9','3'], 4:['8','4','2']},
    'DB': {1:['3','8','2'], 2:['1','6','4'], 3:['0','5','9'], 4:['7','4','1']},
    'SG': {1:['2','7','4'], 2:['3','8','0'], 3:['1','6','5'], 4:['9','0','2']}
}

SHIFT_STRENGTH = {
    'DS': {'Days': ['Tuesday', 'Thursday'], 'Weeks': [2, 4], 'Dates': [1, 11, 21, 31]},
    'FD': {'Days': ['Wednesday', 'Friday'], 'Weeks': [1, 3], 'Dates': [4, 9, 14, 19]},
    'GD': {'Days': ['Monday', 'Saturday'], 'Weeks': [2, 3], 'Dates': [3, 8, 13, 18]},
    'GL': {'Days': ['Tuesday', 'Wednesday'], 'Weeks': [1, 4], 'Dates': [7, 17, 27]},
    'DB': {'Days': ['Monday', 'Friday'], 'Weeks': [3], 'Dates': [5, 15, 25]},
    'SG': {'Days': ['Thursday', 'Sunday'], 'Weeks': [2], 'Dates': [2, 12, 22]}
}

def clean_val(val):
    if pd.isna(val): return ""
    v = "".join(filter(str.isdigit, str(val)))
    return v.zfill(2)[-2:] if v else ""

def get_week_num(dt):
    d = dt.day
    return 4 if d > 21 else (d-1)//7 + 1

def calculate_confidence(s_name, t_date):
    day, week, dt = t_date.strftime('%A'), get_week_num(t_date), t_date.day
    score = 40
    if day in SHIFT_STRENGTH[s_name]['Days']: score += 15
    if week in SHIFT_STRENGTH[s_name]['Weeks']: score += 10
    if dt in SHIFT_STRENGTH[s_name]['Dates']: score += 10
    return min(score, 95)

def apply_32(v):
    v = clean_val(v)
    if not v or len(v) != 2: return set()
    A, B = int(v[0]), int(v[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

@st.cache_data
def run_engine(df_json, t_date_str, target_shift, engine_ver):
    df = pd.read_json(io.StringIO(df_json))
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    df['DS'] = df['DS'].shift(-1)
    
    t_date = pd.to_datetime(t_date_str)
    hist = df[df['DATE'] < t_date].tail(365)
    serial_hits = []
    for src in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']:
        for lb in range(1, 61):
            hits = sum(1 for i in range(len(hist)-1, 60, -4) if clean_val(hist.iloc[i][target_shift]) in apply_32(clean_val(hist.iloc[i-lb][src])))
            if hits > 0: serial_hits.append(((src, lb), hits))
    
    serial_hits.sort(key=lambda x: x[1], reverse=True)
    toppers, losers = (serial_hits[:4], serial_hits[-7:]) if engine_ver == 'v33' else (serial_hits[:4], serial_hits[-5:])
    
    curr_h = df[df['DATE'] < t_date]
    top_p = set().union(*(apply_32(clean_val(curr_h.iloc[-lb][src])) for (src, lb), h in toppers))
    min_p = set().union(*(apply_32(clean_val(curr_h.iloc[-lb][src])) for (src, lb), h in losers))
    final = top_p - min_p
    
    if engine_ver == 'v33':
        week = get_week_num(t_date)
        gold = {p for p in final if any(d in p for d in MASTER_RULES[target_shift][week])}
        return final, gold
    return final, set()

# --- SIDEBAR (FREEZE AREA) ---
with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    uploaded_file = st.file_uploader("Upload Master File", type=['xlsx', 'csv'])
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_raw['DATE'] = pd.to_datetime(df_raw['DATE'])
        t_date = st.date_input("Target Date", df_raw['DATE'].max())
        df_json = df_raw.to_json()
        st.success("File & Date Locked")

# --- MAIN APP ---
if uploaded_file:
    conf_total = sum(calculate_confidence(s, t_date) for s in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']) // 6
    st.markdown(f"<div class='conf-meter'>📅 DATE: {t_date.strftime('%d-%b-%Y')} | AVG MARKET CONFIDENCE: {conf_total}%</div>", unsafe_allow_html=True)

    tabs = st.tabs(["DS", "FD", "GD", "GL", "DB", "SG"])
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']

    for idx, s_name in enumerate(shifts):
        with tabs[idx]:
            c_score = calculate_confidence(s_name, t_date)
            st.markdown(f"<div class='accuracy-tag'>🎯 Shift Confidence: {c_score}% (Week: {get_week_num(t_date)} | Day: {t_date.strftime('%a')})</div>", unsafe_allow_html=True)
            
            p33, g33 = run_engine(df_json, str(t_date), s_name, 'v33')
            p24, _ = run_engine(df_json, str(t_date), s_name, 'v24')
            common = p33.intersection(p24)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Engine v33 (7-Year Master)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p33)):
                    cls = "item-box v33-box " + ("super-hit" if p in g33 else "")
                    if p in common: cls += " vvip-match"
                    h += f"<div class='{cls}'>{p}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)
            with col2:
                st.markdown("**Engine v24 (Historical Audit)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p24)):
                    cls = "item-box v24-box " + ("vvip-match" if p in common else "")
                    h += f"<div class='{cls}'>{p}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)

            st.warning(f"🏆 VVIP Common ({len(common)}): {', '.join(sorted(list(common)))}")
            
            st.markdown("---")
            b1, b2 = st.columns(2)
            # FIX: `.date()` error fixed here by using `prev` directly
            if b1.button(f"📊 Load v33 History ({s_name})"):
                for i in range(1, 12): # 11 din ki history
                    prev = t_date - pd.Timedelta(days=i)
                    p, _ = run_engine(df_json, str(prev), s_name, 'v33')
                    row = df_raw[df_raw['DATE'] == pd.to_datetime(prev)]
                    val = clean_val(row[s_name].values[0]) if not row.empty else ""
                    st.write(f"{prev.strftime('%d-%m')} (Week {get_week_num(prev)}): {'✅ ' + val if val in p and val != '' else val}")
            
            if b2.button(f"📊 Load v24 History ({s_name})"):
                for i in range(1, 12): # 11 din ki history
                    prev = t_date - pd.Timedelta(days=i)
                    p, _ = run_engine(df_json, str(prev), s_name, 'v24')
                    row = df_raw[df_raw['DATE'] == pd.to_datetime(prev)]
                    val = clean_val(row[s_name].values[0]) if not row.empty else ""
                    st.write(f"{prev.strftime('%d-%m')}: {'✅ ' + val if val in p and val != '' else val}")
    
