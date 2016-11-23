import glob
import hashlib
import requests
import csv
import sys, os
import os.path
import urllib
import time

csv.field_size_limit(sys.maxsize)

start_time=time.time()
print "Starting time %s"%start_time

def UTF8(data):
	try:
		return data.encode('utf-8', 'ignore')
	except:
		return data


class SaveImg:
	def __init__(self):
		self.rows = []
		self.FIELDS = []

	def process(self):
		fileNames = glob.glob('../output/Bookout.csv')
		print fileNames
		for fileName in fileNames:
			print 'Cur file is', fileName
			self.rows = []
			self.fields = []
			self.noi=0
			fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
			self._readCSV(fileName)
			print len(self.rows)
			self.save_img()
			try:
				os.mkdir('../output/new_output/')
			except:
				pass
			self._writeCSV("../output/new_output/" + fileBaseName + ".csv");

	def _readCSV(self, fileName):
		inputFile = open(fileName, 'r')
		reader = csv.DictReader(inputFile, dialect=csv.excel)
		self.FIELDS = reader.fieldnames;
		self.rows.extend(reader);
		inputFile.close();

	def save_img(self):
		print 'Downloading...'
		for row in self.rows:
			s = ''
			lis_imgs = []
			new_lis_imgs = []
			cont = ''
			file_ext=''
			h = hashlib.new('ripemd160')
			s = row['listing_gallery']
			lis_imgs = s.split(',')
			for i in lis_imgs:
				if 'http' in i:
					self.noi+=1
					h.update(i + str(row['EduID']))
					cont = h.hexdigest()
					file_ext=i.split('.')[-1].strip()
					print file_ext
					print cont
					if not os.path.exists('../output/images/%s.%s' % (cont,file_ext)):
						try:
							print '## Trying..'	
							urllib.urlretrieve(i, '../output/images/%s.%s' % (cont,file_ext))
							new_lis_imgs.append('%s.%s' % (cont,file_ext))
							print 'Download success'
						except Exception as err:
							print err
					else:
						print 'File already downloaded'
						
			if len(new_lis_imgs) != 0:
				row['listing_gallery'] = ",".join(new_lis_imgs)

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
			print "\n>>>Time--> %s seconds" %(time.time()-start_time)
			print "\n>>>Total Images--> ",self.noi
		except Exception as err:
			print err
			print "Something awful happened when processing result.csv";


if __name__ == '__main__':
	f = SaveImg()
	f.process()
