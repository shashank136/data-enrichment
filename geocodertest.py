import csv
import logging
import glob
import os
import time
import googlemaps
import parseWorkingHours
from slugify import slugify
import urllib
import requests
import bs4
import re
import math
from imagesFetch import fetch
from imagesFetch import correctImage


KEYS = [
        'AIzaSyCgs8C71RqvWoeO69XBXVPQH006i7v4IkM', #Ananth's
        'AIzaSyCcijQW6eCvvt1ToSkjaGA4R22qBdZ0XsI', #Aakash's
        'AIzaSyATi8d86dHYR3U39S9_zg_dWZIFK4c86ko' #Shubhankar's
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
        self.FIELDS = []

    def process(self):
        fileNames = glob.glob('./input/*.csv');
        print fileNames
        for fileName in fileNames:
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0];
            self._readCSV(fileName);
            self._addGeocoding();
            self._addLocationPhoto();
            self._addFeaturedImage();
            self._formatWorkinghours();
            self._writeCSV("./output/processed_"+fileBaseName+".csv");

    def _readCSV(self, fileName):
        inputFile = open(fileName, 'r')
        sample_text = ''.join(inputFile.readline() for x in range(3))
        dialect = csv.Sniffer().sniff(sample_text);
        inputFile.seek(0);
        reader = csv.DictReader(inputFile, dialect=dialect)
        # skip the head row
        # next(reader)
        # append new columns
        reader.fieldnames.extend(["listing_locations", "featured_image", "location_image", "fullAddress", "lat", "lng","prec_loc"]);
        reader.fieldnames.extend(["rating","reviews","author"]);
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        inputFile.close();

    def _addGeocoding(self):
        geoLocationAdded = 0;
        geoLocationFailed = 0;
        for row in self.rows:
            if (row["lat"] is None or row["lat"] == ""):
                if row["Locality"] is None:         # To handle any exception for operations on 'NoneType'
                    row["Locality"] = ""
                if row["City"] is None:
                    row["City"] = ""
                row["Locality"] = row["Locality"].title()
                row["City"] = row["City"].title()
                address = "%s %s, %s, %s, %s" % (row["Street Address"],row["Locality"],row["City"],row["Pincode"],row["Country"])

                address_prec = "%s, %s" % (row["City"], row["Country"]) #calculating precise location

                row["fullAddress"] = address;
                row["listing_locations"] = row["Locality"] + ", " + row["City"];
                geocode_city=self.gmaps.geocode(address_prec) #geocodes for city
                lat_prec=geocode_city[0]['geometry']['location']['lat']
                lng_prec=geocode_city[0]['geometry']['location']['lng']

                try:
                    time.sleep(1); # To prevent error from Google API for concurrent calls
                    geocode_result = self.gmaps.geocode(address);
                    if(len(geocode_result)>0):
                        row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                        row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                    else:
                        logging.warning("Geocode API failure for : '" + address + "'");
                        time.sleep(1);
                        geocode_result = self.gmaps.geocode(row["Name"] + ", " + address);
                        if (len(geocode_result) > 0):
                            row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                            row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                        else:
                            logging.warning("Trying by adding name failed for: '" + address + "'"+"hence taking city geocodes");
                            #geoLocationFailed+=1;
                            row["lat"] = lat_prec;
                            row["lng"] = lng_prec;

                except Exception as err:
                    logging.exception("Something awful happened when processing '"+address+"'");
                    geoLocationFailed+=1;

                if int(math.ceil(abs(float(lat_prec)-float(row["lat"])))) ==1 and int(math.ceil(abs(float(lng_prec)-float(row["lng"])))) ==1:
                    '''
                    for checking precise location by
                    getting difference in city geocodes
                    and place geocodes
                    '''
                    row["prec_loc"]="true"
                else:
                    row["lat"] = lat_prec;
                    row["lng"] = lng_prec;

                geoLocationAdded+=1;
                if (geoLocationAdded%20==0):
                    print("Processed "+str(geoLocationAdded)+" rows.");

        time.sleep(1); # To prevent error from Google API for concurrent calls
        print("Successfully completed processing of (" + str(geoLocationAdded-geoLocationFailed) + "/" + str(geoLocationAdded) + ") rows.");

    def _addLocationPhoto(self):
        for row in self.rows:
            details_reviews=[]
            list_pics=[]
            str_place=""
            if row["lat"]==0:
               row['location_image'] = '';

            else:
                myLocation = (row["lat"], row["lng"]);
                #print myLocation
                url1='https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+row['Name']+'&types=establishment&location='+str(row['lat'])+','+str(row['lng'])+'&radius=50000&key='+KEYS[key_index]
                #print 'Autocomplete URL',url1
                try:
                    url2='https://maps.googleapis.com/maps/api/place/details/json?placeid='
                    placeid=requests.get(url1).json().get('predictions')[0]['place_id'];
                    url2=url2+placeid+"&key="+KEYS[key_index]
                    #print 'Place id ',row['Name'], url2



                    detail_placeid=requests.get(url2).json().get('result')
                    details=detail_placeid['photos']
                    details_reviews=detail_placeid['reviews']
                    #print details_reviews

                    for i in range(len(details)):
                        url3='https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photoreference='+details[i]['photo_reference']+'&key='+KEYS[key_index]

                        t=requests.get(url3)
                        list_pics.append(t.url) #resolving redirects it returns final url

                    str_place=",".join(list_pics)
                    #print "Images URL initail",row["Images URL"]
                    x=row['Images URL']
                    #new_imgs=correctImage(x) #checking the images for thumbnail
                    #print "New imgs geo",new_imgs
                    row["Images URL"]=str_place+row['Images URL']

                except Exception:
                    print "Image not found for "+row['Name']
                if row["prec_loc"]=="true":
                    print "Adding rating and reviews"
                    f._addRatingsReviews(details_reviews,row)

    def _addFeaturedImage(self):
        for row in self.rows:
            if not row["Images URL"]:
                #image=imagesFetch(row["Name"])
                row['featured_image'] = fetch(row['Name']); #creates png image
                row['Images URL']=row['featured_image'];
                #print row['featured_image']
            else:
                row['featured_image'] = row['Images URL'].split(",")[0].strip();

    def _addRatingsReviews(self,reviews,row):
        row["rating"],row['author'],row['reviews']="","",""
        for i in range(len(reviews)):
            if i==(len(reviews)-1):
                row["rating"]+=str(reviews[i]['rating'])
                row['author']+=str(reviews[i]['author_name'])
                row['reviews']+=str(reviews[i]['text'])
            else:
                row["rating"]+=str(reviews[i]['rating'])+","
                row['author']+=str(reviews[i]['author_name'])+","
                row['reviews']+=str(reviews[i]['text'])+","

    def _formatWorkinghours(self):
        for row in self.rows:
            if not row["Working Hours"]:
                row['Working Hours'] = '';
            else:
                row['Working Hours'] = parseWorkingHours.parseWorkingHours(row['Working Hours']);

    def _writeCSV(self, fileName):
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
