# -*- coding: utf-8 -*-
import requests
import csv
import sys
import glob
from random import randint
import parseGWorkHours  #parsing with google place details
import parseWorkingHours
import math
import time
from fbGraph import safe_dec_enc
from API.gmap_placeid_api import GMAP_ID

class AutoComplete():
    def __init__(self, key):
        self.GOOGLE_API_KEYS = key
        self.key_index=0
        self.key = self.GOOGLE_API_KEYS[self.key_index]
        self.rows = []
        # GLOBAL JSON DICTIONARY TO BE USED BY ALL FUNCTION RATHER THAN MAKING  DIRECT API CALLS
        self.json_objects = dict()
        self.gmap_api = GMAP_ID()

    def main(self,rows_data,state):
        self.rows = rows_data
        self._autoComplete(state)
        self._updateAddress()
        self._googleUpdates()
        self._remove_intra_duplicates()
        self._addLocationPhoto()
        self._addRatingsReviews()
        self._formatWorkinghours()
        # Dictionary self.json_objects is large
        # This should be released before the next file is opened as the current object won't go out of scope.
        # So _releaseMemory() should be the last function to run. Place other functions before this.
        self._releaseMemory()

    def _autoComplete(self,state):
        fixed_count = 0
        no_prediction_count = 0

        print '\nRUNNING AUTOCOMPLETE'
        print 'STATE : ',state

        for row in self.rows:
            row['State'] = state
            ######################
            resp = self.gmap_api.get_id(row)
            if resp['status_code'] == 201:
                row['place_id'] = resp['place_id']
                resp_x = self.gmap_api.get_id_details(resp['place_id'])
                if resp_x['status_code'] == 201:
                    self.json_objects[resp['place_id']]=resp_x['place_details']
                    fixed_count += 1
                elif (400 <= resp_x['status_code'] < 600):
                    print 'ERROR:', repr(resp_x)
                    sys.exit(0)
            elif (400 <= resp['status_code'] < 600):
                print 'ERROR:', repr(resp)
                sys.exit(0)
            else:
                no_prediction_count += 1
            #####################
            row.pop('State', None)

        print '####################'
        print 'VERIFIED     : ',fixed_count
        print 'NOT VERIFIED : ',no_prediction_count
        print '####################\n'

    def _updateAddress(self):
        print 'UPDAING ADDRESS'
        row_idx = 2
        for row in self.rows:
            if row['place_id'] is not None and row['place_id'] != '':
                resp = self.json_objects[row['place_id']]
                row['autocomplete_precise_address'] = resp['formatted_address']
            row_idx += 1

    def _addLocationPhoto(self):
        no_place_id=0
        progress=0
        print '\nAdding photos...please wait...'
        for row in self.rows:
            details_reviews=[]
            detail_placeid=""
            list_pics=[]
            str_place=""
            if row['place_id'] is not None and row['place_id']!='':
                no_place_id+=1
                resp=self.json_objects[row['place_id']]
                progress+=1
                try:
                    photos=resp['photos']
                    row["Total Views"] = len(photos)*randint(200,250)
                    for i in range(len(photos)):
                        photo_url='https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photoreference='+photos[i]['photo_reference']+'&key='+self.GOOGLE_API_KEYS[self.key_index]
                        t=requests.get(photo_url)
                        list_pics.append(t.url)

                    str_place=",".join(list_pics)
                    if row['Images URL']:
                        row['Images URL'] = str_place + "," + row['Images URL']
                    else:
                        row['Images URL'] = str_place

                except Exception:
                    #print "Image Not found"
                    row['Total Views'] = randint(100,300)
                #print "len jsonObj, progress",len(self.json_objects),progress

            else:
                row['Total Views'] = randint(100,300)
            #sys.stdout.write("\r%d%%" % int(math.ceil((float(progress)/self.fixed_count)*100)))
            #sys.stdout.flush()
        print "\nNo of place id ->"+str(no_place_id)

    def _addRatingsReviews(self):
        for row in self.rows:
            row["rating"],row['author'],row['reviews']="","",""
            total=0
            if row['place_id'] is not None and row['place_id']!='':
                resp=self.json_objects[row['place_id']]
                try:
                    reviews=resp['reviews']
                    row["Total Views"] += len(reviews)*randint(500,600)
                    for i in range(len(reviews)):
                        total += reviews[i]['rating']
                        if i==(len(reviews)-1):
                            row["rating"]+=str(reviews[i]['rating'])
                            row['author']+=reviews[i]['author_name'].encode('utf-8')
                            row['reviews']+=reviews[i]['text'].encode('utf-8').replace(",","&#44;")
                        else:
                            row["rating"]+=str(reviews[i]['rating'])+","
                            row['author']+=reviews[i]['author_name'].encode('utf-8')+","
                            row['reviews']+=reviews[i]['text'].encode('utf-8').replace(",","&#44;")+","
                    if total==0:
                        row['avg_rating']=3.5
                    else:
                        row['avg_rating']=round((total*1.0)/len(reviews),1)
                except Exception:
                    pass
                    row['avg_rating']=3.5
            else:
                row['avg_rating']=3.5

    def _cityName(self, row, add_comp):
        union_territory = ['chandigarh','delhi','puducherry','lakshadweep','andaman and nicobar islands','dadra and nagar haveli','daman and diu']
        gen_case = row['City']       # genral case
        for i in add_comp:
            if 'administrative_area_level_1' in i['types'] and i['long_name'].lower() in union_territory:
                return i['long_name'].title()
            if 'locality' in i['types']:
                gen_case = i['long_name'].title()
        return gen_case

    def _googleUpdates(self):
        no_vprt=0
        for row in self.rows:
            if row['place_id'] is not None and row['place_id']!='':
                resp=self.json_objects[row['place_id']]
                try:
                    if resp['permanently_closed']:
                        row['perma_closed']='true'
                        row['Name']=row['Name']+' [Address Unverified]'
                        print "Permanently closed is ",row['Name']
                except:
                    pass
                try:
                    view=resp['geometry']['viewport']
                    row['viewport']=view
                    no_vprt+=1
                except:
                    pass
                add_comp=resp['address_components']
                for i in (add_comp):
                    if 'sublocality_level_1' in i['types']:
                        row['Locality']=i['long_name'].title()
                    if 'postal_code' in i['types']:
                        row['Pincode']=i['long_name']
                row['City'] = self._cityName(row, add_comp)
                row['fullAddress']=resp['formatted_address']
                row['lat']=resp['geometry']['location']['lat']
                #print 'Lat',row['lat']
                row['lng']=resp['geometry']['location']['lng']
                if row['Website'] is None or row['Website']=='':
                    try:
                        website=resp['website']
                        row['Website']=website
                    except Exception:
                        pass
        print 'viewports for ',no_vprt
    def _formatWorkinghours(self):
        for row in self.rows:
            if row['Working Hours'] is not None and row['Working Hours']!='':
                row['Working Hours'] = parseWorkingHours.parseWorkingHours(row['Working Hours']);
            else:
                try:
                    #if row['place_details'] is not None and row['place_details']['opening_hours']:
                    resp=self.json_objects[row['place_id']]
                    GPlacesWH=resp['opening_hours']['periods']
                    GWrkHours=parseGWorkHours.parse(GPlacesWH)
                    row['Working Hours']=GWrkHours
                except Exception:
                    row['Working Hours']=''

    def rhash(self,row):
        main_fields = ['Name','Street Address','Locality','City','Pincode']
        k=""
        for i in main_fields:
            k+=str(safe_dec_enc(row.get(i), True)).lower().strip()
        return hash(k)

    def _remove_intra_duplicates(self):
        groups =dict()
        for row in self.rows:
            hsh = self.rhash(row)
            if hsh in groups:
                groups[hsh].append(row)
            else:
                groups[hsh] = [row]
        total_count = 0
        for i in groups:
            sub_count = 0
            groups[i].pop(0)
            for row in groups[i]:
                self.rows.remove(row)
                sub_count += 1
            total_count += sub_count
        print '\nREMOVED INTRA-DUPLICATES : ',total_count

    def _releaseMemory(self):
        self.json_objects.clear()
