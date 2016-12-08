import csv
import os
import glob

class ProcessDuplicate():
	def __int__(self):
		self.rows = []
		self.FIELDS = []

	def process(self):
		fileNames_2 = glob.glob('./sulekha_other_temp/*.csv')
		fileNames_1 = glob.glob('./sulekha_temp/*.csv')
		central = {}
		central_same = {}
		same_repeat = 0
		other_repeat = 0
		total = 0
		number_of_files = 0
		sulekha_temp = 0
		sulekha_other_temp = 0

		print "wait for execution to complete"
		for fileName_1 in fileNames_1:
			number_of_files = number_of_files + 1 #counts how many files are getting executed, not related with logic of this program
			self.rows = []
			self.FIELDS = []
			fileBaseName = os.path.splitext(os.path.basename(fileName_1))[0]
			self.readCSV(fileName_1)
			for row in self.rows:
				total = total + 1 #counts total number of entries, not related with logic of this program
				city = row['City']
				locality = row['Locality']
				name = row['Name']

				if city in central.keys():
					if locality in central[city].keys():
						if name in central[city][locality]:
							same_repeat = same_repeat + 1
						else:
							central[city][locality].append(name)
							sulekha_temp = sulekha_temp + 1
					else:
						central[city][locality] = []
						central[city][locality].append(name)
						sulekha_temp = sulekha_temp + 1
				else:
					central[city] = {}
					central[city][locality] = []
					central[city][locality].append(name)
					sulekha_temp = sulekha_temp + 1
		
		print "###############\nThe following data are for sulekha_temp:\n"
		print "number of Same folder entries repeat: ",same_repeat
		print "total: ",total
                print "total number of files: ",number_of_files
		print "finished building central dictionary:\n"
##################################################################################

		same_repeat = 0
		total = 0
		number_of_files = 0

		for fileName_2 in fileNames_2:
                        self.rows = []
                        self.FIELDS = []
			number_of_files = number_of_files + 1
                        
                        self.readCSV(fileName_2)
                        for row in self.rows:
				total = total + 1
                                city = row['City']
                                locality = row['Locality']
                                name = row['Name']

                                if city in central_same.keys():
                                        if locality in central_same[city].keys():
                                                if name in central_same[city][locality]:
                                                        same_repeat = same_repeat + 1
                                                else:
                                                        central_same[city][locality].append(name)
							sulekha_other_temp = sulekha_other_temp + 1
                                        else:
                                                central_same[city][locality] = []
                                                central_same[city][locality].append(name)
						sulekha_other_temp =sulekha_other_temp + 1
                                else:
                                        central_same[city] = {}
                                        central_same[city][locality] = []
                                        central_same[city][locality].append(name)
					sulekha_other_temp = sulekha_other_temp + 1

		print "#############\nThe following are for sulekha_other_temp:\n"
		print "number of Same entries in sulekha_other_temp: ",same_repeat
		print "total: ",total
                print "total number of files: ",number_of_files


##################################################################################
                for fileName_2 in fileNames_2:
                	self.rows = []
                	self.FIELDS = []
                	
                	self.readCSV(fileName_2)
                	for row in self.rows:
                		city = row['City']
                		locality = row['Locality']
                		name = row['Name']

                		if city in central.keys():
                			if locality in central[city].keys():
                				if name in central[city][locality]:
                					other_repeat = other_repeat + 1
							# remove the # tags of the following to check results
							#print "row in sulekha_other_temp:\n",row
							#print "\ncentral data:\n",central[city][locality],"\n",name,"\n",locality,"\n",city
							#inp = input()
                
                print "End of execution\n"
                print "number of same entries:",other_repeat
		print "\n\nSulekha_temp distinct entries: ",sulekha_temp
		print "\nSulekha_other_temp distinct entries: ",sulekha_other_temp

	def readCSV(self, fileName):
		inputFile = open(fileName, 'r')
		reader = csv.DictReader(inputFile, dialect=csv.excel)
		self.FIELDS = reader.fieldnames;
		self.rows.extend(reader);
		inputFile.close()

if __name__ == "__main__":
	f = ProcessDuplicate()
	f.process()
