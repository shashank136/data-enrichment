import requests

KEYS = [
        'AIzaSyB-o_BigZi-jvjKqNXiyyTb8GKBriiI06c', #Rohit
        'AIzaSyCgs8C71RqvWoeO69XBXVPQH006i7v4IkM', #Ananth's
        'AIzaSyCcijQW6eCvvt1ToSkjaGA4R22qBdZ0XsI', #Aakash's
        'AIzaSyA-sGk-2Qg_yQAoJtQ1YUPKEYPCQ5scf5A', #Shubhankar's
        'AIzaSyBVmpXHCROnVWDWQKSqZwgnGFyRAilvIc4',  #Shashwat's
        'AIzaSyAD58vGvx1OdgRq-XdYFZW8cyKhODkg6lc',   #Sisodia
        'AIzaSyDs9N58rJ1n-C7qQ0B1qnhAP8DSzzLd1sU',    #Singh
        'AIzaSyC5-mD5yfBlyy1K7H_HKhCk-05d9kF02_k',  #Akarsh
        'AIzaSyCq7QLuMkfcm-68JL95Au5x9Vc_0qCp8iU'   #Shardul
]

class GMAP_ID:
    def __init__(self):
        self.GOOGLE_API_KEYS = KEYS
        self.key_index=0
        self.required_fields = ['Name', 'City', 'State']

    def graceful_request(self,url):
        chain_count = 0
        while True:
            resp = requests.get(url+self.GOOGLE_API_KEYS[self.key_index]).json()
            if resp['status'] == 'OK':
                return (201, resp)
            elif resp['status'] == 'ZERO_RESULTS':
                return (205, None)
            elif resp['status'] == 'NOT_FOUND':
                return (205, None)
            self.key_index = (self.key_index+1)%len(self.GOOGLE_API_KEYS)
            chain_count += 1
            if chain_count == len(self.GOOGLE_API_KEYS):
                return (500, None)

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
            if row.get('Phone'+str(i)):
                phones.append(self.number_parser(row['Phone'+str(i)]))
        if row.get('Website'):
            websites.append(row['Website'].strip())
        if row.get('Website2'):
            websites.append(row['Website2'].strip())

        url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input='+address+'&types=establishment&location=0,0&radius=20000000&components=country:IN&key='
        i_code, resp = self.graceful_request(url)
        if i_code == 500:
            return (501, False, '')
        elif resp is None:
            return (i_code, False, '')

        if len(resp["predictions"]) == 1 and allow_single:
            return (i_code, True, resp["predictions"][0])

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
                    return (i_code, True, correct_prediction)

            # PHONE VERIFICATION
            for x in resp["predictions"]:
                resp_x = temp_json.get(x['place_id'])
                if resp_x is None:
                    url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+x['place_id']+'&key='
                    i_code, resp_x = self.graceful_request(url)
                    if i_code == 500:
                        return (502, False, '')
                    temp_json[x['place_id']] = resp_x

                # To prevent errors when graceful_request() returns 'None'
                if resp_x is None:
                    break
                resp_x = resp_x.get('result')
                # THIS GUARANTEES THE COUNTRY CODE TO START WITH +
                international_number = self.number_parser(extract(resp_x.get('international_phone_number')))
                for phone in phones:
                    if self.number_parser(phone) == international_number:
                        return (i_code, True, x)

            # WEBSITE VERIFICATION
            for website in websites:
                website = self.website_parser(website)
                found = False
                multiple_match = False
                correct_prediction = ''
                for x in resp["predictions"]:
                    resp_x = temp_json.get(x['place_id'])
                    if resp_x is None:      # SAVES KEY, IN CASE ALREADY FETCHED ABOVE
                        url='https://maps.googleapis.com/maps/api/place/details/json?placeid='+x['place_id']+'&key='
                        i_code, resp_x = self.graceful_request(url)
                        if i_code == 500:
                            return (502, False, '')
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
                    return (i_code, True, correct_prediction)
        return (i_code, False, '')

    def get_id(self, row):
        ###################
        # ROW DATA SANITY CHECK
        for x in self.required_fields:
            if x not in row:
                return self.form_response(401, None)
        ##################

        state = row['State']
        temp_json = dict()
        address = ''
        valid_locality = True       # COMPLETE ADDRESS AVAILABLE
        flag = False                # FATE DECIDING FLAG
        prediction = ''

        if not row.get('Locality'):
            valid_locality = False
        else:
            address = row['Name'] + ', ' + row['Locality']
            # False : Same state results not insured, hence not going for single prediction (For single prediction before state match)
            # True : To ensure same state match
            status_code, flag, prediction = self.analyze_prediction(row,address,state,False,True,temp_json)
            if 500 <= status_code < 600:
                return self.form_response(status_code, None)

        if flag == False:
            if row.get('Pincode'):
                address = row['Name'] + ', ' + row['Pincode']
                # True : Because same state results are insured, hence single prediction can be taken + Added advantage of wrong information in csv being overcomed
                status_code, flag, prediction = self.analyze_prediction(row,address,state,True,True,temp_json)
                if 500 <= status_code < 600:
                    return self.form_response(status_code, None)
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

            if flag == False and row['City']:
                address = row['Name'] + ', ' + row['City']
                # False : If city name is a subset of locality name of any place, it will show in prediction and that may not be in same state. Hence state match is necessary
                # True : Sometimes institute's name is a subset of a large name. For those cases a single prediction with the matching state leads to inaccuracy, given the earlier queries didn't work out. This case needs review, so keeping it True.
                status_code, flag, prediction =  self.analyze_prediction(row,address,state,False,True,temp_json)
                if 500 <= status_code < 600:
                    return self.form_response(status_code, None)

                if flag == False and valid_locality and row.get("Street Address"):
                    address = row["Street Address"] + ' ' + row["Locality"] + ', ' + row["City"]
                    # False : State match is not a guarntee because of high noise in query.
                    # False : Single matching state is not a guaranteed. because of high noise in query
                    status_code, flag, prediction =  self.analyze_prediction(row,address,state,False,False,temp_json)
                    if 500 <= status_code < 600:
                        return self.form_response(status_code, None)

        if flag == True:
            return self.form_response(201, prediction['place_id'])
        else:
            return self.form_response(205, None)

    def get_id_details(self, place_id):
        if place_id:
            url = 'https://maps.googleapis.com/maps/api/place/details/json?placeid='+place_id+'&key='
            i_code, resp = self.graceful_request(url)
            if i_code == 201:
                return self.form_details_response(201, resp['result'])
            elif i_code == 500:
                return self.form_details_response(502, None)
            else:
                return self.form_details_response(i_code, None)
        else:
            return self.form_details_response(401, None)

    def form_details_response(self, status_code, place_details):
        return {'status_code':status_code,
                'place_details':place_details
                }

    def form_response(self, status_code, place_id):
        return {'status_code':status_code,
                'place_id':place_id
                }
