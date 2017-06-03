import csv
import updatedprocessMobile

def test_processMobile():

	src = open('../sample_data.csv')

	src_reader = csv.reader(src,delimiter=",")

	src_list = []

	for row in src_reader:
		x = row
		src_list.append(x)

	val = False
	val = updatedprocessMobile.processAll(src_list)
	assert val== True
