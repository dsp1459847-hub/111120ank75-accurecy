import pandas as pd
import streamlit as st
import io

# --- Page Config ---
st.set_page_config(layout="wide", page_title="MAYA AI: DUAL ENGINE TRIPLE AUDIT")

# --- Custom Styling (Fixed Logic - No Changes) ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 11px; padding: 4px; text-align: center; border: 1px solid #444; border-radius: 3px; font-weight: bold; }
    .v33-box { background: #1A237E; color: white; border-left: 3px solid #FFD700; }
    .v24-box { background: #263238; color: #00E676; border-left: 3px solid #00E676; }
    .super-hit { background: radial-gradient(circle, #FFD700, #FFA000) !important; color: black !important; box-shadow: 0px 0px 8px #FFD700; }
    .vvip-match { border: 2px solid #FF5252 !important; background: #FFEBEE !important; color: #B71C1C !important; }
    .audit-box { border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #fdfdfd; margin-bottom: 10px; }
    .pass-tick { color: #2E7D32; font-weight: bold; }
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

# --- SIDEBAR (FREEZE) ---
with st.sidebar:
    st.header("⚙️ Controls")
    uploaded_file = st.file_uploader("Upload File")
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_raw['DATE'] = pd.to_datetime(df_raw['DATE'])
        t_date = st.date_input("Target Date", df_raw['DATE'].max())
        df_json = df_raw.to_json()

# --- MAIN APP ---
if uploaded_file:
    tabs = st.tabs(["DS", "FD", "GD", "GL", "DB", "SG"])
    for idx, s_name in enumerate(["DS", "FD", "GD", "GL", "DB", "SG"]):
        with tabs[idx]:
            p33, g33 = run_engine(df_json, str(t_date), s_name, 'v33')
            p24, _ = run_engine(df_json, str(t_date), s_name, 'v24')
            common = p33.intersection(p24)
            actual = clean_val(df_raw[df_raw['DATE'] == pd.to_datetime(t_date)][s_name].values[0]) if not df_raw[df_raw['DATE'] == pd.to_datetime(t_date)].empty else ""
            
            st.markdown(f"### Result: {actual}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Engine v33 (7-Year)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p33)):
                    cls = "item-box v33-box " + ("super-hit" if p in g33 else "")
                    if p in common: cls += " vvip-match"
                    h += f"<div class='{cls}'>{p}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)
            with c2:
                st.markdown("**Engine v24 (Audit)**")
                h = "<div class='compact-grid'>"
                for p in sorted(list(p24)):
                    cls = "item-box v24-box " + ("vvip-match" if p in common else "")
                    h += f"<div class='{cls}'>{p}</div>"
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)

            # --- DUAL ENGINE TRIPLE HISTORY ---
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            show_h33 = col_b1.button(f"🔍 v33 Triple Audit ({s_name})")
            show_h24 = col_b2.button(f"🔍 v24 Triple Audit ({s_name})")

            if show_h33 or show_h24:
                h1, h2 = st.columns(2)
                # Engine v33 History
                if show_h33:
                    with h1:
                        st.info("v33 Historical Triple Audit")
                        for title, dates in [("Recent 11 Days", [t_date - pd.Timedelta(days=i) for i in range(1, 12)]),
                                           (f"Weekday ({t_date.strftime('%A')})", df_raw[(df_raw['DATE'].dt.day_name()==t_date.strftime('%A')) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(7)['DATE']),
                                           (f"Date ({t_date.day})", df_raw[(df_raw['DATE'].dt.day==t_date.day) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE'])]:
                            st.subheader(title)
                            for d in dates:
                                p, _ = run_engine(df_json, str(d), s_name, 'v33')
                                val = clean_val(df_raw[df_raw['DATE'] == pd.to_datetime(d)][s_name].values[0])
                                st.write(f"{d.strftime('%d-%m')} : {'✅ ' + val if val in p and val != '' else val}")

                # Engine v24 History
                if show_h24:
                    with h2:
                        st.info("v24 Historical Triple Audit")
                        for title, dates in [("Recent 11 Days", [t_date - pd.Timedelta(days=i) for i in range(1, 12)]),
                                           (f"Weekday ({t_date.strftime('%A')})", df_raw[(df_raw['DATE'].dt.day_name()==t_date.strftime('%A')) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(7)['DATE']),
                                           (f"Date ({t_date.day})", df_raw[(df_raw['DATE'].dt.day==t_date.day) & (df_raw['DATE']<pd.to_datetime(t_date))].tail(5)['DATE'])]:
                            st.subheader(title)
                            for d in dates:
                                p, _ = run_engine(df_json, str(d), s_name, 'v24')
                                val = clean_val(df_raw[df_raw['DATE'] == pd.to_datetime(d)][s_name].values[0])
                                st.write(f"{d.strftime('%d-%m')} : {'✅ ' + val if val in p and val != '' else val}")
                
