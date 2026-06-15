import pandas as pd
import pprint
from typing import Any, Tuple
def get_tar(df: pd.DataFrame) -> Tuple[pd.Series[Any], pd.DataFrame]:
    cols = df.columns
    print("Please choose a target column from:\n")
    for i in range(len(cols)):
        print(f"{i+1}: {cols[i]}")
    choice = int(input())
    target = df.iloc[:, choice-1]
    pprint.pprint(target)
    df_new = df.drop(df.columns[choice-1], axis=1)
    return target, df_new
