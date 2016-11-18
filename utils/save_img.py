import glob
import hashlib
import requests
import csv
import sys,os
import os.path
import urllib
csv.field_size_limit(sys.maxsize)

def UTF8(data):
	try:
		return data.encode('utf-8','ignore')
	except:
		return data

class SaveImg():
	def __init__(self):
	    self.rows = []
	    self.FIELDS = []
	
	def process(self):
		fileNames=glob.glob('../output/updated_*.csv')
		print fileNames
		for fileName in fileNames:
			print 'Cur file is',fileName
			self.rows=[]
			self.fields=[]
			fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
			self._readCSV(fileName)
			print len(self.rows)
			self.save_img()
			try:
				os.mkdir('../output/new_output/')
			except:
				pass
			self._writeCSV("../output/new_output/"+fileBaseName+".csv");
	
	def _readCSV(self, fileName):
		inputFile = open(fileName, 'r')
		reader = csv.DictReader(inputFile, dialect=csv.excel)
		self.FIELDS = reader.fieldnames;
		self.rows.extend(reader);
		inputFile.close();
	
	def save_img(self):
		print 'Downloading...'
		for row in self.rows:
			s=''
			lis_imgs=[]
			new_lis_imgs=[]
			cont=''
			h=hashlib.new('ripemd160')
			s=row['listing_gallery']
			lis_imgs=s.split(',')
			for i in lis_imgs:
				if 'static.career' not in i and i!=' ':
					print '## Trying Method 1'
	  				h.update(i+str(row['EduID']))
					cont=h.hexdigest()
					print cont
					if not os.path.exists('../output/images/%s.jpg'%cont):
						try:
							req=requests.get(i)
							if req.status_code==200:
								# print 'Downloading..'
								with open('../output/images/%s.jpg'%cont,'wb') as f:
									f.write(req.content)
		    						f.close()
		    						print 'Download success'
		    					new_lis_imgs.append('http://static.careerbreeder.com/output/images/%s.jpg'%cont)

						except:
							try:
								print '## Trying Method 2'
								urllib.urlretrieve(i,'../output/images/%s.jpg'%cont)
								new_lis_imgs.append('http://static.careerbreeder.com/output/images/%s.jpg'%cont)
								print 'Download success'
							except Exception as err:
								print err
					else:
						print 'File already downloaded'

    		if len(new_lis_imgs)!=0:
    			row['listing_gallery']=",".join(new_lis_imgs)
    			row['featured_image']=row['listing_gallery'][0]
	
	def _writeCSV(self, fileName):
		print "Writing to CSV..."
		try:
			csvFile = open(fileName, 'w');
			writer = csv.DictWriter(csvFile, fieldnames=self.FIELDS);
			writer.writerow(dict(zip(self.FIELDS, self.FIELDS)))
			for row in self.rows:
				for i in row:
					row[i] = UTF8(row[i])
				writer.writerow(row)
			csvFile.close()
		except Exception as err:
			logging.exception("Something awful happened when processing result.csv");

if __name__=='__main__':
	f=SaveImg()
	f.process()




