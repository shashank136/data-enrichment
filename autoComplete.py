import requests
import csv
import sys
import glob

class AutoComplete():
    def __init__(self, key):
        self.key = key
        self.autocomplete_flag = ['FIXED', 'MULTIPLE MATCHED', 'NONE MATCHED', 'NO INPUT DATA', 'NO PREDICTION']

        self.state_data_rows = []
        file_name = glob.glob('./state_data/city_state.csv')
        state_file = open(file_name[0],'r')
        state_reader = csv.DictReader(state_file, dialect=csv.excel)
        self.state_data_rows.extend(state_reader)
        state_file.close()

        self.rows = []

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
        resp = requests.get(url).json()
        while True:
            if resp['status'] == 'OK':
                break
            if resp['status'] == 'ZERO_RESULTS':
                break
            resp = requests.get(url)
            print 'ERROR - RESENDING REQUEST'
        return resp

    def main(self, rows_data):
        self.rows = rows_data

        self._autoComplete()
        self._updateAddress()
        #sys.exit()

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
                #address = row['Name'] + row['Street Address']

            if valid:
                #url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&key='+key
                url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='+self.key
                resp = self.graceful_request(url)

                correct_prediction = ''
                if len(resp["predictions"]) > 0:
                    #print json.dumps(resp,indent=4)
                    #sys.exit()
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

                    print '\t'*5,'RESULT : ',

                    if multiple_match == True:
                        address = row['Name'] + ', ' + row['Locality'] + row['City']
                        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='+self.key
                        resp = self.graceful_request(url)

                        if len(resp["predictions"]) == 1:
                            correct_prediction = resp["predictions"][0]
                            multiple_match = False

                    if found and not multiple_match:
                        fixed_count += 1
                        print self.autocomplete_flag[0]
                        row['place_id'] = correct_prediction['place_id']

                    elif multiple_match:
                        multiple_matched_count += 1
                        print self.autocomplete_flag[1]

                    else:
                        none_matched_count += 1
                        print self.autocomplete_flag[2]
                else:
                    no_prediction_count += 1
                    print row_idx,'\t',self.autocomplete_flag[4]

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
            #print row_idx,'\t',row['place_id']
            if row['place_id'] is not None and row['place_id'] != '':
                url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+row['place_id']+'&key='+self.key
                resp = self.graceful_request(url).get('result')
                row['autocomplete_precise_address'] = resp['formatted_address']
                print 'ADDRESS UPDATED FOR ROW : ',row_idx
            row_idx += 1
        print '\n'
