import requests
import csv
import sys
import glob

class AutoComplete():
    def __init__(self, key):
        self.GOOGLE_API_KEYS = key
        self.key_index=0
        self.key = self.GOOGLE_API_KEYS[self.key_index]
        self.chain_failure = False      # TO DISTINGUISH BETWEEN CONCURRENT CALL FAILURE and QUERY-OVERLIMIT FAILURE

        self.autocomplete_flag = ['FIXED', 'MULTIPLE MATCHED', 'NONE MATCHED', 'NO INPUT DATA', 'NO PREDICTION']
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
        while True:
            resp = requests.get(url+self.GOOGLE_API_KEYS[self.key_index]).json()
            if resp['status'] == 'OK':
                break
            if resp['status'] == 'ZERO_RESULTS':
                break
            print 'ERROR - RESENDING REQUEST'

            # TO DISTINGUISH BETWEEN SINGLE AND MULTIPLE FAILURES
            if self.chain_failure:
                print 'CHANGING KEYS'
                self.key_index = (self.key_index+1)%len(self.GOOGLE_API_KEYS)
                self.chain_failure = False
            else:
                self.chain_failure = True

        self.chain_failure = False
        return resp

    # REQUIRES COUNTRY CODE TO START WITH +, IF PRESENT
    def parser(self, x):
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

    def no_prediction_cases(self, row, address):
        extract = lambda x:'' if x is None else x
        phones = []
        if row['Phone1'] != '' and row['Phone1'] is not None:
            phones.append(row['Phone1'])
        if row['Phone2'] != '' and row['Phone2'] is not None:
            phones.append(row['Phone2'])
        if row['Phone3'] != '' and row['Phone3'] is not None:
            phones.append(row['Phone3'])
        if row['Phone4'] != '' and row['Phone4'] is not None:
            phones.append(row['Phone4'])
        if row['Phone5'] != '' and row['Phone5'] is not None:
            phones.append(row['Phone5'])

        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='
        resp = self.graceful_request(url)
        if len(resp["predictions"]) == 1:
            print '\t-->','  ',resp["predictions"][0]["description"]
            return True, resp["predictions"][0]['place_id']

        elif len(resp["predictions"]) > 1:
            print '\tMATCHING PHONE NUMBERS'
            print '\t|| ORIGINAL : ',phones
            for x in resp["predictions"]:
                place_id = x['place_id']
                url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+place_id+'&key='
                resp_x = self.graceful_request(url).get('result')
                # THIS GUARANTEES THE COUNTRY CODE TO START WITH +
                international_number = self.parser(extract(resp_x.get('international_phone_number')))
                print '\t||   > NEW : ',international_number
                for phone in phones:
                    if self.parser(phone) == international_number:
                        print '\t|| PHONE NUMBERS MATCHED'
                        print '\t-->','  ',x["description"]
                        return True, place_id

            print '\t|| NO PHONE MATCHED'
            return False,''
        else:
            return False,''

    def update_json_object(self, place_id):
        url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+place_id+'&key='
        resp_x = self.graceful_request(url).get('result')
        self.json_objects[place_id]=resp_x

    def main(self, rows_data):
        self.rows = rows_data

        self._autoComplete()
        self._updateAddress()


        # Dictionary self.json_objects is large
        # This should be released before the next file is opened as the current object won't go out of scope.
        # So _releaseMemory() should be the last function to run. Place other functions before this.
        self._releaseMemory()

    def _autoComplete(self):
        fixed_count = 0
        multiple_matched_count = 0
        none_matched_count = 0
        no_prediction_count = 0
        no_data_count = 0

        print '\nRUNNING AUTOCOMPLETE'
        state = self.get_state(self.rows[0]['City'])
        print 'STATE : ',state
        row_idx=2

        for row in self.rows:
            valid = True
            address = ''

            if (row['Locality'] == ''):
                valid = False
                no_data_count += 1
                print row_idx,'\t',self.autocomplete_flag[3]
            else:
                address = row['Name'] + ', ' + row['Locality']

            if valid:
                url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='
                resp = self.graceful_request(url)

                correct_prediction = ''
                if len(resp["predictions"]) > 0:
                    print row_idx,
                    found = False
                    multiple_match = False
                    for x in resp["predictions"]:
                        print '\t-->','  ',x["description"]
                        for term in x["terms"]:
                            if term['value'].strip().lower() == state.strip().lower():
                                if not found:
                                    correct_prediction = x
                                    found = True
                                else:
                                    multiple_match = True

                    print '\tRES: ',
                    if multiple_match == True:
                        address = row['Name'] + ', ' + row['Locality'] + row['City']
                        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='
                        resp = self.graceful_request(url)

                        if len(resp["predictions"]) == 1:
                            correct_prediction = resp["predictions"][0]
                            multiple_match = False

                    if found and not multiple_match:
                        fixed_count += 1
                        print self.autocomplete_flag[0]
                        place_id = correct_prediction['place_id']
                        row['place_id'] = place_id
                        self.update_json_object(place_id)

                    elif multiple_match:
                        multiple_matched_count += 1
                        print self.autocomplete_flag[1]

                    else:
                        none_matched_count += 1
                        print self.autocomplete_flag[2]
                else:
                    flag = False
                    place_id = ''

                    print row_idx,
                    address = row['Name'] + ', ' + row['Pincode']
                    flag, place_id =  self.no_prediction_cases(row,address)
                    if flag == False:
                        address = row['Name'] + ', ' + row['City']
                        flag, place_id =  self.no_prediction_cases(row,address)

                    if flag == False:
                        no_prediction_count += 1
                        print '\t',self.autocomplete_flag[4]
                    else:
                        print '\tRES: ',
                        fixed_count += 1
                        print self.autocomplete_flag[0]
                        row['place_id'] = place_id
                        self.update_json_object(place_id)

            row_idx += 1
        print '####################'
        print 'FIXED      : ',fixed_count
        print 'MULT-MATCH : ',multiple_matched_count
        print 'NO-MATCH   : ',none_matched_count
        print 'NO-PRED    : ',no_prediction_count
        print 'NO-DATA    : ',no_data_count
        print '####################\n'

    def _updateAddress(self):
        print 'UPDAING ADDRESS'
        row_idx = 2
        for row in self.rows:
            if row['place_id'] is not None and row['place_id'] != '':
                resp = self.json_objects[row['place_id']]
                row['autocomplete_precise_address'] = resp['formatted_address']
                print 'ADDRESS UPDATED FOR ROW : ',row_idx
            row_idx += 1
        print '\n'

    def _releaseMemory(self):
        self.json_objects.clear()
