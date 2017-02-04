import csv
import logging
import sys
import glob
import os

MAX_SIZE=20*10**6 # ~20mb
csv.field_size_limit(sys.maxint)
def UTF8(data):
    try:
        return data.encode('utf-8','ignore')
    except:
        return data

class ConcatCSV:
    def __init__(self):
        self.rows=[]
        self.fields=[]
        self.files=[]
        self.output_file_name="updated_combined.csv"

    def _readCSV(self, fileName):
        try:
            size=os.path.getsize(fileName)
            if size > MAX_SIZE:
                print "Leaving out large File %s which has size = %s byte"%(fileName,size)
                return
            inputFile = open(fileName, 'rb')
        except:
            logging.exception("error opening file "+fileName);
        reader = csv.DictReader(inputFile, dialect=csv.excel)
        self.files.append(fileName)
        if not self.fields:
            self.fields = reader.fieldnames
            self.output_file_name = fileName
        else:
            fieldSet = set(reader.fieldnames)
            originalFieldSet=set(self.fields)
            newFields =list(fieldSet-originalFieldSet)
            if newFields:
                print "Warning: Fields mismatch at %s"%fileName
                print "New Fields had to be added to the whole table:",newFields
                self.fields.extend(newFields)
        self.rows.extend(reader)
        inputFile.close()

    def _writeCSV(self):
        print "Backing up small files :"
        backup_path = os.path.join(os.path.dirname(self.output_file_name),'SMALL_FILES')
        try:
            os.makedirs(backup_path)
        except os.error as e:
            pass #assumed to exist
        for i in self.files:
            print i
            os.rename(i,os.path.join(backup_path,os.path.basename(i)))
        print "Writing to first CSV..."
        try:
            csvFile = open(self.output_file_name, 'wb');
            writer = csv.DictWriter(csvFile, fieldnames=self.fields);
            writer.writerow(dict(zip(self.fields, self.fields)))
            for row in self.rows:
                for i in row:
                    row[i] = UTF8(row[i])
                writer.writerow(row)
            csvFile.close()


            print "Output File %s is of %s bytes"%(self.output_file_name,os.path.getsize(self.output_file_name))
        except Exception as err:
            logging.exception("Error occured while joining "+self.output_file_name)

    def _readByMatch(self,inputFiles):
        fileNames = glob.glob(inputFiles)
        for i in fileNames:
                self._readCSV(i)

##    def _readByList(self,fileList=[]):
##        for i in fileList:
##            self._readCSV(i)

    def main(self):
        inputFiles = "../output/updated_*.csv"
        self._readByMatch(inputFiles)
        if len(self.files) > 1:
            self._writeCSV()
