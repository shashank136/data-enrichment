import csv
import glob,sys
csv.field_size_limit(sys.maxint)

class Normalize_City:
    def __init__(self):
        self.alias_universe = dict()
        self.initUniverse()

    def initUniverse(self):
        u_rows = []
        with open('city_alias/alias_data.csv', 'rb') as csvFile:
            reader = csv.DictReader(csvFile, dialect=csv.excel)
            u_rows.extend(reader)
        for row in u_rows:
            map_value = row['Current_Use']
            for key, value in row.items():
                if key != 'Current_Use' and value:
                    self.alias_universe[value.lower()] = map_value

    def read_csv(self,file_path,fields,rows):
        with open(file_path, 'rb') as csvFile:
            reader = csv.DictReader(csvFile, dialect=csv.excel)
            fields.extend(reader.fieldnames)
            rows.extend(reader)

    def write_csv(self,file_path,fields,rows):
        with open(file_path, 'wb') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=fields)
            writer.writerow(dict(zip(fields,fields)))
            for row in rows:
                writer.writerow(row)

    def normalize(self, rows):
        for row in rows:
            if row['City'] and self.alias_universe.get(row['City'].lower()):
                row['City'] = self.alias_universe[row['City'].lower()]

    def main(self, files):
        for file_path in files:
            print file_path
            fields, rows = [], []
            self.read_csv(file_path, fields, rows)
            self.normalize(rows)
            self.write_csv(file_path, fields, rows)

if __name__ == '__main__':
    print '\nNORMALIZING CITY NAMES'
    files = glob.glob("output/updated_*.csv")
    obj = Normalize_City()
    obj.main(files)
