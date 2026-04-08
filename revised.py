import numpy
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
import pprint
import re

DATE_KEYWORDS = {"date", "dt", "time", "day", "month", "year", "created", "updated"}
BOOL_TRUE  = {"true", "yes", "y", "1", "on"}
BOOL_FALSE = {"false", "no", "n", "0", "off"}
class NewReader():

    def __init__(self, path : str):
        self.path: str  = path
        self.data: pd.DataFrame = pd.DataFrame()
        self.load_csv()

    def load_csv(self):
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
        self._regularize_strings()
        self._convert_bool()


    def desc_stats(self):
        cat_col = self.data.select_dtypes(include=["object", "category"])
        numerical_cols = self.data.select_dtypes(include=[np.number])
        report_null = null_report(self.data)
        report_cat = categorical_report(cat_col)
        report_num = numerical_report(numerical_cols)
        cor_matrix = correlation(self.data)
        skew, kurt = skewness_kurtosis(self.data)

        self.print_reports(report_cat)
        self.print_reports(report_num)
        self.print_nulls(report_null)

        #self.write_simple_report(report_cat, report_num, report_null) will figure this out later bleh.


    def print_csv(self):
        pprint.pprint(self.data)

    def _convert_date(self):
        pattern = r"^(0?[1-9]|1[0-2])[./-](0?[1-9]|[12]\d|3[01])[./-]\d{4}$"
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            name_match = any(kw in col.lower() for kw in DATE_KEYWORDS)
            pattern_match = sample.str.match(pattern).mean() > 0.8

            if name_match or pattern_match:
                parsed = pd.to_datetime(
                    self.data[col].astype(str),
                    dayfirst=True,
                    errors="coerce",
                    format="mixed"
                )
                if parsed.notna().mean() > 0.8:
                    self.data[col] = parsed.dt.strftime("%m/%d/%Y")
                    self.data[col] = pd.to_datetime(self.data[col])

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
            sample = self.data[col].dropna().astype(str).str.lower()
            all_values = set(sample.unique())

            if all_values.issubset(BOOL_TRUE | BOOL_FALSE):
                self.data[col] = sample.map(lambda x: True if x in BOOL_TRUE else False)
    
    def _null_report(self):
        report = {}
        for col in self.data.columns:
            num_null = self.data.isna().sum()

            report[col] = {
                "Nulls" : num_null
            }
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

    def write_simple_report(self, report_cat : Dict[str, Dict[str, Any]], report_num: Dict[str, Dict[str, Any]], report_null: Dict[str, Dict[str, Any]]):
        with open("report.txt", "w") as f:
            f.write("Categorical Statistics")
            for col, stats in report_cat.items():
                f.write(col + "\n")
                for key, value in stats.items():
                    f.write(f"{key}: \n")
                    if isinstance(value, pd.Series):
                        text = value.head(n=5).to_string()
                        f.write(text + "\n")
                    else:
                        f.write(str(value))
                    f.write("\n")
                f.write("\n")

def null_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        num_null = df.isna().sum()
        report["values"] = num_null
    return report

def numerical_report(df : pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}

    for col in df.columns:
        mean = df[col].mean()
        median = df[col].median()
        std = df[col].std()
        min = df[col].min()
        max = df[col].max()
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        report[col] = {
            "mean" : mean,
            "median": median,
            "std": std,
            "min": min,
            "max": max,
            "IQR": IQR
        }
    return report

def categorical_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        counts = df[col].value_counts()
        counts = df[col].value_counts()
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
        return None

def parse_dollars(val: str) -> float | str:
    val = str(val).strip()
    if "$" in val:
        return float(val.replace("$", ""))
    try:
        return float(val) 
    except ValueError:
        return val
    
def correlation(df: pd.DataFrame) -> pd.DataFrame:
    numerical_cols = df.select_dtypes([np.number])
    return numerical_cols.corr()

def skewness_kurtosis(df: pd.DataFrame) -> tuple[pd.Series[Any], pd.Series[Any]]:
    numerical_cols = df.select_dtypes([np.number])

    skewness = numerical_cols.skew()
    kur = numerical_cols.kurtosis()

    return skewness, kur