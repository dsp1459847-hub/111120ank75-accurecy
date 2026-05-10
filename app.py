import pandas as pd
import streamlit as st
import io

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="MAYA AI: PARALLEL HISTORY v35.10")

# --- Custom Styling (Bold & Dark) ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 3px; }
    .item-box { font-size: 14px; padding: 6px; text-align: center; border-radius: 4px; font-weight: 900; border: 1px solid #444; }
    .v33-box { background-color: #0D47A1; color: #FFD600; } 
    .v24-box { background-color: #1B5E20; color: #CCFF90; } 
    .super-hit { background: linear-gradient(135deg, #FFD600, #FFA000) !important; color: #000 !important; border: 2px solid #fff !important; }
    .vvip-match { border: 2px solid #FF5252 !important; box-shadow: 0px 0px 5px #FF5252; }
    
    .header-info { background: #000; color: gold; padding: 10px; border-radius: 8px; text-align: center; border: 2px solid gold; margin-bottom: 10px; font-weight: bold; }
    .pass-status { color: #00FF00; font-weight: bold; border: 1px solid #00FF00; padding: 2px 8px; border-radius: 4px; font-size: 16px; margin-left: 10px; }
    .fail-status { color: #FF5252; font-weight: bold; border: 1px solid #FF5252; padding: 2px 8px; border-radius: 4px; font-size: 16px; margin-left: 10px; }
    .pass-tick { color: #00FF00; font-weight: 900; }

    /* History Layout */
    .history-card { background: #f8f9fa; border: 1px solid #ccc; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: #000; }
    .engine-col { width: 49%; display: inline-block; vertical-align: top; border-right: 1px solid #eee; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- INTERNAL LOGIC (STRICTLY NO CHANGE) ---
MASTER_RULES = {
    'DS': {1:['0','5'], 2:['1','6','9'], 3:['2','7','3'], 4:['4','8','0']},
    'FD': {1:['4','9','2'], 2:['0','5','7'], 3:['1','6','3'], 4:['8','2','9']},
    'GD': {1:['1','6','0'], 2:['3','8','5'], 3:['4','9','7'], 4:['2','7','1']},
    'GL': {1:['7','2','4'], 2:['1','6','0'], 3:['5','9','3'], 4:['8','4','2']},
    'DB': {1:['3','8','2'], 2:['1','6','4'], 3:['0','5','9'], 4:['7','4','1']},
    'SG': {1:['2','7','4'], 2:['3','8','0'], 3:['1','6','5'], 4:['9','0','2']}
}

def clean_val(val):
    if pd.isna(val): return ""
    v = "".join(filter(str.isdigit, str(val)))
    return v.zfill(2)[-2:] if v else ""

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
        d = t_date.day
        week = 4 if d > 21 else (d-1)//7 + 1
        gold = {p for p in final if any(x in p for x in MASTER_RULES[target_shift][week])}
        return final, gold
    return final, set()

# --- SIDEBAR ---
with st.sidebar:
    uploaded_file = st.file_uploader("Upload File", type=['xlsx', 'csv'])
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_raw['DATE'] = pd.to_datetime(df_raw['DATE'])
        t_date = st.date_input("Target Date", df_raw['DATE'].max())
        df_json = df_raw.to_json()

# --- MAIN APP ---
if uploaded_file:
    st.markdown(f"<div class='header-info'>📅 {t_date.strftime('%d-%b-%Y')} DASHBOARD</div>", unsafe_allow_html=True)
    tabs = st.tabs(["DS", "FD", "GD", "GL", "DB", "SG"])
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']

    for idx, s_name in enumerate(shifts):
        with tabs[idx]:
            actual_row = df_raw[df_raw['DATE'] == pd.to_datetime(t_date)]
            actual = clean_val(actual_row[s_name].values[0]) if not actual_row.empty else ""
            p33, g33 = run_engine(df_json, str(t_date), s_name, 'v33')
            p24, _ = run_engine(df_json, str(t_date), s_name, 'v24')
            common = p33.intersection(p24)
            
            # Result Section with Pass/Fail Label
            status_33 = f"<span class='pass-status'>v33: PASS ✅</span>" if actual in p33 and actual!="" else f"<span class='fail-status'>v33: FAIL ❌</span>"
            status_24 = f"<span class='pass-status'>v24: PASS ✅</span>" if actual in p24 and actual!="" else f"<span class='fail-status'>v24: FAIL ❌</span>"
            
            st.markdown(f"### RESULT: <span style='color:gold'>{actual if actual else '--'}</span> {status_33} {status_24}", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Engine v33 (Golden)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p33)):
                    cls = "item-box v33-box " + ("super-hit" if p in g33 else "")
                    if p in common: cls += " vvip-match"
                    tick = " ✅" if (p == actual and actual != "") else ""
                    h += f"<div class='{cls}'>{p}{tick}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)
            with col2:
                st.markdown("**Engine v24 (Audit)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p24)):
                    cls = "item-box v24-box " + ("vvip-match" if p in common else "")
                    tick = " ✅" if (p == actual and actual != "") else ""
                    h += f"<div class='{cls}'>{p}{tick}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)

    # --- PARALLEL HISTORY SECTION ---
    st.markdown("---")
    st.subheader("📋 DEEP AUDIT HISTORY (v33 & v24 Parallel)")
    
    if st.button("🚀 LOAD HISTORY"):
        for s_name in shifts:
            st.markdown(f"<div class='history-card'>", unsafe_allow_html=True)
            st.markdown(f"### 🎰 {s_name} Audit", unsafe_allow_html=True)
            
            # Side-by-Side Containers
            st.markdown("<div style='display:flex; gap:10px;'>", unsafe_allow_html=True)
            
            # Left: v33
            st.markdown("<div class='engine-col'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#0D47A1;'>Engine v33</h4>", unsafe_allow_html=True)
            for title, dates in [("Recent 11D", [t_date - pd.Timedelta(days=i) for i in range(1, 12)]),
                               (f"War ({t_date.strftime('%a')})", df_raw[(df_raw['DATE'].dt.day_name()==t_date.strftime('%A')) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE']),
                               (f"Date ({t_date.day})", df_raw[(df_raw['DATE'].dt.day==t_date.day) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE'])]:
                st.write(f"**{title}**")
                for d in dates:
                    p_h, _ = run_engine(df_json, str(pd.to_datetime(d).date()), s_name, 'v33')
                    val_h = clean_val(df_raw[df_raw['DATE'] == pd.to_datetime(d)][s_name].values[0])
                    tick = " <span class='pass-tick'>✅</span>" if (val_h in p_h and val_h != "") else ""
                    st.markdown(f"{pd.to_datetime(d).strftime('%d-%m')} : **{val_h}**{tick}", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Right: v24
            st.markdown("<div class='engine-col' style='border-right:none;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#1B5E20;'>Engine v24</h4>", unsafe_allow_html=True)
            for title, dates in [("Recent 11D", [t_date - pd.Timedelta(days=i) for i in range(1, 12)]),
                               (f"War ({t_date.strftime('%a')})", df_raw[(df_raw['DATE'].dt.day_name()==t_date.strftime('%A')) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE']),
                               (f"Date ({t_date.day})", df_raw[(df_raw['DATE'].dt.day==t_date.day) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE'])]:
                st.write(f"**{title}**")
                for d in dates:
                    p_h, _ = run_engine(df_json, str(pd.to_datetime(d).date()), s_name, 'v24')
                    val_h = clean_val(df_raw[df_raw['DATE'] == pd.to_datetime(d)][s_name].values[0])
                    tick = " <span class='pass-tick'>✅</span>" if (val_h in p_h and val_h != "") else ""
                    st.markdown(f"{pd.to_datetime(d).strftime('%d-%m')} : **{val_h}**{tick}", unsafe_allow_html=True)
            st.markdown("</div></div></div>", unsafe_allow_html=True)
            
