"""
src/output/charts.py
Matplotlib/Seaborn QA distribution charts for the generated dataset.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from loguru import logger

# ─── Styling ─────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117",
    "axes.facecolor": "#1a1d27",
    "axes.edgecolor": "#2e3047",
    "axes.labelcolor": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "text.color": "#c9d1d9",
    "grid.color": "#2e3047",
    "grid.alpha": 0.5,
    "font.family": "DejaVu Sans",
})

PALETTE = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657"]
ARCHETYPE_COLORS = {
    "happy_customer":        "#3fb950",
    "neutral_passive":       "#58a6ff",
    "frustrated_detractor":  "#f78166",
    "delivery_focused":      "#ffa657",
    "value_seeker":          "#d2a8ff",
}


def generate_qa_charts(df: pd.DataFrame, output_path: str | Path) -> None:
    """Generate a comprehensive QA chart grid and save as PNG.

    Args:
        df: Responses DataFrame.
        output_path: Path to save the PNG file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(20, 14), facecolor="#0f1117")
    fig.suptitle(
        "Synthetic Survey Response — QA Distribution Report",
        fontsize=18, fontweight="bold", color="#c9d1d9", y=0.98,
    )

    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.35)

    # ── 1. Q1 Satisfaction Bar Chart ─────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    sat_counts = df["q1_satisfaction"].value_counts().sort_index()
    bars = ax1.bar(sat_counts.index, sat_counts.values, color=PALETTE, edgecolor="#2e3047")
    ax1.set_title("Q1 — Satisfaction (1–5)", fontsize=11, pad=8)
    ax1.set_xlabel("Rating")
    ax1.set_ylabel("Count")
    for bar, val in zip(bars, sat_counts.values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 str(val), ha="center", va="bottom", fontsize=9, color="#c9d1d9")
    ax1.grid(axis="y", alpha=0.3)

    # ── 2. Q2 NPS Histogram (Detractor / Passive / Promoter) ─────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    nps_colors = []
    for v in range(11):
        if v <= 6:
            nps_colors.append("#f78166")
        elif v <= 8:
            nps_colors.append("#ffa657")
        else:
            nps_colors.append("#3fb950")

    nps_counts = df["q2_nps"].value_counts().sort_index()
    ax2.bar(
        nps_counts.index, nps_counts.values,
        color=[nps_colors[i] for i in nps_counts.index],
        edgecolor="#2e3047",
    )
    ax2.set_title("Q2 — NPS Score (0–10)", fontsize=11, pad=8)
    ax2.set_xlabel("NPS Score")
    ax2.set_ylabel("Count")
    ax2.set_xticks(range(11))
    # Legend
    from matplotlib.patches import Patch
    ax2.legend(handles=[
        Patch(color="#f78166", label=f"Detractors (0–6): {int((df.q2_nps <= 6).sum())}"),
        Patch(color="#ffa657", label=f"Passives (7–8): {int(((df.q2_nps >= 7) & (df.q2_nps <= 8)).sum())}"),
        Patch(color="#3fb950", label=f"Promoters (9–10): {int((df.q2_nps >= 9).sum())}"),
    ], fontsize=7, loc="upper left")
    ax2.grid(axis="y", alpha=0.3)

    # ── 3. Q3 Category Donut ─────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    cat_counts = df["q3_category"].value_counts()
    wedges, texts, autotexts = ax3.pie(
        cat_counts.values,
        labels=cat_counts.index,
        autopct="%1.1f%%",
        colors=PALETTE,
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"edgecolor": "#0f1117", "linewidth": 2},
    )
    for t in texts + autotexts:
        t.set_color("#c9d1d9")
        t.set_fontsize(8)
    centre_circle = plt.Circle((0, 0), 0.55, fc="#1a1d27")
    ax3.add_patch(centre_circle)
    ax3.set_title("Q3 — Category Distribution", fontsize=11, pad=8)

    # ── 4. Q4 Delivery Donut ─────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    del_counts = df["q4_delivery_on_time"].value_counts()
    del_labels = ["On Time" if v else "Late" for v in del_counts.index]
    ax4.pie(
        del_counts.values,
        labels=del_labels,
        autopct="%1.1f%%",
        colors=["#3fb950", "#f78166"],
        startangle=90,
        wedgeprops={"edgecolor": "#0f1117", "linewidth": 2},
    )
    ax4.set_title("Q4 — Delivery Status", fontsize=11, pad=8)
    for text in ax4.texts:
        text.set_color("#c9d1d9")
        text.set_fontsize(9)

    # ── 5. Coherence Score Histogram ─────────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.hist(df["coherence_score"], bins=10, range=(0, 1), color="#58a6ff",
             edgecolor="#0f1117", alpha=0.85)
    ax5.axvline(0.6, color="#f78166", linestyle="--", linewidth=1.5, label="Threshold (0.6)")
    ax5.set_title("Coherence Score Distribution", fontsize=11, pad=8)
    ax5.set_xlabel("Coherence Score")
    ax5.set_ylabel("Count")
    ax5.legend(fontsize=8)
    ax5.grid(axis="y", alpha=0.3)
    mean_coh = df["coherence_score"].mean()
    ax5.text(0.05, 0.88, f"Mean: {mean_coh:.3f}", transform=ax5.transAxes,
             fontsize=9, color="#ffa657")

    # ── 6. Q1 vs Q2 Scatter (Correlation) ────────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    scatter_colors = [ARCHETYPE_COLORS.get(a, "#58a6ff") for a in df["persona_archetype"]]
    ax6.scatter(df["q1_satisfaction"], df["q2_nps"], c=scatter_colors, alpha=0.5, s=20)
    # Regression line
    m, b = np.polyfit(df["q1_satisfaction"], df["q2_nps"], 1)
    x_line = np.linspace(1, 5, 100)
    ax6.plot(x_line, m * x_line + b, color="#ffa657", linewidth=1.5, label="Trend")
    r = df[["q1_satisfaction", "q2_nps"]].corr().iloc[0, 1]
    ax6.set_title(f"Q1 vs Q2 Correlation (r={r:.2f})", fontsize=11, pad=8)
    ax6.set_xlabel("Satisfaction (Q1)")
    ax6.set_ylabel("NPS Score (Q2)")
    ax6.legend(fontsize=8)
    ax6.grid(alpha=0.2)

    # ── 7. Archetype Distribution ─────────────────────────────────────────────
    ax7 = fig.add_subplot(gs[2, 0])
    arch_counts = df["persona_archetype"].value_counts()
    arch_colors = [ARCHETYPE_COLORS.get(a, "#58a6ff") for a in arch_counts.index]
    bars7 = ax7.barh(arch_counts.index, arch_counts.values, color=arch_colors, edgecolor="#2e3047")
    ax7.set_title("Persona Archetype Distribution", fontsize=11, pad=8)
    ax7.set_xlabel("Count")
    for bar, val in zip(bars7, arch_counts.values):
        ax7.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 str(val), va="center", fontsize=8, color="#c9d1d9")
    ax7.grid(axis="x", alpha=0.3)

    # ── 8. Sentiment Compound Distribution ───────────────────────────────────
    ax8 = fig.add_subplot(gs[2, 1])
    ax8.hist(df["sentiment_compound"], bins=20, range=(-1, 1),
             color="#d2a8ff", edgecolor="#0f1117", alpha=0.85)
    ax8.axvline(0, color="#ffa657", linestyle="--", linewidth=1, label="Neutral")
    ax8.set_title("Q5 Sentiment Distribution (VADER)", fontsize=11, pad=8)
    ax8.set_xlabel("Compound Score")
    ax8.set_ylabel("Count")
    ax8.legend(fontsize=8)
    ax8.grid(axis="y", alpha=0.3)

    # ── 9. Delivery Impact on Satisfaction ───────────────────────────────────
    ax9 = fig.add_subplot(gs[2, 2])
    on_time_mean = df[df["q4_delivery_on_time"] == True]["q1_satisfaction"].mean()
    late_mean    = df[df["q4_delivery_on_time"] == False]["q1_satisfaction"].mean()
    bars9 = ax9.bar(
        ["On Time", "Late"],
        [on_time_mean, late_mean],
        color=["#3fb950", "#f78166"],
        width=0.5,
        edgecolor="#2e3047",
    )
    ax9.set_title("Delivery Impact on Satisfaction", fontsize=11, pad=8)
    ax9.set_ylabel("Mean Satisfaction (Q1)")
    ax9.set_ylim(0, 5.5)
    for bar, val in zip(bars9, [on_time_mean, late_mean]):
        ax9.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{val:.2f}", ha="center", va="bottom", fontsize=10, color="#c9d1d9")
    ax9.grid(axis="y", alpha=0.3)
    diff = on_time_mean - late_mean
    ax9.text(0.5, 0.85, f"Δ = {diff:+.2f}", transform=ax9.transAxes,
             ha="center", fontsize=11, color="#ffa657", fontweight="bold")

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#0f1117")
    plt.close()
    logger.success(f"QA chart saved: {output_path}")
