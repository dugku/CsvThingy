from csv_reader import CSV_Read
from revised import NewReader, check_uniqueness, correlation
from plotter import Plot

"""
TODO:
Create a menu for csv laoding since doing it manually is annoying at this point
The report should be exported as a HTML but right now need to get the other stuff figured out first
"""

def main():
	reader = NewReader("Titanic-Dataset.csv")
	menu(reader)

def menu(newReader: NewReader):
	while True:
		print("Please select an action to perform on the csv file:")
		print("1. Print CSV")
		print("2. Print Column Types")
		print("3. Full Data Report")	
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
			plot = Plot(cat_col, num_col, corr)
			plot.histogram()
			plot.bar_graph()
			plot.heatmap_correlation()
if __name__ == '__main__':
	main()

#What is the total of the dkjs algo. algorithms class some eom date.
