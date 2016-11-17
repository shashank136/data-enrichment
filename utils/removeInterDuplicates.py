import csv
import glob,sys
import joinCSV
csv.field_size_limit(sys.maxsize)

class Inter_Duplicates:
    def __init__(self):
        self.main_fields = ['post_title','Street Address','Locality','City','Pincode']
        self.hash_universe = set()
        self.removed_EduID = []

    def read_csv(self,file_path,fields,rows):
        with open(file_path, 'r') as csvFile:
            reader = csv.DictReader(csvFile, dialect=csv.excel)
            fields.extend(reader.fieldnames)
            rows.extend(reader)

    def rhash(self,row):
        k=""
        for i in self.main_fields:
            k+=str(row[i]).lower().strip()
        return hash(k)

    def multi_idx_delete(self,rows,indexes):
        rev_indexes = sorted(indexes,reverse=True)
        for index in rev_indexes:
            self.removed_EduID.append(int(rows[index]['EduID']))
            del rows[index]

    def remove_similar(self,rows):
        print "\tInitial Records :",len(rows)
        indexes = []
        sub_count = 0
        for idx,row in enumerate(rows):
            hsh = self.rhash(row)
            if hsh in self.hash_universe:
                indexes.append(idx)
                sub_count += 1
            else:
                self.hash_universe.add(hsh)
        self.multi_idx_delete(rows,indexes)
        print '\tRemoved :',sub_count
        print '\tFinal Records :',len(rows)

    def write_csv(self,file_path,fields,rows):
        with open(file_path, 'w') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=fields)
            writer.writerow(dict(zip(fields,fields)))
            for row in rows:
                writer.writerow(row)

    def main(self,files):
        for file_path in files:
            print file_path
            fields = []
            rows = []
            self.read_csv(file_path,fields,rows)
            self.remove_similar(rows)
            self.write_csv(file_path,fields,rows)
            print '\n'

        print 'UNIVERSE SIZE : ',len(self.hash_universe)
        print 'TOTAL REMOVED : ',len(self.removed_EduID)
        print '\n',self.removed_EduID

if __name__ == '__main__':
    joinCSV.ConcatCSV().join('../output/updated_*.csv')
    files = glob.glob("../output/updated_*.csv")
    obj = Inter_Duplicates()
    obj.main(files)
