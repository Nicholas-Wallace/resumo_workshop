import os
import time
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import colormaps
from plotly.io import write_json
from plotly.io import read_json
from pathlib import Path

from segy_handler import SegyHandler
from file_handler import FileHandler


def read_and_plot():
    start_time = time.perf_counter()

    file_handler = FileHandler()
    segy_handler = SegyHandler(
        data_directory="./data", 
        available_segy_files=["jequitinhonha"] 
    )

    results = segy_handler.process_segy_file("jequitinhonha")
    
    file_info = results["jequitinhonha"]
    
    df = segy_handler.read_segy("jequitinhonha")
    
    #df_filtered = df[(df['CDP'] >= 1700) & df['CDP'] <= 1800]

    print(df.columns)

    #df_data = segy_handler.add_amplitudes_to_dataframe(df_filtered, "jequitinhonha")

    title = "Seismic Section"
    x_title = "Trace Number"
    y_title = "Time (s)"
    color_title = "Amplitude"
    colormap = "seismic"
    show_seismic = False

    trace_sample_count = df["TRACE_SAMPLE_COUNT"].iloc[0]
    trace_sample_interval = df["TRACE_SAMPLE_INTERVAL"].iloc[0]

    # Compute amplitude matrix and time-related parameters
    amplitudes = np.vstack(df["Amplitudes"].values)
    dt_ms = trace_sample_interval / 1000  # Convert interval to milliseconds
    duration_sec = (trace_sample_count * dt_ms) / \
        1000  # Total duration in seconds

    # Generate trace_number array starting from trace_start, incremented by trace_increment, with length equal to number of rows in df
    if "TRACE_SEQUENCE_FILE" in df.columns:
        trace_start = df["TRACE_SEQUENCE_FILE"].iloc[0]
    elif "TRACE_SEQUENCE_LINE" in df.columns:
        trace_start = df["TRACE_SEQUENCE_LINE"].iloc[0]
    else:
        trace_start = 1

    trace_increment = 1
    trace_number = np.arange(trace_start, trace_start + trace_increment * len(df), trace_increment)

    # Time samples in seconds
    time_samples = np.linspace(0, duration_sec, trace_sample_count)

    x_min, x_max = trace_number[0], trace_number[-1]

    norm_amplitudes = amplitudes / np.max(np.abs(amplitudes))

    cmap = plt.get_cmap(colormap)
    colorscale = [
        [i / 255, f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"]
        for i in range(256)
        for r, g, b, _ in [cmap(i / 255)]
    ]


    fig = go.Figure(data=go.Heatmap(
        z=norm_amplitudes.T,
        x=trace_number,
        y=time_samples,
        colorscale=colorscale,
        zsmooth='best', # Applies bilinear interpolation for smoother visualization (equivalent to Seismic Unix Ximage)
        zmid=0,
        colorbar=dict(
            title=color_title,
            tickfont=dict(size=14),
            thickness=30,
            len=1,
        )
    ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24)
        ),
        xaxis_title=x_title,
        yaxis_title=y_title,
        yaxis=dict(
            autorange="reversed",
            showgrid=False,
            title=dict(
                font=dict(size=18)
            ),
            tickfont=dict(size=18)
        ),
        xaxis=dict(
            range=[x_min, x_max],
            showgrid=False,
            title=dict(
                font=dict(size=18)
            ),
            tickfont=dict(size=18)
        ),
        width=700,
        height=500,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    save_path = os.path.join(
    "./data", f"{time.time()}_seismic_section.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    write_json(fig, save_path)

    try:
      if isinstance(save_path, str) and os.path.exists(save_path):
        loaded_fig = read_json(save_path)
        chart_key = Path(save_path).stem
        st.plotly_chart(loaded_fig, width="stretch", key=chart_key)
      else:
        raise FileNotFoundError(f"Visualization file not found")
    except Exception as e:
      st.error(f"Error loading graphic '{save_path}': {str(e)}")

    end_time = time.perf_counter()
    st.session_state.last_run = end_time - start_time

try:
    if 'last_run' not in st.session_state:
        st.session_state.last_run = 0

    st.button("Run Performance Test", on_click=read_and_plot)

    if st.session_state.last_run > 0:
        st.success(f"Task took {st.session_state.last_run:.4f} seconds")
except Exception as e:
    print(f"Test failed: {e}")

