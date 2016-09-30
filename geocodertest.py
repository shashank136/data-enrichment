# -*- coding: utf-8 -*-
import csv
import logging
import glob
import os
import time
import googlemaps
from slugify import slugify
import urllib
import requests
import bs4
import re
import math
from random import randint
from imagesFetch import fetch

from facepy import GraphAPI
from autoComplete import AutoComplete
from fbGraph import processGraph

KEYS = [
        'AIzaSyCgs8C71RqvWoeO69XBXVPQH006i7v4IkM', #Ananth's
        'AIzaSyCcijQW6eCvvt1ToSkjaGA4R22qBdZ0XsI', #Aakash's
        'AIzaSyATi8d86dHYR3U39S9_zg_dWZIFK4c86ko', #Shubhankar's
        'AIzaSyBVmpXHCROnVWDWQKSqZwgnGFyRAilvIc4'  #Shashwat's
]
KEYS_FB=['1040517959329660|c7e458dd968fca33d05a18fddbcd86ab',   #Rohit
         '1697721727215546|a372f9c8b412e8b053094042fc4b42e6',   #Shantanu
          ]# format is AppID|AppSecret, API version: 2.7
key_index_fb = 0
key_index = 0


class geocoderTest():
    def __init__(self, geo_type='google'):

        try:
            global key_index
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        except:
            #check for actual error if required set no. of calls = 2500 (or whatever)
            key_index += 1
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        self.rows = []
        self.FIELDS = []
        self.autoComp = AutoComplete(key=KEYS)
        self.fbGraph =  processGraph(key=None)

    def process(self):
        fileNames = glob.glob('./input/sample_big.csv');
        print fileNames
        fileCount = 0
        for fileName in fileNames:
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
            self._readCSV(fileName)
            self._removeThumbs()

            self.autoComp.main(self.rows)
            
            self._addGeocoding()
            self.fbGraph.processAll(self.rows)
            self._addFeaturedImage()
            #self._formatWorkinghours()
            fileCount +=1
            self._writeCSV("./output/processed_"+fileBaseName+".csv");
            print("***Successfully processed "+str(fileCount)+" files.***");

    def _readCSV(self, fileName):
        inputFile = open(fileName, 'r')
        #sample_text = ''.join(inputFile.readline() for x in range(3))
        #dialect = csv.Sniffer().sniff(sample_text);
        #inputFile.seek(0);
        reader = csv.DictReader(inputFile, dialect=csv.excel)   # Using default excel dialect because sniffer fails to form the right container from 3 rows of sample text
        # skip the head row
        # next(reader)
        # append new columns
        reader.fieldnames.extend(["Mail2", "listing_locations", "featured_image", "location_image", "fullAddress", "lat", "lng","prec_loc"]);
        reader.fieldnames.extend(["rating","reviews","author","Total Views","avg_rating","place_details", "fb_page", "fb_verified"]);
        reader.fieldnames.extend(['autocomplete_precise_address','place_id','perma_closed'])
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        inputFile.close();

    def _addGeocoding(self):
        geoLocationAdded = 0;
        geoLocationFailed = 0;
        precise_count = 0
        print 'ADDING GEOCODES...'
        '''
        Each CSV file will be pertaining to a city.
        We can save almost half of the calls to geocoder API if we calculate the City cordinates only once.
        '''
        
        for row in self.rows:
            if (row["lat"] is None or row["lat"] == ""):
                #row = self.rows[0]
                #if row["City"] is None:
                #    row = self.rows[1]#Highly unlikely that this will also fail
                #row["City"] = row["City"].title()
                city = row["City"].title()
                row["City"]=city
                # print("Processing: " + row["City"])
                address_prec = "%s, %s" % (row["City"], row["Country"]) #calculating precise location
                geocode_city=self.gmaps.geocode(address_prec) #geocodes for city
                lat_prec=geocode_city[0]['geometry']['location']['lat']
                lng_prec=geocode_city[0]['geometry']['location']['lng']
                #print 'lat,lng ',lat_prec,lng_prec
                time.sleep(1); # To prevent error from Google API for concurrent calls

                if row["Locality"] is None:         # To handle any exception for operations on 'NoneType'
                    row["Locality"] = ""
                #row["City"] = city;
                row["Locality"] = row["Locality"].title()
                address = "%s %s, %s, %s, %s" % (row["Street Address"],row["Locality"],row["City"],row["Pincode"],row["Country"])
                #if row['fullAddress'] is 'None' or row['fullAddress']=='':
                row["fullAddress"] = address.title();
                row["listing_locations"] = row["Locality"] + ", " + row["City"];

                try:
                    time.sleep(1); # To prevent error from Google API for concurrent calls
                    geocode_result = self.gmaps.geocode(address);
                    if(len(geocode_result)>0):
                        row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                        row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                    else:
                        time.sleep(1);
                        geocode_result = self.gmaps.geocode(row["Name"] + ", " + address);
                        if (len(geocode_result) > 0):
                            row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                            row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                        else:
                            #geoLocationFailed+=1;
                            row["lat"] = lat_prec;
                            row["lng"] = lng_prec;

                except Exception as err:
                    logging.exception("Something awful happened when processing '"+address+"'");
                    geoLocationFailed+=1;

                try:
                    check = int(math.ceil(abs(float(lat_prec)-float(row["lat"])))) ==1 and int(math.ceil(abs(float(lng_prec)-float(row["lng"])))) ==1
                except:
                    check = False
                if check:
                    '''
                    for checking precise location by
                    getting difference in city geocodes
                    and place geocodes
                    '''
                    row["prec_loc"]="true"
                    precise_count +=1
                else:
                    row["lat"] = lat_prec;
                    row["lng"] = lng_prec;
                if row['lat'] is None or row['lat']=='':
                    row['lat']=lat_prec
                if not row['lng']:
                    row['lng']=lng_prec

                geoLocationAdded+=1;
                if (geoLocationAdded%50==0):
                    print("Processed "+str(geoLocationAdded)+" rows.");

        print("Total precise entries: " + str(precise_count) + " out of " + str(geoLocationAdded) );
   

    def _removeThumbs(self):
        for row in self.rows:
            row["Images URL"] = ",".join(filter(lambda url: not 'businessphoto-t' in url,row["Images URL"].split(",")))

    def _addFeaturedImage(self):
        for row in self.rows:
            if not row["Images URL"]:
                #image=imagesFetch(row["Name"])
                row['featured_image'] = fetch(row['Name']); #creates png image
                row['Images URL']=row['featured_image'];
                #print row['featured_image']
            else:
                row['featured_image'] = row['Images URL'].split(",")[0].strip();

    def _writeCSV(self, fileName):
        print "Writing to CSV..."
        try:
            # DictWriter
            csvFile = open(fileName, 'w');
            writer = csv.DictWriter(csvFile, fieldnames=self.FIELDS);
            # write header
            writer.writerow(dict(zip(self.FIELDS, self.FIELDS)));
            for row in self.rows:
                writer.writerow(row)
            csvFile.close()
        except Exception as err:
            logging.exception("Something awful happened when processing result.csv");

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    f = geocoderTest()
    f.process()
