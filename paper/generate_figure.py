#!/usr/bin/env python3
"""Generate the architecture figure for the JOSS paper."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis("off")

box_kw = dict(boxstyle="round,pad=0.4", facecolor="#dbeafe", edgecolor="#2563eb", linewidth=1.5)
box_green = dict(boxstyle="round,pad=0.4", facecolor="#dcfce7", edgecolor="#16a34a", linewidth=1.5)
box_orange = dict(boxstyle="round,pad=0.4", facecolor="#fff7ed", edgecolor="#ea580c", linewidth=1.5)
box_purple = dict(boxstyle="round,pad=0.4", facecolor="#f3e8ff", edgecolor="#9333ea", linewidth=1.5)

# Title
ax.text(5, 6.6, "CompLaB3D Architecture", fontsize=16, fontweight="bold",
        ha="center", va="center")

# GUI layer
ax.text(5, 5.8, "CompLaB Studio GUI (Python / PySide6)",
        fontsize=12, ha="center", va="center", bbox=box_purple)

# GUI sub-components
gui_items = ["Template\nSelector", "XML\nGenerator", "Kinetics\nCode-Gen",
             "3D Geometry\nViewer (VTK)", "Solver\nManager"]
for i, item in enumerate(gui_items):
    x = 1.0 + i * 2.0
    ax.text(x, 4.7, item, fontsize=8, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ede9fe",
                      edgecolor="#9333ea", linewidth=1))

# Arrow GUI -> Solver
ax.annotate("", xy=(5, 3.9), xytext=(5, 4.3),
            arrowprops=dict(arrowstyle="-|>", color="#555", lw=2))
ax.text(5.7, 4.1, "XML + .hh", fontsize=8, color="#555", ha="left")

# C++ Solver layer
ax.text(5, 3.5, "C++ Solver (Palabos LBM / MPI-parallel)",
        fontsize=12, ha="center", va="center", bbox=box_kw)

# Operator splitting stages
stages = [
    ("Transport\n(LBM ADE)", "#dbeafe", "#2563eb"),
    ("Kinetics\n(Monod / decay)", "#dcfce7", "#16a34a"),
    ("Equilibrium\n(Newton-Raphson\n+ Anderson)", "#fff7ed", "#ea580c"),
    ("Biofilm CA\n(growth /\ndetachment)", "#fef9c3", "#ca8a04"),
]
for i, (label, fc, ec) in enumerate(stages):
    x = 1.25 + i * 2.25
    ax.text(x, 2.2, label, fontsize=8, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=fc,
                      edgecolor=ec, linewidth=1.2))

# Arrows between stages
for i in range(3):
    x_from = 1.25 + i * 2.25 + 0.7
    x_to = 1.25 + (i + 1) * 2.25 - 0.7
    ax.annotate("", xy=(x_to, 2.2), xytext=(x_from, 2.2),
                arrowprops=dict(arrowstyle="-|>", color="#888", lw=1.5))

# Arrow Solver -> Output
ax.annotate("", xy=(5, 1.2), xytext=(5, 1.7),
            arrowprops=dict(arrowstyle="-|>", color="#555", lw=2))

# Output
ax.text(5, 0.8, "VTI Output (ParaView)",
        fontsize=10, ha="center", va="center", bbox=box_green)

# Operator splitting label
ax.text(5, 2.9, "Operator Splitting (per timestep)",
        fontsize=9, fontstyle="italic", ha="center", va="center", color="#555")

plt.tight_layout()
fig.savefig("paper/architecture.png", dpi=300, bbox_inches="tight")
fig.savefig("paper/architecture.pdf", dpi=300, bbox_inches="tight")
print("Saved paper/architecture.png and paper/architecture.pdf")
