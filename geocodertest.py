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
from mobileAPI import processMobile
from facepy import GraphAPI
from autoComplete import AutoComplete
from fbGraph import processGraph,UTF8
from mediaWiki import mediaWiki
from validate_email import filterMails


KEYS = [
        'AIzaSyCp4DIN0mzmvQxcq0IOMtu48ZmFwr3qyj8', #Rohit
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
        #self.new_rows=[]
        self.FIELDS = []
        self.filterMails=filterMails
        self.autoComp = AutoComplete(key=KEYS)
        self.fbGraph =  processGraph(key=None)
        self.mobiles = processMobile()
        self.wikipedia = mediaWiki()

    def process(self):
        fileNames = glob.glob('./input/*.csv');
        print fileNames
        fileCount = 0
        for fileName in fileNames:
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0]
            self._readCSV(fileName)
            self._removeThumbs()
            print "\nCurrent file is",fileName,"\n"
            self.autoComp.main(self.rows)
            self._addGeocoding()
            self.fbGraph.processAll(self.rows)
            self._addFeaturedImage()
            self.mobiles.processAll(self.rows)
            self.filterMails(self.rows,fileBaseName)
            self.wikipedia.processAll(self.rows)
            '''
            added patternmatcher
            '''
            # self._formatWorkinghours()
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


        reader.fieldnames.extend(["Mail2", "listing_locations", "featured_image", "location_image", "fullAddress", "lat", "lng","viewport","prec_loc"]);
        reader.fieldnames.extend(["rating","reviews","author","Total Views","avg_rating","place_details", "fb_page", "fb_verified"]);
        reader.fieldnames.extend(['autocomplete_precise_address','place_id','perma_closed','Mobiles','wikipedia','fb_posts','fb_photos','fb_videos','fb_workingHours'])
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        #self.rows=self.new_rows
        inputFile.close();

    def _addGeocoding(self):
        geoLocationAdded = 0;
        geoLocationFailed = 0;
        precise_count = 0
        city_geo={}
        new_city=""
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
                new_city = row["City"].title()
                row["City"]=new_city
                # print("Processing: " + row["City"])
                if new_city not in city_geo:
                    address_prec = "%s, %s" % (row["City"], row["Country"]) #calculating precise location
                    geocode_city=self.gmaps.geocode(address_prec) #geocodes for city
                    city_geo[new_city]={'lat':geocode_city[0]['geometry']['location']['lat']}
                    city_geo[new_city]['lng']=geocode_city[0]['geometry']['location']['lng']
                    #print 'lat,lng ',lat_prec,lng_prec
                    time.sleep(1); # To prevent error from Google API for concurrent calls
                lat_prec=city_geo[new_city]['lat']
                lng_prec=city_geo[new_city]['lng']

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

    def _titleCase(self):
        separators=[' ',',','.','/','-']
        count = 0
        for row in self.rows:
            for key in ['Street Address', 'Locality', 'City', 'Country', 'listing_locations', 'autocomplete_precise_address', 'author', 'fullAddress']:
                if key in row:
                    data = row[key]
                separate=True
                new=[]
                if not data:
                    continue
                for i in data:
                    if i in separators:
                        separate = True
                    elif separate:
                        new.append(i.upper())
                        separate = False
                        continue
                    new.append(i)
                row[key] = ''.join(new)
                if data!=row[key]:
                    count+=1

    def _writeCSV(self, fileName):
        print "Writing to CSV..."
        try:
            self._titleCase()
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

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    f = geocoderTest()
    f.process()
