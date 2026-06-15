import pandas as pd
from catboost import CatBoostClassifier, Pool
from typing import Any
def feature_importance(target: pd.Series[Any], test: pd.DataFrame):
    pooled = Pool(test, target)
    model = CatBoostClassifier(iterations=2, depth=3, learning_rate=1)
    model.fit(test, target)
    
    features = model.feature_importances_

    print(features)
