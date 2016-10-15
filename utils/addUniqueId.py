import csv
import logging
import os

class AddUniqueId():
    def __init__(self):
        self.rows = []
        self.FIELDS = []

    def getFileNames(self, root, file_ext):
        fileNames = [];
        for dirpath, dirnames, filenames in os.walk(root):
            for fileName in filenames:
                if fileName.endswith(file_ext):
                    fileNames.append(os.path.join(dirpath, fileName));
        return fileNames;

    def process(self):
        PATH = "../input/test/";
        csvFileNames = self.getFileNames(PATH, 'csv');
        print(csvFileNames);
        fileCount = 0;
        eduId = 0;
        for fileName in csvFileNames:
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
            print("\nProcessing file : "+fileName+"\n");
            fileCount += 1;
            with open(fileName, 'rb') as input, open(fileName+".new", 'wb') as output:
                reader = csv.reader(input, delimiter=',')
                writer = csv.writer(output, delimiter=',')
                all = []
                row = next(reader)
                row.insert(0, 'EduID')
                all.append(row)
                for row in reader:
                    eduId += 1
                    row.insert(0, eduId)
                    all.append(row)
                writer.writerows(all);
                os.remove(fileName);
                os.rename(fileName+".new", fileName);
            print("***Successfully processed "+str(fileCount)+" file(s).***");

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    f = AddUniqueId()
    f.process()