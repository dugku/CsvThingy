import  matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from typing import Optional
import math
import seaborn as sns

class Plot():
    """
    Argh Money blah blah
    """
    def __init__(self, data_c: pd.DataFrame, data_n: pd.DataFrame, cor_matrix: pd.DataFrame):
        self.cat_data = data_c
        self.num_data = data_n
        self.cor_matrix: pd.DataFrame = cor_matrix
        self.n_col: int = 3
        self.n_rows: int = 3

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

    def heatmap_correlation(self, path:str = "heatmap.png"):
        sns.heatmap(self.cor_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.savefig(path, dpi=300, bbox_inches='tight')

    def pair_plot(self):
        pass