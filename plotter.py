import  matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from typing import Optional
import math
import seaborn as sns
import missingno as msno
from dataclasses import dataclass, field


"""
TODO:
Box plots (Done)
Tidy up some of the code to be more configureable (DID COLOR PALETTE YAY! -thanks claude)
Figure have the dataset name.?
Return the figure paths 
"""

#Custom color pallet thingy hold on..

@dataclass
class Palette:
    """
    Customize your chart colors here — just swap out hex codes.
    """
    primary: list[str] = field(default_factory=lambda: [
        "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2",
        "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
    ])
    background: str = "#FFFFFF"
    grid:       str = "#E5E5E5"
    text:       str = "#333333"
    edge:       str = "#1A1A1A"
    heatmap:    str = "coolwarm"

PASTEL_PALETTE = Palette(
    primary=[
        "#AEC6CF", "#FFD1DC", "#B5EAD7", "#FFDAC1", "#C7CEEA",
        "#E2F0CB", "#F0E6EF", "#FFF1BA", "#D4E8E1", "#FAD4C0",
    ],
    background="#FAFAFA",
    grid="#EDEDED",
    text="#555555",
    edge="#AAAAAA",
    heatmap="PiYG",
)

DARK_PALETTE = Palette(
    primary=[
        "#5B8FF9", "#E8684A", "#5AD8A6", "#F6BD16", "#E86452",
        "#6DC8EC", "#945FB9", "#FF9845", "#1E9493", "#FF99C3",
    ],
    background="#1E1E2E",
    grid="#2E2E3E",
    text="#CDD6F4",
    edge="#CDD6F4",
    heatmap="magma",
)


class Plot():
    """
    Argh Money blah blah
    """
    def __init__(self, data_c: pd.DataFrame, data_n: pd.DataFrame, cor_matrix: pd.DataFrame, palette: Palette):
        self.cat_data = data_c
        self.num_data = data_n
        self.palette: Palette = palette
        self.cor_matrix: pd.DataFrame = cor_matrix
        self.n_col: int = 5
        self.n_rows: int = 5
        self._apply_palette()

    def _apply_palette(self) -> None:
        """Push palette values into matplotlib's rcParams."""
        p = self.palette
        plt.rcParams.update({
            "axes.prop_cycle":    plt.cycler(color=p.primary),
            "figure.facecolor":   p.background,
            "axes.facecolor":     p.background,
            "axes.edgecolor":     p.edge,
            "axes.labelcolor":    p.text,
            "axes.grid":          False ,
            "grid.color":         p.grid,
            "xtick.color":        p.text,
            "ytick.color":        p.text,
            "text.color":         p.text,
        })

    def _base_fig(self, n_plots: int, n_col: int = 3):
        """Create a standard subplot grid and return (fig, flat-axes array)."""
        n_rows = math.ceil(n_plots / n_col)
        fig, ax = plt.subplots(
            nrows=n_rows, ncols=n_col,
            figsize=(12, 4 * n_rows),
            facecolor=self.palette.background,
        )
        axes = np.atleast_1d(ax).ravel()
        return fig, axes, n_rows
    
    def _hide_unused(self, axes, n_used: int) -> None:
        for ax in axes[n_used:]:
            ax.set_visible(False)
    
    def _style_ax(self, ax) -> None:
        """Apply palette-consistent styling to a single Axes."""
        ax.set_facecolor(self.palette.background)
        ax.tick_params(colors=self.palette.text)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.palette.edge)
    
    def _plot_missing(self, data: pd.DataFrame, title: str, path: str) -> str:
        total = len(data)
        missing = data.isnull().sum()
        present = total - missing
        cols = data.columns.tolist()
        x = np.arange(len(cols))

        fig, ax = plt.subplots(figsize=(max(8, len(cols) * 0.9), 5),
                               facecolor=self.palette.background)

        ax.bar(x, present, color=self.palette.primary[0],
               edgecolor=self.palette.edge, label="Present")
        ax.bar(x, missing, bottom=present, color=self.palette.primary[2],
               edgecolor=self.palette.edge, label="Missing", alpha=0.85)

        for idx, col in enumerate(cols):
            n_missing = missing[col]
            pct = n_missing / total * 100
            label = f"{total - n_missing}\n({100 - pct:.0f}%)"
            ax.text(idx, total + total * 0.01, label,
                    ha="center", va="bottom",
                    fontsize=8, color=self.palette.text)

        ax.set_xticks(x)
        ax.set_xticklabels(cols, rotation=35, ha="right",
                           fontsize=9, color=self.palette.text)
        ax.set_ylabel("Row count", color=self.palette.text)
        ax.set_ylim(0, total * 1.15)
        ax.set_title(title, fontsize=13, color=self.palette.text, pad=12)
        ax.legend(framealpha=0.3, labelcolor=self.palette.text,
                  facecolor=self.palette.background)
        self._style_ax(ax)

        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=self.palette.background)
        plt.close(fig)
        return path


    def histogram(self, path: str = "histogram.png") -> None:
        numeric_cols = list(self.num_data.columns)

        if not numeric_cols:
            raise ValueError("No numeric columns available to plot.")

        n_plots = len(numeric_cols)
        n_col = 3
        n_rows = math.ceil(n_plots / n_col)

        fig, ax = plt.subplots(nrows=n_rows, ncols=n_col, figsize=(12, 4 * n_rows))
        axes = np.atleast_1d(ax).ravel()

        for i, col in enumerate(numeric_cols):
            axes[i].hist(self.num_data[col].dropna(), edgecolor="black")
            axes[i].set_title(col)
            axes[i].set_xlabel(col)
            axes[i].set_ylabel("Frequency")

        for j in range(n_plots, len(axes)):
            axes[j].set_visible(False)

        fig.suptitle("Numerical Feature Distributions", fontsize=14)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def bar_graph(self, path: str = "barplots.png"):
        category_col = list(self.cat_data.columns)

        if not category_col:
            raise ValueError("No numeric columns available to plot.")

        n_plots = len(category_col)
        n_col = 3
        n_rows = math.ceil(n_plots / n_col)

        fig, ax = plt.subplots(nrows=n_rows, ncols=n_col, figsize=(12, 4 * n_rows))
        axes = np.atleast_1d(ax).ravel()

        for i, col in enumerate(category_col):
            counts = self.cat_data[col].dropna().value_counts().head(n=5)

            axes[i].bar(counts.index.astype(str), counts.values, edgecolor="black")
            axes[i].set_title(col)
            axes[i].set_xlabel(col)
            axes[i].set_ylabel("Count")
            axes[i].tick_params(axis="x", rotation=45)

        for j in range(n_plots, len(axes)):
            axes[j].set_visible(False)

        fig.suptitle("Categorical Feature Counts", fontsize=14)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def heatmap_correlation(self, path: str = "heatmap.png"):
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(self.cor_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def pair_plot(self):
        pass #may not need. Will think about it.

    def missing_values_vis(self, path_cat: str = "missing_cat.png", path_num: str = "missing_num.png") -> tuple[str, str]:
        self._plot_missing(self.cat_data, "Missing Values — Categorical", path_cat)
        self._plot_missing(self.num_data, "Missing Values — Numerical",   path_num)
        return path_cat, path_num

    def box_plot(self, path: str = "boxplots.png") -> str:
        numeric_cols = list(self.num_data.columns)
        if not numeric_cols:
            raise ValueError("No numeric columns available to plot.")

        fig, axes, _ = self._base_fig(len(numeric_cols))
        colors = self.palette.primary

        for i, col in enumerate(numeric_cols):
            color = colors[i % len(colors)]
            data = self.num_data[col].dropna()

            bp = axes[i].boxplot(
                data,
                patch_artist=True,     
                notch=False,
                vert=True,
                widths=0.5,
                boxprops=dict(facecolor=color, color=self.palette.edge),
                medianprops=dict(color=self.palette.edge, linewidth=2),
                whiskerprops=dict(color=self.palette.edge),
                capprops=dict(color=self.palette.edge),
                flierprops=dict(
                    marker="o",
                    markerfacecolor=color,
                    markeredgecolor=self.palette.edge,
                    markersize=4,
                    alpha=0.6,
                ),
            )

            axes[i].set_title(col)
            axes[i].set_ylabel(col)
            axes[i].set_xticks([])
        
        self._hide_unused(axes, len(numeric_cols))
        fig.suptitle("Numerical Feature Distributions (Box Plots)", fontsize=14, color=self.palette.text)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=self.palette.background)
        plt.close(fig)
        return path