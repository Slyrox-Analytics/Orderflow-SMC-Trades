
import io
import os
from datetime import datetime
import pandas as pd
import streamlit as st

from gh_store import GHStore

st.set_page_config(page_title="Orderflow Trade Stats", page_icon="⚡", layout="wide")

# --- Config from secrets (Streamlit Cloud) or env (local) ---
TOKEN  = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
OWNER  = st.secrets.get("REPO_OWNER",   os.getenv("REPO_OWNER", ""))
REPO   = st.secrets.get("REPO_NAME",    os.getenv("REPO_NAME", ""))
BRANCH = st.secrets.get("BRANCH",       os.getenv("BRANCH", "main"))

USE_GITHUB = bool(TOKEN and OWNER and REPO and BRANCH)
STORE = GHStore(TOKEN, OWNER, REPO, BRANCH) if USE_GITHUB else None

CSV_PATH = "data/journal.csv"

st.sidebar.success("GitHub Storage aktiv" if USE_GITHUB else "Lokaler CSV-Fallback (kein Token)")

# --- Helpers ---
def load_csv() -> pd.DataFrame:
    if USE_GITHUB:
        content, _ = STORE.get_file(CSV_PATH)
        if content is None:
            return pd.DataFrame(columns=[
                "date","time","session","symbol","direction","bias","level",
                "entry","stop","take_profit","exit","result","rr","comment","screenshot_path"
            ])
        return pd.read_csv(io.StringIO(content))
    else:
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH)
        return pd.DataFrame(columns=[
            "date","time","session","symbol","direction","bias","level",
            "entry","stop","take_profit","exit","result","rr","comment","screenshot_path"
        ])

def save_csv(df: pd.DataFrame):
    csv_str = df.to_csv(index=False)
    if USE_GITHUB:
        # get sha if exists
        _, sha = STORE.get_file(CSV_PATH)
        STORE.put_file(CSV_PATH, csv_str, message="chore: update journal.csv", sha=sha)
    else:
        os.makedirs("data", exist_ok=True)
        with open(CSV_PATH, "w", encoding="utf-8") as f:
            f.write(csv_str)

def detect_session(local_time: str) -> str:
    h, m = map(int, local_time.split(":"))
    t = h*60 + m
    if 8*60 <= t <= 12*60: return "London"
    if 14*60+30 <= t <= 18*60: return "New York"
    return "Other"

def compute_rr(entry, stop, tp):
    try:
        risk = abs(entry - stop)
        reward = abs(tp - entry)
        if risk == 0: return None
        return round(reward / risk, 2)
    except Exception:
        return None

# --- UI ---
st.title("⚡ Scalper Journal — Streamlit + GitHub")

page = st.sidebar.radio("Navigation", ["Trade erfassen", "Journal & Filter", "Stats & Export"])

if page == "Trade erfassen":
    st.header("Trade erfassen")
    c1,c2,c3 = st.columns(3)
    with c1:
        d = st.date_input("Datum", value=datetime.now().date())
    with c2:
        tm = st.time_input("Uhrzeit (lokal)", value=datetime.now().time().replace(second=0, microsecond=0))
    with c3:
        symbol = st.selectbox("Symbol", ["BTCUSDT.P","ETHUSDT.P","NAS100","ES","GOLD"], index=0)

    c4,c5,c6,c7 = st.columns(4)
    with c4:
        direction = st.selectbox("Richtung", ["Long","Short"])
    with c5:
        bias = st.selectbox("Tagesbias", ["Bullish","Bearish","Neutral"], index=0)
    with c6:
        level = st.selectbox("Zone/Level", ["FVG","Orderblock","Liquidity Sweep","Reclaim","Breakout","Retest"])
    with c7:
        comment = st.text_input("Kurzkommentar (optional)")

    c8,c9,c10 = st.columns(3)
    with c8:
        entry = st.number_input("Entry", step=0.5, format="%.2f")
    with c9:
        stop = st.number_input("Stop", step=0.5, format="%.2f")
    with c10:
        tp = st.number_input("Take Profit", step=0.5, format="%.2f")

    rr = compute_rr(entry, stop, tp) if entry and stop and tp else None
    st.markdown(f"**R:R (auto):** {rr if rr is not None else '—'}")

    shot = st.file_uploader("Screenshot (optional)", type=["png","jpg","jpeg","webp"])

    if st.button("Speichern ✅", use_container_width=True):
        if not (entry and stop and tp):
            st.warning("Bitte Entry, Stop und TP angeben.")
        else:
            df = load_csv()
            date_str = d.strftime("%Y-%m-%d")
            time_str = tm.strftime("%H:%M")
            session = detect_session(time_str)
            screenshot_path = ""

            # upload screenshot to GitHub if configured
            if shot is not None:
                fname = f"data/screenshots/{date_str}_{time_str.replace(':','')}_{shot.name}"
                if USE_GITHUB:
                    STORE.upload_binary(fname, shot.getbuffer(), message=f"feat: add screenshot {fname}")
                    screenshot_path = fname
                else:
                    os.makedirs("data/screenshots", exist_ok=True)
                    with open(fname, "wb") as f:
                        f.write(shot.getbuffer())
                    screenshot_path = fname

            new_row = {
                "date": date_str,
                "time": time_str,
                "session": session,
                "symbol": symbol,
                "direction": direction,
                "bias": bias,
                "level": level,
                "entry": float(entry),
                "stop": float(stop),
                "take_profit": float(tp),
                "exit": None,
                "result": None,
                "rr": rr,
                "comment": comment,
                "screenshot_path": screenshot_path
            }
            df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
            save_csv(df)
            st.success("Gespeichert (Commit erstellt)")

elif page == "Journal & Filter":
    st.header("Journal & Filter")
    df = load_csv()
    if df.empty:
        st.info("Noch keine Trades.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            date_from = st.date_input("Von", value=pd.to_datetime(df["date"]).min().date())
        with c2:
            date_to = st.date_input("Bis", value=datetime.now().date())
        with c3:
            f_session = st.multiselect("Session", ["London","New York","Other"], default=["London","New York","Other"])
        with c4:
            f_dir = st.multiselect("Richtung", ["Long","Short"], default=["Long","Short"])

        mask = (pd.to_datetime(df["date"]).dt.date >= date_from) & (pd.to_datetime(df["date"]).dt.date <= date_to)
        mask &= df["session"].isin(f_session) & df["direction"].isin(f_dir)
        sdf = df.loc[mask].copy()

        st.dataframe(sdf, use_container_width=True)

        st.subheader("Exit / Ergebnis speichern")
        if not sdf.empty:
            idx = st.selectbox("Zeile auswählen (Index)", sdf.index.tolist())
            exit_price = st.number_input("Exit-Preis", step=0.5, format="%.2f")
            if st.button("Update 💾"):
                base_df = load_csv()
                base_df.loc[idx, "exit"] = float(exit_price)
                # compute result
                dirn = base_df.loc[idx, "direction"]
                entry = float(base_df.loc[idx, "entry"])
                res = (exit_price - entry) if dirn == "Long" else (entry - exit_price)
                base_df.loc[idx, "result"] = float(res)
                save_csv(base_df)
                st.success("Aktualisiert (Commit erstellt)")

elif page == "Stats & Export":
    st.header("Stats & Export")
    df = load_csv()
    if df.empty:
        st.info("Noch keine Trades.")
    else:
        # KPIs
        closed = df["result"].notna().sum()
        total = df["result"].dropna().sum() if closed else 0.0
        winrate = round((df["result"].dropna().gt(0).mean())*100,1) if closed else 0.0
        avg_rr = round(pd.to_numeric(df["rr"], errors="coerce").dropna().mean(), 2) if not df.empty else 0.0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Gesamter P/L", f"{total:.2f}")
        c2.metric("Geschlossene Trades", f"{closed}")
        c3.metric("Trefferquote", f"{winrate}%")
        c4.metric("Ø R:R", f"{avg_rr}")

        # Tages-P/L Chart
        df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        daily = df.dropna(subset=["result"]).groupby(df["date_dt"].dt.date)["result"].sum().reset_index()
        daily.columns = ["Datum","Tages-P/L"]
        st.write("**Tages-P/L**")
        st.bar_chart(daily.set_index("Datum"))

        st.download_button("CSV exportieren ⬇️", data=df.drop(columns=["date_dt"]).to_csv(index=False).encode("utf-8"), file_name="journal_export.csv", mime="text/csv")
