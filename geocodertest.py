# -*- coding: utf-8 -*-
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
from random import randint
from imagesFetch import fetch
import parseGWorkHours  #parsing with google place details
from facepy import GraphAPI
from autoComplete import AutoComplete

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
            global key_index,key_index_fb
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        except:
            #check for actual error if required set no. of calls = 2500 (or whatever)
            key_index += 1
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        try:
            self.graph=GraphAPI(KEYS_FB[key_index_fb])
        except:
            key_index_fb= (key_index_fb+1)%len(KEYS_FB)
            self.graph=GraphAPI(KEYS_FB[key_index_fb])

        self.rows = []
        self.FIELDS = []
        self.autoComp = AutoComplete(key=KEYS)

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

            self.autoComp.main(self.rows)

            self._addGeocoding()
            self._addLocationPhoto()
            self._repairFromGraph()
            self._addFeaturedImage()
            self._formatWorkinghours()
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
        reader.fieldnames.extend(["listing_locations", "featured_image", "location_image", "fullAddress", "lat", "lng","prec_loc"]);
        reader.fieldnames.extend(["rating","reviews","author","Total Views","avg_rating","place_details", "fb_page", "cover_photo"]);
        reader.fieldnames.extend(['autocomplete_precise_address','place_id'])
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        inputFile.close();

    def _addGeocoding(self):
        geoLocationAdded = 0;
        geoLocationFailed = 0;
        precise_count = 0

        '''
        Each CSV file will be pertaining to a city.
        We can save almost half of the calls to geocoder API if we calculate the City cordinates only once.
        '''
        row = self.rows[0]
        if row["City"] is None:
            row = self.rows[1] #Highly unlikely that this will also fail
        row["City"] = row["City"].title()
        city = row["City"]
        print("Processing: " + row["City"])
        address_prec = "%s, %s" % (row["City"], row["Country"]) #calculating precise location
        geocode_city=self.gmaps.geocode(address_prec) #geocodes for city
        lat_prec=geocode_city[0]['geometry']['location']['lat']
        lng_prec=geocode_city[0]['geometry']['location']['lng']
        time.sleep(1); # To prevent error from Google API for concurrent calls

        for row in self.rows:
            if (row["lat"] is None or row["lat"] == ""):
                if row["Locality"] is None:         # To handle any exception for operations on 'NoneType'
                    row["Locality"] = ""
                row["City"] = city;
                row["Locality"] = row["Locality"].title()
                address = "%s %s, %s, %s, %s" % (row["Street Address"],row["Locality"],row["City"],row["Pincode"],row["Country"])
                row["fullAddress"] = address;
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

                geoLocationAdded+=1;
                if (geoLocationAdded%50==0):
                    print("Processed "+str(geoLocationAdded)+" rows.");

        print("Total precise entries: " + str(precise_count) + " out of " + str(geoLocationAdded) );

    def _addLocationPhoto(self):
        for row in self.rows:
            details_reviews=[]
            detail_placeid=""
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

                    row["Total Views"]=randint(200,500)
                    detail_placeid=requests.get(url2).json().get('result')

                    row['place_details']=detail_placeid
                    details=detail_placeid['photos']
                    try:
                        details_reviews=detail_placeid['reviews']
                    except Exception:
                        # FOR CASES WITH NO REVIEWS BUT THERE MAY BE PHOTOS
                        pass

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
                    row["Total Views"]=randint(50,200)
                if row["prec_loc"]=="true":
                    print "Adding rating and reviews"
                    f._addRatingsReviews(details_reviews,row)
                else:
                    row['avg_rating']=3.5

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

    def _addRatingsReviews(self,reviews,row):
        row["rating"],row['author'],row['reviews']="","",""
        total=0
        for i in range(len(reviews)):
            total += reviews[i]['rating']
            if i==(len(reviews)-1):
                row["rating"]+=str(reviews[i]['rating'])
                row['author']+=reviews[i]['author_name'].encode('utf-8')
                row['reviews']+=reviews[i]['text'].encode('utf-8')
            else:
                row["rating"]+=str(reviews[i]['rating'])+","
                row['author']+=reviews[i]['author_name'].encode('utf-8')+","
                row['reviews']+=reviews[i]['text'].encode('utf-8')+","
        if total == 0:
            row['avg_rating'] = 3.5
        else:
            row['avg_rating'] = round((total*1.0)/len(reviews),1)

    def _repairFromGraph(self):
        details=0;link=0;cover=0;website=0;pincode=0;street=0;dp=0
        for row in self.rows:
            try:
                search_result=self.graph.get("search?q=%s&fields=location&type=place"%(row['Name']))
                #search_result=self.graph.search(row['Name'],'place')
                node=dict()
                #profile_pic=dict()
                for place in search_result['data']:
                    if not 'location' in place:
                        continue
                    if row['City'].lower() == place['location']['city'].lower():
                        node=self.graph.get(place['id']+"?fields=location,description,phone,link,cover,website")
                        #profile_pic=self.graph.get(place['id']+"%2Fpicture%3Fheight%3D500%26width%3D500")
                        break
                #print(node)
##                if 'data' in profile_pic:
##                    if 'url' in profile_pic and 'is_silhouette' in profile_pic:
##                        if not row['Images URL'] and profile_pic['data']['is_silhouette'] == 'false':
##                            row['Images URL'] = profile_pic['data']['url']
##                            dp+=1
                if node:
                    if 'description' in node and not row['Details']:
                        row['Details'] = node['description']
                        #print "Added description "+node['description'][:40]+" to "+row["Name"]+" from facebook"
                        details+=1
                    if 'link' in node:
                        row['fb_page']=node['link']
                        #print "Added page "+node['link']+" to "+row["Name"]+" from facebook"
                        link+=1
                    if 'cover' in node:
                        row['cover_photo'] = node['cover']['source'] #tbd: download it!
                        #print "Added cover "+node['cover']['source']+" to "+row["Name"]+" from facebook"
                        cover+=1
                    if not row['Website']:
                        if 'website' in node:
                            row['Website'] = node['website']
                            #print "Added website "+node['website']+" to "+row["Name"]+" from facebook"
                            website+=1
                    if not row['Pincode'] and 'zip' in node['location'] :
                        row['Pincode']=node['location']['zip']
                        #print "Added pin "+node['location']['zip']+" to "+row["Name"]+" from facebook"
                        pincode+=1
                    if not row['Street Address'] and 'street' in node['location']:
                        row['Street Address'] = node['location']['street']
                        #print "Added address "+node['location']['street']+" to "+row["Name"]+" from facebook"
                        street+=1
            except:
               logging.exception("Error loading information from facebook for " + row['Name']);
        print "New Info Added from Facebook\nDetails:%d Facebook Link:%d Cover:%d \nWebsite:%d Pincode:%d Address:%d Images:%d"%(details,link,cover,website,pincode,street,dp)



    def _formatWorkinghours(self):
        for row in self.rows:
            if row['Working Hours'] is not None and row['Working Hours']!='':
                row['Working Hours'] = parseWorkingHours.parseWorkingHours(row['Working Hours']);
            else:
                try:
                    #if row['place_details'] is not None and row['place_details']['opening_hours']:
                    GPlacesWH=row['place_details']['opening_hours']['periods']
                    GWrkHours=parseGWorkHours.parse(GPlacesWH)
                    row['Working Hours']=GWrkHours
                except Exception:
                    row['Working Hours']=''

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
