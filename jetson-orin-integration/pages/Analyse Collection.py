#!/usr/bin/env python3
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA
import streamlit as st

st.set_page_config(page_title="Analyse Thermal Collection", page_icon="📊", layout="wide")

IMG_SHAPE = (120, 160)

@st.cache_data(show_spinner=False)
def list_collections() -> List[Path]:
    d = Path.home() / "Desktop"
    if not d.exists():
        return []
    cols = sorted(d.glob("thermal_collection_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p for p in cols if p.is_dir()]

@st.cache_data(show_spinner=False)
def load_collection(dirpath: str) -> Tuple[np.ndarray, list]:
    """Load all .npy images into array of shape (n, 120, 160). Returns (stack, filenames)."""
    p = Path(dirpath)
    files = sorted(p.glob("*.npy"))
    imgs = []
    names = []
    for f in files:
        try:
            arr = np.load(f)
            if arr.shape != IMG_SHAPE:
                # attempt reshape if flat
                if arr.ndim == 1 and arr.size == IMG_SHAPE[0] * IMG_SHAPE[1]:
                    arr = arr.reshape(IMG_SHAPE)
                else:
                    continue
            imgs.append(arr.astype(float))
            names.append(f.name)
        except Exception:
            continue
    if not imgs:
        return np.empty((0,) + IMG_SHAPE), []
    stack = np.stack(imgs, axis=0)
    return stack, names


def compute_stats(stack: np.ndarray) -> dict:
    # Mask negatives as NaN (faulty pixels)
    data = np.where(stack <= 0, np.nan, stack)
    # Overall stats across all pixels & frames
    overall = {
        "count_frames": int(stack.shape[0]),
        "min": float(np.nanmin(data)) if data.size else np.nan,
        "max": float(np.nanmax(data)) if data.size else np.nan,
        "mean": float(np.nanmean(data)) if data.size else np.nan,
        "median": float(np.nanmedian(data)) if data.size else np.nan,
    }
    # Mode: approximate via histogram of all values
    flat = data.reshape(-1)
    flat = flat[~np.isnan(flat)]
    if flat.size:
        hist, bins = np.histogram(flat, bins=100)
        idx = int(np.argmax(hist))
        mode = float((bins[idx] + bins[idx+1]) / 2)
    else:
        mode = np.nan
    overall["mode"] = mode

    # Per-pixel mean for heatmap
    mean_img = np.nanmean(data, axis=0)

    return {"overall": overall, "mean_img": mean_img}


def run_pca(stack: np.ndarray, n_components: int = 3):
    if stack.shape[0] < 2:
        return None
    data = np.where(stack <= 0, np.nan, stack)
    # Fill NaNs with per-pixel mean to keep structure
    per_pixel_mean = np.nanmean(data, axis=0)
    filled = np.where(np.isnan(data), per_pixel_mean, data)
    X = filled.reshape(filled.shape[0], -1)
    pca = PCA(n_components=min(n_components, X.shape[0], X.shape[1]))
    comps = pca.fit_transform(X)  # scores shape (n_samples, k)
    components = pca.components_.reshape(-1, *IMG_SHAPE)  # shape (k, 120, 160)
    return {
        "pca": pca,
        "scores": comps,
        "components": components,
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
    }


def main():
    st.title("📊 Analyse Thermal Collection")
    cols = list_collections()
    if not cols:
        st.warning("No thermal_collection_* directories found under ~/Desktop")
        st.stop()

    options = [c.name for c in cols]
    choice = st.selectbox("Select a collection", options)
    selected_dir = cols[options.index(choice)]

    with st.spinner("Loading collection..."):
        stack, names = load_collection(str(selected_dir))

    st.write(f"Loaded {stack.shape[0]} images from {selected_dir}")

    if stack.shape[0] == 0:
        st.error("No valid .npy images found in this directory.")
        st.stop()

    # Summary stats
    stats = compute_stats(stack)
    overall = stats["overall"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Frames", overall["count_frames"]) 
    c2.metric("Mean (°C)", f"{overall['mean']:.2f}")
    c3.metric("Median (°C)", f"{overall['median']:.2f}")
    c4.metric("Mode (°C)", f"{overall['mode']:.2f}" if not np.isnan(overall['mode']) else "NaN")

    # Heatmap of mean image
    st.subheader("Mean Temperature Heatmap")
    mean_img = stats["mean_img"]
    fig_hm = px.imshow(mean_img, color_continuous_scale="Turbo", origin="upper",
                       labels=dict(color="°C"))
    fig_hm.update_layout(height=500)
    st.plotly_chart(fig_hm, use_container_width=True)

    # Overall histogram
    st.subheader("Overall Temperature Distribution")
    flat = stack.reshape(-1)
    flat = flat[flat > 0]
    hist_fig = px.histogram(flat, nbins=100, labels={'value': '°C'})
    st.plotly_chart(hist_fig, use_container_width=True)

    # PCA
    st.subheader("Principal Component Analysis (PCA)")
    res = run_pca(stack, n_components=3)
    if res is None:
        st.info("Need at least 2 frames for PCA.")
    else:
        pca = res["pca"]
        scores = res["scores"]
        components = res["components"]
        evr = res["explained_variance_ratio"]

        # Explained variance
        ev_fig = go.Figure(data=[go.Bar(x=[f"PC{i+1}" for i in range(len(evr))], y=evr)])
        ev_fig.update_layout(title="Explained Variance Ratio", yaxis_title="Ratio")
        st.plotly_chart(ev_fig, use_container_width=True)

        # Component images
        comp_cols = st.columns(len(components))
        for i, comp in enumerate(components):
            fig_c = px.imshow(comp, color_continuous_scale="RdBu", origin="upper",
                              title=f"Component {i+1}")
            comp_cols[i].plotly_chart(fig_c, use_container_width=True)

        # Scores scatter (PC1 vs PC2)
        if scores.shape[1] >= 2:
            df_scores = pd.DataFrame(scores[:, :2], columns=["PC1", "PC2"])
            df_scores["frame"] = list(range(1, scores.shape[0] + 1))
            sc_fig = px.scatter(df_scores, x="PC1", y="PC2", text="frame",
                                title="Scores: PC1 vs PC2")
            sc_fig.update_traces(textposition='top center')
            st.plotly_chart(sc_fig, use_container_width=True)

    # File listing
    with st.expander("Files"):
        st.write(selected_dir)
        st.write(names)

if __name__ == "__main__":
    main()
