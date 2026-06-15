import os
from typing import List
from pathlib import Path
def get_files(dir_path: str) -> List[str]:
    files = os.listdir(dir_path)
    return files

def pprint_datasets(dir_path: str) -> Path:
    files = get_files(dir_path)
    print("Please select a dataset to load in:")
    for i, x in enumerate(files):
        print(f"\t{i+1}). {x}")
    
    thing = int(input())
    return Path("./Datasets/" + files[thing-1])