import pprint
import glob
import os
import csv
from collections import OrderedDict

class findPattern():
	
	def __init__(self):
		self.rows=[]
		self.fields=[]
	
	def proFiles(self):
		fileNames=glob.glob('./output/processed_*.csv')
		fileCount=0
		for fileName in fileNames:
			self.rows=[]
			fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
			self._readCSV(fileName)
			self._findPattern(self.rows,fileName)

	def _readCSV(self,fileName):
		inputFile=open(fileName,'r')
		reader=csv.DictReader(inputFile,dialect=csv.excel)
		self.rows.extend(reader);
		inputFile.close();
	
	def _findPattern(self,rows,fileName):
		file.write('---'+str(fileName).replace('./output/processed_','').upper()+'---')
		lis_phn=''
		dicPhn={}
		phnLis=[]
		for row in rows:
			for i in range(1,6):
				if len(row['Phone'+str(i)])>=10:
					x=str(row['Phone'+str(i)]).replace('+91','').replace(' ','').replace('(','').replace(')','').replace('-','')[:6]
					y=str(row['Phone'+str(i)]).replace('+91','').replace(' ','').replace('(','').replace(')','').replace('-','')[:5]
					try:
						dicPhn[x]+=1
						dicPhn[y]+=1
					except:
						dicPhn[x]=1
						dicPhn[y]=1	
		y={k: v for k, v in dicPhn.iteritems() if v>25}
		y=(sorted(y.items(),key=lambda x:x[1]))
		if len(y)==0:
			file.write('\nNo pattern freq more than 25\n\n')	
		else:
			y=str(y)
			y=y.replace('),','),\n')
			file.write('\n'+y+'\n\n')
				
if __name__=='__main__':
	file=open('./output/PatMatch','w+')
	x=findPattern()
	x.proFiles()
	file.close()
	print 'Output saved to ./output/PatMatch'