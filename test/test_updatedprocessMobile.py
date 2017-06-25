import csv
import updatedprocessMobile

def test_processMobile():

	src = open('data-enrichment/test/sample_data.csv')

	src_reader = csv.reader(src,delimiter=",")

	src_list = []

	for row in src_reader:
		x = row
		src_list.append(x)

	# val = False
	tabb = updatedprocessMobile.processAll(src_list)
	
	def compare(dictOne,dictTwo):
    		for keyOne in dictOne:
        		for keyTwo in dictTwo:
            			if keyOne == keyTwo[]:
                		print(dictTwo[keyTwo])

	for i in tabb:
		if tabb[i] == True:
			print(str(i)+' '+'following is a vaid number')
		else:
			print(str(i)+' '+'following is an invalid number')
	
