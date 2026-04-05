from csv_reader import CSV_Read
def main():
	menu()

def menu():
	print("Please select a action to perform on the csv file:")
	print("1. Print CSV")
	print("2. Print Numerical Statistics")
	print("3. Print Categorial Statistics")
	choice = int(input())
	reader = CSV_Read("adult.csv")
	if choice == 1:
		reader.print_csv()
	if choice == 2:
		reader.numerical_stats()
	if choice == 3:
		reader.categorical_stats()
	if choice == 4:
		reader.get_IQR()
	if choice == 5:
		reader.confidence_interval()
	menu()
if __name__ == '__main__':
	main()
