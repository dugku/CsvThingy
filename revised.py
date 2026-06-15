from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
import pprint
import re
from pathlib import Path
from dateutil.parser import parse as dateutil_parse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from scipy import stats

"""
TODO fix:
--Fix some stuff in _convert date (Maybe)
--parser percent return None but num_report doesn't handle if apparently (Not done but will be one the list for a while)
"""
#This is now getting messy, tech debt is real.
"""
TODO add:
Outlier detection: Most likely will do IQR, maybe will implement isolation forest, or different method (IQR Method done)
More visual missing values (Did now need to format that shit)
Duplicate row detection ()
Maybe automatically transform if a column is extremely skewed or not(?)
Cluster Analysis -- just to see if there are any natural groupding with out any advanced data maniplutation
Since some dataset(s) will have extremely high dimensionally PCA or something will be good to have.
"""


DATE_KEYWORDS_EXACT = {"date", "dt", "created", "updated"}
DATE_KEYWORDS_RISKY = {"day", "month", "year", "time"}
DATE_KEYWORD_BLOCKLIST = {"by", "for", "rate", "zone", "experience", "limit", "type"}
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
        dups = report_dups(self.data)

        self.corr_matrix = correlation(self.data)
        self.skew, self.kurt = skewness_kurtosis(self.data)
        
        self.write_html_report(
            report_cat=report_cat,
            report_num=report_num,
            report_null=report_null,
            report_outliers=report_outliers,
            dups=dups,
            filename="./Reports/report.html",
            template_dir="/Users/uggh/Desktop/CsvThingy/templates",
            template_name="report_temp.html",
        )
    def print_csv(self):
        pprint.pprint(self.data)
    
    def _is_date_column_name(self, col: str) -> bool:
        tokens = set(re.split(r"[_\s\-]+", col.lower()))
        if tokens & DATE_KEYWORD_BLOCKLIST:
            return False
        if tokens & DATE_KEYWORDS_EXACT:
            return True
        if len(tokens & DATE_KEYWORDS_RISKY) >= 2:
            return True
        return False
    
    def _looks_like_date(self, val: str) -> bool:
        try:
            dateutil_parse(val, fuzzy=False)
            return True
        except (ValueError, OverflowError):
            return False

    def _convert_date(self):
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            if sample.empty:
                continue

            name_match = self._is_date_column_name(col)
            pattern_match = sample.apply(self._looks_like_date).mean() > 0.8

            if name_match or pattern_match:
                parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
                if parsed.notna().mean() > 0.8:
                    self.data[col] = pd.to_datetime(self.data[col], errors="coerce", format="mixed")
     
    def _percents(self):
        for col in self.data.columns:
            sample = self.data[col].dropna().astype(str)
            if sample.str.contains("%").any():
                converted = self.data[col].apply(parse_percent)
                if converted.notna().sum() >= self.data[col].notna().sum() * 0.8:
                    self.data[col] = pd.to_numeric(converted, errors="coerce")

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
        bool_map = {**{k: True for k in BOOL_TRUE}, **{k: False for k in BOOL_FALSE}}
        for col in self.data.columns:
            normalized = self.data[col].astype(str).str.strip().str.lower()
            non_null_values = set(normalized[self.data[col].notna()].unique())

            if non_null_values and non_null_values.issubset(BOOL_TRUE | BOOL_FALSE):
    
                self.data[col] = normalized.map(bool_map).where(self.data[col].notna())
    
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

    def write_html_report(self, report_cat: Dict[str, Dict[str, Any]], report_num: Dict[str, Dict[str, Any]], report_null: Dict[str, Dict[str, Any]], report_outliers: Dict[str, Dict[str, Any]], dups: Dict[str, Any], 
        filename: str = "./Reports/report.html", 
        template_dir: str = "/Users/uggh/Desktop/CsvThingy/templates",
        template_name: str = "report_temp.html",
    ) -> None:
        categorical_data = {
            col: {k: _make_json_safe(v) for k, v in stats.items()}
            for col, stats in report_cat.items()
        }

        numerical_data = {
            col: {k: _make_json_safe(v) for k, v in stats.items()}
            for col, stats in report_num.items()
        }

        null_data = {
            col: {k: _make_json_safe(v) for k, v in stats.items()}
            for col, stats in report_null.items()
        }

        outlier_data = {
            col: {k: _make_json_safe(v) for k, v in stats.items()}
            for col, stats in report_outliers.items()
        }

        duplicate_data = {k: _make_json_safe(v) for k, v in dups.items()}

        corr_matrix = (
            self.corr_matrix.round(3).to_dict()
            if self.corr_matrix is not None and not self.corr_matrix.empty
            else None
        )

        skew_data = (
            {k: _make_json_safe(v) for k, v in self.skew.round(3).to_dict().items()}
            if self.skew is not None and not self.skew.empty
            else None
        )

        kurt_data = (
            {k: _make_json_safe(v) for k, v in self.kurt.round(3).to_dict().items()}
            if self.kurt is not None and not self.kurt.empty
            else None
        )

        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

        template = env.get_template(template_name)

        html = template.render(
            report_title="Data Analysis Report",
            categorical_data=categorical_data,
            numerical_data=numerical_data,
            null_data=null_data,
            outlier_data=outlier_data,
            duplicate_data=duplicate_data,
            corr_matrix=corr_matrix,
            skew_data=skew_data,
            kurt_data=kurt_data,
        )

        Path(filename).write_text(html, encoding="utf-8")

def null_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        report[col] = {
            "null_count": int(df[col].isna().sum()),
            "null_percent": (int(df[col].isna().sum()) / len(df[col])) * 100,
            "non_null": int(df[col].count()),
            "all_null": df[col].isna().all(),
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
        Q05 = df[col].quantile(0.05)
        Q50 = df[col].quantile(0.50)
        Q95 = df[col].quantile(0.95)
        df_range = max_col - min_col
        zero_count = (df[col] == 0).sum()
        negative_numbers = (df[col] < 0).sum()
        coeff_var = std_col / mean_col
        mad = stats.median_abs_deviation(df[col], scale=1.0)

        report[col] = {
            "mean" : mean_col ,
            "median": median_col,
            "std": std_col,
            "min": min_col,
            "max": max_col,
            "IQR": IQR,
            "Q1" : Q1,
            "Q3": Q3,
            "Q05": Q05,
            "Q50": Q50,
            "Q95": Q95,
            "range": df_range,
            "zero_count": zero_count,
            "negative_numbers": negative_numbers,
            "coeff_var": coeff_var,
            "mad": mad
        }
    return report

def categorical_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    report = {}
    for col in df.columns:
        counts = df[col].value_counts(dropna=True)
        max_value = counts.max()
        min_value = counts.min()
        length = len(df[col])
        normal_counts = df[col].value_counts(normalize=True) 
        report[col] = {
            "counts": counts.head(n=10),
            "max": max_value,
            "min": min_value,
            "length": length,
            "top_value": counts.idxmax(),
            "top_percent": normal_counts.head(n=7),
            "rare_values": normal_counts[normal_counts <= 0.025].head(n=7).index.tolist()
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

def report_dups(df: pd.DataFrame) -> Dict[str, Any]:
    report = {}
    report["Dupes"] = int(df.duplicated().sum()) 
    return report

def _make_json_safe(value):
    if isinstance(value, pd.Series):
        return {str(k): _make_json_safe(v) for k, v in value.items()}
    if isinstance(value, pd.Index):
        return [_make_json_safe(v) for v in value.tolist()]
    if isinstance(value, np.ndarray):
        return [_make_json_safe(v) for v in value.tolist()]
    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if pd.isna(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None

    return value