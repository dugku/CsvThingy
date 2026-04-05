import pprint
import numpy as np
from statistics import median, fmean, stdev, pvariance
import math
import scipy.stats as st
class CSV_Read():
	'''
	This will be cool once I am done but not yet
	'''
	def __init__(self, path):
		self.path = path
		self.data = []
		self.numeric_col = []
		self.categorical_cols = []
		self.read_lines()

	def read_lines(self):
		with open(self.path, "r+") as f:
			line = f.readlines()
			for l in line:
				j = l.rstrip()
				if not j:
					continue
				splitted = j.split(",")
				self.data.append(splitted)
		self.thingy_columns()

	def thingy_columns(self):
		row1 = self.data[1]
		for i, x in enumerate(row1):
			if is_numeric(x):
				self.numeric_col.append(i)
			else:
				self.categorical_cols.append(i)

	def numerical_stats(self):
		rows = self.data[1:]
		for i in self.numeric_col:
			values = []
			for r in rows:
				return_val = check_empty(r[i])
				if return_val is not None: #These two lines are not best practice but I will rewrite a little later
					values.append(float(r[i]))
				else:
					continue
			np_values = np.array(values)
			hm = mean_cols(np_values)
			med = median_cols(np_values)
			std = standard_devation(np_values)
			var = variance_cols(np_values)
			col_name = self.data[0][i]
			print(f"--- {col_name} ---")
			print(f"  Mean:     {hm}")
			print(f"  Median:   {med}")
			print(f"  Std Dev:  {std}")
			print(f"  Variance: {var}")

	def categorical_stats(self):
		rows = self.data[1:]
		for i in self.categorical_cols:
			value_dict = {}
			for r in rows:
				if r[i] in value_dict:
					value_dict[r[i]] += 1
				else:
					value_dict[r[i]] = 1 
			col_name = self.data[0][i]
			nice = get_portion(value_dict)
			print(f"--- {col_name} ---")
			for f, j in nice.items():
				print(f"{f}: {j}")

	def get_IQR(self):
		rows = self.data[1:]
		for i in self.numeric_col:
			values = []
			for r in rows:
				values.append(float(r[i]))
			np_values = np.array(values)
			results = percentile_IQR(np_values)
			col_name = self.data[0][i]
			print(f"--- {col_name} ---")
			print(f"25% Percentile {results[0]}")
			print(f"50% Percentile {results[1]}")
			print(f"75% Percentile {results[2]}")

	def confidence_interval(self):
		rows = self.data[1:]
		for i in self.numeric_col:
			values = []
			for r in rows:
				return_val = check_empty(r[i])
				if return_val is not None: #These two lines are not best practice but I will rewrite a little later
					values.append(float(r[i]))
				else:
					continue
			np_values = np.array(values)
			results = calc_ci(np_values)
			col_name = self.data[0][i]
			print(f"--{col_name}--")
			print(results)


	def print_csv(self):
		pprint.pprint(self.data)

def calc_ci(vals, confidence = 0.95):
	df = len(vals) - 1

	if df == 0:
		return None

	mean = np.mean(vals)
	sem = st.sem(vals)

	return st.t.interval(confidence, df, loc=mean, scale=sem)
def get_portion(all_values):
	total_entries = 0
	return_dict = {}
	for i in all_values.values():
		total_entries += i

	for x, h in all_values.items():
		return_dict[x] = (h / total_entries) * 100

	return return_dict

def check_empty(val):
	if val == "":
		return None
	else:
		return val

def percentile_IQR(vals):
	return np.percentile(vals, [25, 50, 75])

def mean_cols(vals):
	return np.mean(vals)

def median_cols(vals):
	return np.median(vals)

def standard_devation(vals):
	return np.std(vals)

def variance_cols(vals):
	return np.var(vals)

def is_numeric(entry):
	try:
		float(entry)
		return True
	except ValueError:
		return False