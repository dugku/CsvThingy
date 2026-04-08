from csv_reader import CSV_Read
from revised import NewReader
def main():
	reader = NewReader("Titanic-Dataset.csv")
	menu(reader)

def menu(newReader: NewReader):
	while True:
		print("Please select an action to perform on the csv file:")
		print("1. Print CSV")
		print("2. Print Column Types")
		print("3. Standardize Data")	
		choice = int(input())	
		if choice == 1:
			newReader.print_csv()
		if choice == 2:
			newReader.column_types()
		if choice == 3:
		    newReader.standardize_data()
		if choice == 4:
			newReader.desc_stats() #for both numeric and categorical
		if choice == 5:
			newReader._null_report()

if __name__ == '__main__':
	main()
