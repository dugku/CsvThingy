from csv_reader import CSV_Read
from revised import NewReader, check_uniqueness, correlation
from plotter import Plot, Palette, PASTEL_PALETTE, DARK_PALETTE
from dataset_selector import get_files, pprint_datasets
import pandas as pd
from feature_importance import feature_importance
from get_target import get_tar
"""
TODO:
Create a menu for csv laoding since doing it manually is annoying at this point
The report should be exported as a HTML but right now need to get the other stuff figured out first
"""

def main():
	thing = pprint_datasets("./Datasets")
	reader = NewReader(thing)
	menu(reader)

def menu(newReader: NewReader):
	while True:
		print("Please select an action to perform on the csv file:")
		print("1. Print CSV")
		print("2. Print Column Types")
		print("3. Full Data Report")	
		print("4. Time Series Plotting")
		print("5. Basic Feature Importance")
		choice = int(input())	
		if choice == 1:
			newReader.print_csv()
		if choice == 2:
			newReader.column_types()
		if choice == 3:
			newReader.standardize_data()
			newReader.desc_stats() #for both numeric and categorical
			cat_col, num_col = newReader.get_col_types()
			cat_col = check_uniqueness(cat_col)
			num_col = check_uniqueness(num_col)
			corr = correlation(newReader.data)
			print(num_col)
			plot = Plot(cat_col, num_col, corr, palette=DARK_PALETTE)
			plot.histogram()
			plot.bar_graph()
			plot.heatmap_correlation()
			plot.missing_values_vis()
			plot.box_plot()
		if choice == 4:
			series_data = pprint_columns(newReader.data)
			target = pprint_columns(newReader.data)
			plot.time_series_plotting(series_data, target)
		if choice == 5:
			values = get_tar(newReader.data)
			feature_importance(values[0], values[1])

def pprint_columns(df: pd.DataFrame) -> pd.Series:
	print("Please Select a Column:")
	for i, x in enumerate(df.columns):
		print(f"{i+1}: {x}")
	choice = int(input())
	return df[df.columns[choice-1]]

if __name__ == '__main__':
	main()
