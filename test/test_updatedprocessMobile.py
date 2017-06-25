import csv
import updatedprocessMobile

def test_processMobile():

	src = open('../sample_data.csv')

	src_reader = csv.reader(src,delimiter=",")

	src_list = []

	for row in src_reader:
		x = row
		src_list.append(x)

	# val = False
	tabb = updatedprocessMobile.processAll(src_list)

	 for i in check_tab:
		if check_tab[i] == True:
			print(str(i)+' '+'following is a vaid number')
		else:
			print(str(i)+' '+'following is an invalid number')
	
