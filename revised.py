from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
import pprint
import re
from pathlib import Path

"""
TODO fix:
--Fix some of the builit in method stuff (Done)
--Fix some stuff in _convert date (Maybe)
--Make sure the path is valid in __init__ oops (done)
--parser percent return None but num_report doesn't handle if apparently (Not done but will be one the list for a while)
"""

"""
TODO add:
Outlier detection: Most likely will do IQR, maybe will implement isolation forest, or different method (IQR Method done)
More visual missing values
Duplicate row detection
Maybe automatically transform if a column is extremely skewed
Cluster Analysis -- just to see if there are any natural groupding with out any advanced data maniplutation
Since some dataset will have extremely high dimensionally PCA or something will be good to have.
"""


DATE_KEYWORDS = {"date", "dt", "time", "day", "month", "year", "created", "updated"}
BOOL_TRUE  = {"true", "yes", "y", "1", "on"}
BOOL_FALSE = {"false", "no", "n", "0", "off"}
class NewReader():

    def __init__(self, path : Path):
        self.path: Path  = path
        self.data: pd.DataFrame = pd.DataFrame()
        self.corr_matrix : Optional[pd.DataFrame] = None
        self.skew: Optional[pd.Series[Any]] = None
        self.kurt: Optional[pd.Series[Any]] = None
        self.load_csv()

    def load_csv(self):
        if not Path(self.path).exists():
            raise FileNotFoundError(f"No file found at: {self.path}")
        self.data = pd.read_csv(self.path)

    def column_types(self):
        print(self.data.dtypes)

    def standardize_data(self):
        """
        This will be tricky because I don't want to input all the column by hand
        so how can I solve this issuse. Well I can just loop through the columns
        then do some regex from the internet to decide on some of date/money/percent stuff.
        Then also convert those to their approiate data types. I believe I will start with that first.
        """
        self._convert_date()
        self._percents()
        self._convert_dollars()
        #self._regularize_strings() this broke on the first real dataset I used it on.
        self._convert_bool()

    def get_col_types(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        cat_col = self.data.select_dtypes(include=["object", "category"])
        numerical_cols = self.data.select_dtypes(include=[np.number])
        return cat_col, numerical_cols

    def desc_stats(self):
        cat_col, numerical_cols = self.get_col_types()

        report_null = null_report(self.data)
        report_cat = categorical_report(cat_col)
        report_num = numerical_report(numerical_cols)
        report_outliers = outlier_report(numerical_cols)

        self.corr_matrix = correlation(self.data)
        self.skew, self.kurt = skewness_kurtosis(self.data)

        print("\n=== CATEGORICAL REPORT ===")
        self.print_reports(report_cat)

        print("\n=== NUMERICAL REPORT ===")
        self.print_reports(report_num)

        print("\n=== NULL REPORT ===")
        self.print_nulls(report_null)

        print("\n=== CORRELATION MATRIX ===")
        print(self.corr_matrix)

        print("\n=== SKEWNESS ===")
        print(self.skew)

        print("\n=== KURTOSIS ===")
        print(self.kurt)

        print("\n=== OUTLIERS ===")
        #self.print_reports(outlier_report)

        self.write_simple_report(report_cat, report_num, report_null, report_outliers)

    def print_csv(self):
        pprint.pprint(self.data)

    def _convert_date(self):
        pattern = r"^(?:(?:(0[13578]|1[02])([-./])(0[1-9]|[12][0-9]|3[01])\2)|(?:(0[469]|11)([-./])(0[1-9]|[12][0-9]|30)\5)|(?:(02)([-./])(0[1-9]|1[0-9]|2[0-8])\8))\d{4}$" #This is not good but we have ai now days so it's fine
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            if sample.empty:
                continue

            name_match = any(kw in col.lower() for kw in DATE_KEYWORDS)
            pattern_match = sample.str.match(pattern).mean() > 0.8

            if name_match or pattern_match:
                parsed = pd.to_datetime(self.data[col], errors="coerce", format="mixed")
                if parsed.notna().mean() > 0.8:
                    self.data[col] = parsed

    def _percents(self):
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            if sample.str.contains("%").any():
                self.data[col] = self.data[col].apply(parse_percent)

    def _convert_dollars(self):
        pattern = r"^\$[\d,]+(\.\d+)?$"
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            if sample.str.contains(pattern, regex=True).any():
                self.data[col] = self.data[col].apply(parse_dollars)
    
    def _regularize_strings(self):
        for col in self.data.select_dtypes(include="object").columns:
            self.data[col] = self.data[col].str.upper()

    def _convert_bool(self):
        for col in self.data.columns:
            normalized = self.data[col].astype(str).str.strip().str.lower()
            non_null_values = set(normalized[self.data[col].notna()].unique())

            if non_null_values and non_null_values.issubset(BOOL_TRUE | BOOL_FALSE):
                self.data[col] = normalized.map(
                    lambda x: True if x in BOOL_TRUE else False if x in BOOL_FALSE else np.nan
                )
    
    def print_nulls(self, report) -> None:
        for _, thing in report.items():
            print(f"Null Values in Columns")
            print(f"{thing}")

    def print_reports(self, report) -> None:
        for col, stats in report.items():
            print(f"\nColumn: {col}")
            for key, value in stats.items():
                print(f"{key}:")
                print(value)

    def write_simple_report(self,report_cat: Dict[str, Dict[str, Any]],report_num: Dict[str, Dict[str, Any]],report_null: Dict[str, Dict[str, Any]],report_outliers: Dict[str, Dict[str, Any]],filename: str = "report.txt") -> None:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== CATEGORICAL STATISTICS ===\n")
                for col, stats in report_cat.items():
                    f.write(f"\nColumn: {col}\n")
                    for key, value in stats.items():
                        f.write(f"{key}:\n")
                        if isinstance(value, pd.Series):
                            f.write(value.head(5).to_string())
                        else:
                            f.write(str(value))
                        f.write("\n")

                f.write("\n=== NUMERICAL STATISTICS ===\n")
                for col, stats in report_num.items():
                    f.write(f"\nColumn: {col}\n")
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")

                f.write("\n=== NULL REPORT ===\n")
                for col, stats in report_null.items():
                    f.write(f"{col}: {stats['null_count']} null(s)\n")

                f.write("\n=== OUTLIERS ===\n")
                for col, stats in report_outliers.items():
                    f.write(f"\nColumn: {col}\n")
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")


def null_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        report[col] = {
            "null_count": int(df[col].isna().sum())
        }
    return report


def numerical_report(df : pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}

    for col in df.columns:
        mean_col = df[col].mean()
        median_col = df[col].median()
        std_col = df[col].std()
        min_col = df[col].min()
        max_col = df[col].max()
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        report[col] = {
            "mean" : mean_col ,
            "median": median_col,
            "std": std_col,
            "min": min_col,
            "max": max_col,
            "IQR": IQR
        }
    return report

def categorical_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        counts = df[col].value_counts(dropna=True)
        max_value = counts.max()
        min_value = counts.min()
        length = len(df[col])

        report[col] = {
            "counts": counts,
            "max": max_value,
            "min": min_value,
            "length": length
        }
    return report

def parse_percent(val: str) -> float | None:
    val = str(val).strip()
    if "%" in val:
        return float(val.replace("%", "")) / 100
    try:
        return float(val) 
    except ValueError:
        return None #This would be a problem if a dataset has percents like this
        #But for now we don't have to handel it because I need a dataset to break this first. to fix it.

def parse_dollars(val: str) -> float | None:
    val = str(val).strip().replace("$", "").replace(",", "")
    try:
        return float(val)
    except ValueError:
        return None
    
def correlation(df: pd.DataFrame) -> pd.DataFrame:
    numerical_cols = df.select_dtypes([np.number])
    return numerical_cols.corr()

def skewness_kurtosis(df: pd.DataFrame) -> tuple[pd.Series[Any], pd.Series[Any]]:
    numerical_cols = df.select_dtypes([np.number])

    skewness = numerical_cols.skew()
    kur = numerical_cols.kurtosis()

    return skewness, kur

def check_uniqueness(df: pd.DataFrame, threshold: float = 1):
    """
    If there is a lot of unqiueness like if every value is unique then that column is most
    likely garbage and we need to remove it from any analysis. Or maybe not useless but I 
    only am going to be using this to graph.
    """
    cols_to_drop = []

    for col in df.columns:
        non_null_count = df[col].notna().sum()
        if non_null_count == 0:
            continue

        unique_count = df[col].nunique(dropna=True)
        unique_ratio = unique_count / non_null_count
        print(unique_ratio)
        if unique_ratio >= threshold:
            cols_to_drop.append(col)

    return df.drop(columns=cols_to_drop)

def outlier_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}

    for col in df.columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        Bounded_IQR = IQR * 2.25 #3 is used for extreme outliers and 1.5 is used to find outliers in general but 2.25 is find for now.
        lower = Q1 - Bounded_IQR
        upper = Q3 + Bounded_IQR

        outliers = df[(df[col] < lower) | (df[col] > upper)][col]

        report[col] = {
            "outlier_count": len(outliers),
            "lower_fence": lower,
            "upper_fence": upper,
            "outlier_pct": round(len(outliers) / df[col].notna().sum() * 100, 2)
        }

    return report