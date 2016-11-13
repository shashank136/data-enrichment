import csv
import logging
import glob
import os
import time
import googlemaps
from slugify import slugify
import urllib
import requests
import sys
from fbGraph import processGraph,UTF8
import pandas as pd

csv.field_size_limit(sys.maxsize)


KEYS = [
        'AIzaSyAzPTH0yXszPpqMO72o-zGb3hwgQgN1MSI', #Rohit
        'AIzaSyCgs8C71RqvWoeO69XBXVPQH006i7v4IkM', #Ananth's
        'AIzaSyCcijQW6eCvvt1ToSkjaGA4R22qBdZ0XsI', #Aakash's
        'AIzaSyA-sGk-2Qg_yQAoJtQ1YUPKEYPCQ5scf5A', #Shubhankar's
        'AIzaSyBVmpXHCROnVWDWQKSqZwgnGFyRAilvIc4',  #Shashwat's
        'AIzaSyAD58vGvx1OdgRq-XdYFZW8cyKhODkg6lc',   #Sisodia
        'AIzaSyDs9N58rJ1n-C7qQ0B1qnhAP8DSzzLd1sU',    #Singh
        'AIzaSyC5-mD5yfBlyy1K7H_HKhCk-05d9kF02_k',  #Akarsh
        'AIzaSyCq7QLuMkfcm-68JL95Au5x9Vc_0qCp8iU'   #Shardul
]
key_index = 0



class UpdateLoc():
    def __init__(self,geo_type='google'):

        try:
            global key_index
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        except:
            key_index += 1
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        self.rows = []
        self.FIELDS = []
        self.state_data_rows = []
        self.lis_city=[]
        file_name = glob.glob('./state_data/city_state.csv')
        with open(file_name[0],'r') as state_file:
            state_reader = csv.DictReader(state_file, dialect=csv.excel)
            self.state_data_rows.extend(state_reader)
        for row in self.state_data_rows:
            self.lis_city.append(row['Name of City'])

    def process(self):
        fileNames = glob.glob('./output/updated_*.csv');
        print fileNames
        fileCount = 0
        for fileName in fileNames:
            print fileName
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
            self._readCSV(fileName)
            self._updateLoc()
            try:
                os.mkdir("./output/out_new")
            except Exception:
                pass
            self._writeCSV("./output/out_new/"+fileBaseName+".csv"); #folder for saving output file to

    def _readCSV(self, fileName):
        inputFile = open(fileName, 'r')
        reader = csv.DictReader(inputFile, dialect=csv.excel)
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        inputFile.close();


    def _updateLoc(self):
        print 'Updating...'
        for row in self.rows:
            if row['City']=='New Delhi':
                row['City']='Delhi'
            if row['City']=='Bangalore':
                row['City']='Bengaluru'
            if row['place_id'] !='' or row['place_id']!=None:
                url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+row['place_id']+'&key='+KEYS[key_index]
                resp = requests.get(url).json()
                try:
                    add_comp=resp['result']['address_components']
                    self._matchCity(row,add_comp)
                
                except:
                    pass

    def _matchCity(self,row,add_comp):
        dic={}
        city_found=0
        for i in add_comp:
            dic[i["types"][0]]=i["long_name"]
        # print "dic",dic
        for k,v in dic.items():
            if v in self.lis_city:
                city_found=1
                row['City']=v
                break
        if not city_found:
            row['City']=dic['administrative_area_level_1']
        if row['City']=='New Delhi':
            row['City']='Delhi'
        if row['City']=='Bangalore':
            row['City']=='Bengaluru'   
        row['Locality']=dic['sublocality_level_1']

    def _writeCSV(self, fileName):
        print "Writing to CSV..."
        try:
            # DictWriter
            csvFile = open(fileName, 'w');
            writer = csv.DictWriter(csvFile, fieldnames=self.FIELDS);
            # write header
            writer.writerow(dict(zip(self.FIELDS, self.FIELDS)))
            for row in self.rows:
                for i in row:
                    row[i] = UTF8(row[i])
                writer.writerow(row)
            csvFile.close()
        except Exception as err:
            logging.exception("Something awful happened when processing result.csv");

if __name__=='__main__':
    f=UpdateLoc()
    f.process()
