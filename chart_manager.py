"""Vai trò 4 - Data Visualization: biểu đồ 2D / 3D bằng Matplotlib."""
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (kích hoạt projection='3d')

INCOME_COLOR, EXPENSE_COLOR = "#2e9e5b", "#d64545"


def build_bar_figure(top_df) -> Figure:
    """Bar chart 2D: Income đi lên (>0), Expense đi xuống (<0)."""
    fig = Figure(figsize=(7, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    if top_df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig
    colors = [INCOME_COLOR if v > 0 else EXPENSE_COLOR for v in top_df["amount"]]
    ax.bar(top_df["category"], top_df["amount"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Top Categories (Income ↑ / Expense ↓)")
    ax.set_ylabel("Amount")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def build_3d_figure(df) -> Figure:
    """Scatter 3D: Month x Category x Amount."""
    fig = Figure(figsize=(7.5, 5.5), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    if df.empty:
        ax.set_title("No data")
        return fig
    d = df.copy()
    d["month"] = d["date"].dt.strftime("%Y-%m")
    agg = d.groupby(["month", "category"], as_index=False)["amount"].sum()
    months = sorted(agg["month"].unique())
    cats = sorted(agg["category"].unique())
    x = agg["month"].map({m: i for i, m in enumerate(months)})
    y = agg["category"].map({c: i for i, c in enumerate(cats)})
    z = agg["amount"]
    colors = np.where(z > 0, INCOME_COLOR, EXPENSE_COLOR)
    ax.scatter(x, y, z, c=colors, s=60, depthshade=True)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=30, fontsize=7)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cats, fontsize=7)
    ax.set_xlabel("Month"); ax.set_ylabel("Category"); ax.set_zlabel("Amount")
    ax.set_title("3D Spending Trend")
    return fig


def embed(fig: Figure, parent):
    """Nhúng Figure vào cửa sổ Tkinter (không mở cửa sổ ngoài)."""
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    NavigationToolbar2Tk(canvas, parent).update()   # cho phép xoay 3D bằng chuột
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return canvas