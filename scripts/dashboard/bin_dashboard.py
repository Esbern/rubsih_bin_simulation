from __future__ import annotations

"""Streamlit dashboard for rubbish-bin container status.

This dashboard supports two data sources:

1) MQTT subscription (live)
2) JSONL log file produced by the simulator (playback/dry-run)

The intent is to make it easy to demo a "renovation company" monitoring view:
- Live graph of fill percentage per container over time
- Alert when any container reaches a threshold (default 80%)

Run:
- pip install -e ".[dashboard]"
- streamlit run scripts/dashboard/bin_dashboard.py
"""

from datetime import datetime, timedelta, timezone
import json
import queue
import threading
import time
import uuid
from typing import Any

import pandas as pd
import streamlit as st
import altair as alt

from simulated_city.config import load_config
from simulated_city.dashboard_data import event_from_payload, events_to_frame, read_jsonl_incremental
def _drain_queue(q: queue.Queue[dict[str, Any]], max_items: int = 5_000) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for _ in range(max_items):
        try:
            items.append(q.get_nowait())
        except queue.Empty:
            break
    return items
@st.cache_resource
def _start_mqtt_listener(topic_filter: str) -> queue.Queue[dict[str, Any]]:
    """Start a background MQTT subscriber that pushes payload dicts into a queue."""

    cfg = load_config()

    try:
        import paho.mqtt.client as mqtt
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError("paho-mqtt is required. Install the project dependencies.") from e

    q: queue.Queue[dict[str, Any]] = queue.Queue()

    if cfg.mqtt.username is None or cfg.mqtt.password is None:
        raise RuntimeError(
            "MQTT credentials are not set. Create a .env with HIVEMQ_USERNAME and HIVEMQ_PASSWORD (or export them) and restart Streamlit."
        )

    def on_message(_client, _userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8", errors="replace")
            payload = json.loads(payload_str)
            if isinstance(payload, dict):
                q.put(payload)
        except Exception:
            # Keep the dashboard robust for demos.
            return

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{cfg.mqtt.client_id_prefix}-dashboard-{uuid.uuid4().hex[:8]}",
    )
    if cfg.mqtt.username is not None:
        client.username_pw_set(cfg.mqtt.username, password=cfg.mqtt.password)

    if cfg.mqtt.tls:
        import ssl

        client.tls_set_context(ssl.create_default_context())

    client.on_message = on_message
    client.connect(cfg.mqtt.host, cfg.mqtt.port, keepalive=cfg.mqtt.keepalive_s)
    client.subscribe(topic_filter, qos=1)

    t = threading.Thread(target=client.loop_forever, name="mqtt-dashboard", daemon=True)
    t.start()

    return q
def main() -> None:
    st.set_page_config(page_title="Rubbish Bin Dashboard", layout="wide")

    st.title("Rubbish Bin Dashboard")
    st.caption("Live container fill graphs + 80% alert")

    cfg = load_config()
    base_topic = cfg.mqtt.base_topic

    with st.sidebar:
        st.header("Source")
        source = st.radio("Data source", options=["MQTT", "Log file"], index=0)
        refresh_s = st.slider("Refresh interval (seconds)", min_value=1, max_value=10, value=2)
        auto_refresh = st.checkbox("Auto refresh", value=True)
        alert_threshold = st.slider("Alert threshold (%)", min_value=1, max_value=100, value=80)
        history_days = st.selectbox("History window (days)", options=[1, 2, 7, 14], index=2)

        if source == "MQTT":
            st.caption("Subscribes to the retained status topics from the broker.")
        else:
            st.caption("Reads JSONL created via: python -m simulated_city --dry-run --log-file out.jsonl")
            log_path = st.text_input("Log file path", value="sim_status.jsonl")

    if "events_df" not in st.session_state:
        st.session_state["events_df"] = pd.DataFrame(
            {
                "ts": pd.Series(dtype="datetime64[ns, UTC]"),
                "series": pd.Series(dtype="string"),
                "fill_pct": pd.Series(dtype="int64"),
                "timestep_index": pd.Series(dtype="int64"),
                "event": pd.Series(dtype="string"),
            }
        )

    new_payloads: list[dict[str, Any]] = []
    if source == "MQTT":
        topic_filter = f"{base_topic}/bins/+/+/status"
        try:
            q = _start_mqtt_listener(topic_filter)
        except Exception as e:
            st.error(str(e))
            st.stop()
        new_payloads = _drain_queue(q)
    else:
        if "log_offset" not in st.session_state:
            st.session_state["log_offset"] = 0
        try:
            payloads, new_offset = read_jsonl_incremental(log_path, int(st.session_state["log_offset"]))
            st.session_state["log_offset"] = new_offset
            new_payloads = payloads
        except FileNotFoundError:
            st.warning(f"Log file not found: {log_path}")

    new_events = []
    for payload in new_payloads:
        try:
            new_events.append(event_from_payload(payload))
        except Exception:
            continue

    if new_events:
        new_df = events_to_frame(new_events)
        combined = pd.concat([st.session_state["events_df"], new_df], ignore_index=True)
        combined = combined.sort_values(["ts", "series"], kind="mergesort")
        combined = combined.drop_duplicates(subset=["ts", "series", "fill_pct", "event"], keep="last")
        st.session_state["events_df"] = combined.reset_index(drop=True)

    # Keep the last N days.
    # Important: simulation timestamps can advance much faster than wall-clock.
    # Anchor the window to the latest *data* timestamp so the chart shows the
    # last 24 hours of simulated time.
    wall_now = datetime.now(timezone.utc)
    df: pd.DataFrame = st.session_state["events_df"]
    if not df.empty:
        df = df.copy()
        df["ts"] = pd.to_datetime(df["ts"], utc=True)

        # If the log file was appended across multiple simulator runs, values
        # will "reset" back to 0% at each run start. Keep only the latest run.
        if "event" in df.columns:
            init_ts = df.loc[df["event"] == "init", "ts"]
        else:
            init_ts = pd.Series(dtype="datetime64[ns, UTC]")
        if not init_ts.empty:
            latest_start = init_ts.max()
            df = df[df["ts"] >= latest_start]

        # Fallback: if the log was appended across runs but lacks init markers
        # (older logs), detect resets by looking for any fill decrease.
        # Keep only the latest segment after the last decrease.
        diffs = df.sort_values(["series", "ts"]).groupby("series")["fill_pct"].diff()
        reset_rows = df.loc[diffs < 0, "ts"]
        if not reset_rows.empty:
            last_reset = reset_rows.max()
            df = df[df["ts"] >= last_reset]

        ts_max = df["ts"].max()
        anchor = ts_max.to_pydatetime() if isinstance(ts_max, pd.Timestamp) else wall_now
        cutoff = anchor - timedelta(days=int(history_days))

        # Include each series' last-known value before the cutoff so lines don't
        # jump at the left edge of the window.
        before = df[df["ts"] < pd.Timestamp(cutoff)]
        baseline = before.sort_values("ts").groupby("series").tail(1) if not before.empty else before
        after = df[df["ts"] >= pd.Timestamp(cutoff)]
        df = pd.concat([baseline, after], ignore_index=True)

        st.session_state["events_df"] = df

    if df.empty:
        st.info("No status events yet. Run the simulator to produce events.")
    else:
        # Latest per series for alerts.
        latest = df.sort_values("ts").groupby("series").tail(1)
        active_alerts = latest[latest["fill_pct"] >= int(alert_threshold)]

        if not active_alerts.empty:
            st.error(
                "ALERT: Containers at or above threshold: "
                + ", ".join(f"{row.series}={int(row.fill_pct)}%" for row in active_alerts.itertuples())
            )
        else:
            st.success("All containers are below the alert threshold.")

        # Plot
        # `pivot_table` introduces NaNs for series that didn't update at a given
        # timestamp (because other series did). Vega-Lite breaks lines on NaNs,
        # which makes points hoverable but lines appear missing.
        wide = df.pivot_table(index="ts", columns="series", values="fill_pct", aggfunc="last").sort_index()
        wide = wide.ffill().astype("float64")
        long = wide.reset_index().melt(id_vars="ts", var_name="series", value_name="fill_pct").dropna()

        chart = (
            alt.Chart(long)
            .mark_line(interpolate="step-after")
            .encode(
                x=alt.X("ts:T", title=None),
                y=alt.Y("fill_pct:Q", title="Fill %", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("series:N", title=None),
                tooltip=[
                    alt.Tooltip("ts:T", title="ts"),
                    alt.Tooltip("series:N", title="bin"),
                    alt.Tooltip("fill_pct:Q", title="fill_pct"),
                ],
            )
        )
        st.altair_chart(chart, width="stretch")

        with st.expander("Latest values"):
            st.dataframe(latest[["ts", "series", "fill_pct"]].sort_values("series"), width="stretch")

    if auto_refresh:
        time.sleep(float(refresh_s))
        # Streamlit renamed experimental_rerun -> rerun.
        rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun")
        rerun()


if __name__ == "__main__":
    main()
