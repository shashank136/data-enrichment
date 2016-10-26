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

class AutoComplete():
    def __init__(self, key):
        self.GOOGLE_API_KEYS = key
        self.key_index=0
        self.key = self.GOOGLE_API_KEYS[self.key_index]
        self.chain_failure = False      # TO DISTINGUISH BETWEEN CONCURRENT CALL FAILURE and QUERY-OVERLIMIT FAILURE

        self.autocomplete_flag = ['VERIFIED', 'NOT VERIFIED']
        # FOR STATE DATA TO BE USED BY AUTOCOMPLETE
        self.state_data_rows = []
        file_name = glob.glob('./state_data/city_state.csv')
        state_file = open(file_name[0],'r')
        state_reader = csv.DictReader(state_file, dialect=csv.excel)
        self.state_data_rows.extend(state_reader)
        state_file.close()

        self.rows = []
        # GLOBAL JSON DICTIONARY TO BE USED BY ALL FUNCTION RATHER THAN MAKING  DIRECT API CALLS
        self.json_objects = dict()

    def get_state(self,city):
        state = ''
        found = False

        for row in self.state_data_rows:
            if row['Name of City'].strip().lower() == city.strip().lower():
                state = row['State']
                found = True
                break
        if not found:
            print 'NO STATE MATCH FOR CITY'
            sys.exit()
        else:
            return state

    def graceful_request(self,url):
        chain_count = 0
        while True:
            resp = requests.get(url+self.GOOGLE_API_KEYS[self.key_index]).json()
            if resp['status'] == 'OK':
                break
            if resp['status'] == 'ZERO_RESULTS':
                break
            if resp['status'] == 'NOT_FOUND':
                return None

            print 'ERROR - RESENDING REQUEST'

            # TO DISTINGUISH BETWEEN SINGLE AND MULTIPLE FAILURES
            if self.chain_failure:
                print 'CHANGING KEYS'
                self.key_index = (self.key_index+1)%len(self.GOOGLE_API_KEYS)
                self.chain_failure = False
                print 'NEW KEY : ',self.GOOGLE_API_KEYS[self.key_index]
            else:
                self.chain_failure = True
                chain_count += 1

            if chain_count == len(self.GOOGLE_API_KEYS):
                print 'CONCURRENT CALL FAILURE. WAITING.....'
                chain_count = 0
                time.sleep(1)

        self.chain_failure = False
        return resp

    def website_parser(self,x):
        if x == '' or x is None:
            return ''
        ############
        #INITIAL CLEANUP
        x = x.strip()
        x = x.replace('//www.','//')
        #############

        filler_flag = False
        fillers = ['/','#']
        for _ in fillers:
            if _ in x[-1]:
                filler_flag = True
        if filler_flag:
            x = x[:-1]
        return x

    # REQUIRES COUNTRY CODE TO START WITH +, IF PRESENT
    def number_parser(self, x):
        flag_add = False
        numerals = ['0','1','2','3','4','5','6','7','8','9']
        allowed_start_symbols = numerals + ['+']

        ############
        #INITIAL CLEANUP
        x = x.strip()
        idx=0
        for _ in x:
            if _ in allowed_start_symbols:
                break
            idx += 1
        x = x[idx:]
        #############

        if x.find('+91') == 0:
            flag_add = True

        word = ''
        phone_number = []

        if flag_add:
            word = list(x[3:])
        else:
            word = list(x)

        non_zero_encountered = False
        for letter in word:
            # REMOVES 0 FROM START OF NUMBERS
            if not non_zero_encountered:
                if letter in numerals[1:]:
                    non_zero_encountered = True

            if non_zero_encountered:
                if letter in numerals:
                    phone_number.append(letter)
        return ''.join(phone_number)

    def analyze_prediction(self, row, address,state, allow_single, allow_state_matching,temp_json):
        address = address.replace('#','')
        extract = lambda x:'' if x is None else x
        phones = []
        websites = []

        for i in range(1,6):
            if row['Phone'+str(i)]:
                phones.append(self.number_parser(row['Phone'+str(i)]))
        if row['Website']:
            websites.append(row['Website'].strip())
        if row['Website2']:
            websites.append(row['Website2'].strip())

        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='
        resp = self.graceful_request(url)
        if resp is None:
            return False,''

        if len(resp["predictions"]) == 1 and allow_single:
            return True,resp["predictions"][0]

        if len(resp["predictions"]) >= 1:
            if allow_state_matching:
                found = False
                multiple_match = False
                correct_prediction = ''
                for x in resp["predictions"]:
                    for term in x["terms"]:
                        if term['value'].strip().lower() == state.strip().lower():
                            if not found:
                                correct_prediction = x
                                found = True
                            else:
                                multiple_match = True
                if found and not multiple_match:
                    self.update_json_object(correct_prediction['place_id'])
                    return True,correct_prediction

            for x in resp["predictions"]:
                resp_x = temp_json.get(x['place_id'])
                if resp_x is None:
                    url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+x['place_id']+'&key='
                    resp_x = self.graceful_request(url)
                    temp_json[x['place_id']] = resp_x

                # To prevent errors when graceful_request() returns 'None'
                if resp_x is None:
                    break
                resp_x = resp_x.get('result')
                # THIS GUARANTEES THE COUNTRY CODE TO START WITH +
                international_number = self.number_parser(extract(resp_x.get('international_phone_number')))
                for phone in phones:
                    if self.number_parser(phone) == international_number:
                        self.update_json_object(x['place_id'])
                        return True, x

            for website in websites:
                website = self.website_parser(website)
                found = False
                multiple_match = False
                correct_prediction = ''
                for x in resp["predictions"]:
                    resp_x = temp_json.get(x['place_id'])
                    if resp_x is None:
                        url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+x['place_id']+'&key='
                        resp_x = self.graceful_request(url)
                        temp_json[x['place_id']] = resp_x

                    # To prevent errors when graceful_request() returns 'None'
                    if resp_x is None:
                        break
                    resp_x = resp_x.get('result')
                    website_in_json = extract(resp_x.get('website'))
                    if website == self.website_parser(website_in_json):
                        if not found:
                            correct_prediction = x
                            found = True
                        else:
                            multiple_match = True
                if found and not multiple_match:
                    return True,correct_prediction
        return False,''

    def update_json_object(self, place_id):
        if self.json_objects.get('place_id') is None:
            url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+place_id+'&key='
            resp_x = self.graceful_request(url)
            if resp_x is None:
                return
            resp_x = resp_x.get('result')
            self.json_objects[place_id]=resp_x

    def main(self, rows_data):
        self.rows = rows_data
        self._autoComplete()
        self._updateAddress()
        self._addLocationPhoto()
        self._addRatingsReviews()
        self._googleUpdates()
        self._formatWorkinghours()
        # Dictionary self.json_objects is large
        # This should be released before the next file is opened as the current object won't go out of scope.
        # So _releaseMemory() should be the last function to run. Place other functions before this.
        self._releaseMemory()

    def _autoComplete(self):
        fixed_count = 0
        no_prediction_count = 0

        print '\nRUNNING AUTOCOMPLETE'
        state = self.get_state(self.rows[0]['City'])
        print 'STATE : ',state
        row_idx=2

        for row in self.rows:
            temp_json = dict()
            address = ''
            valid = True                    # COMPLETE ADDRESS AVAILABLE

            flag = False
            prediction = ''

            if (row['Locality'] == ''):
                valid = False
            else:
                address = row['Name'] + ', ' + row['Locality']
                # False : Same state results not insured, hence not going for single prediction
                # True : To ensure same state match
                flag,prediction =  self.analyze_prediction(row,address,state,False,True,temp_json)

            if flag == False:
                if row['Pincode'] != '':
                    address = row['Name'] + ', ' + row['Pincode']
                    # True : Because same state results are insured, hence single prediction can be taken + Added advantage of wrong information in csv being overcomed
                    flag, prediction = self.analyze_prediction(row,address,state,True,True,temp_json)
                    # FOR LONG QUERIES IT'S NOT ALWAYS INSURED THAT PINCODE IS IN PREDICTION. THIS MAKES THE DECISION TO NOT CHECK STATE, A WRONG STEP.
                    # HENCE COFORMING HERE FOR THOSE CASES
                    # AS IT's NOT A GENERAL CASE Flag CANNOT BE FALSE
                    if flag==True:
                        found = False
                        matched_parts = prediction["matched_substrings"]
                        for part in matched_parts:
                            offset = int(part["offset"])
                            length = int(part["length"])
                            word = prediction["description"][offset:(offset+length)]
                            if row['Pincode'].strip() in word.strip():
                                found=True
                                break
                        if not found:
                            flag = False

                if flag == False:
                    address = row['Name'] + ', ' + row['City']
                    # False : If city name is a subset of locality name of any place, it will show in prediction and that may not be in same state. Hence state match is necessary
                    # True : Sometimes institute's name is a subset of a large name. For those cases a single prediction with the matching state leads to inaccuracy, given the earlier queries didn't work out. This case needs review, so keeping it True.
                    flag,prediction =  self.analyze_prediction(row,address,state,False,True,temp_json)

                    if flag == False and valid:
                        address = row["Street Address"] + ' ' + row["Locality"] + ', ' + row["City"]

                        # False : State match is not a guarntee because of high noise in query.
                        # False : Single matching state is not a guaranteed. because of high noise in query
                        flag, prediction =  self.analyze_prediction(row,address,state,False,False,temp_json)

            if flag == True:
                fixed_count += 1
                row['place_id'] = prediction['place_id']
                self.update_json_object(prediction['place_id'])
            else:
                no_prediction_count += 1

            row_idx += 1

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
                    if 'locality' in i['types']:
                        row['City']=i['long_name'].title()
                    if 'postal_code' in i['types']:
                        row['Pincode']=i['long_name']
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

    def _releaseMemory(self):
        self.json_objects.clear()
