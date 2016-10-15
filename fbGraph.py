# -*- coding: utf-8 -*-
from facepy import GraphAPI
import logging
import sys
import glob,csv


KEYS_FB=['1040517959329660|c7e458dd968fca33d05a18fddbcd86ab',   #Rohit
         '1697721727215546|a372f9c8b412e8b053094042fc4b42e6',   #Shantanu
          ]# format is AppID|AppSecret, API version: 2.7

key_index = 0

def UTF8(data):
    try:
        return data.encode('utf-8','ignore')
    except:
        return data

class processGraph:
    def __init__(self, key=None):
        global key_index
        """
    >>> Graph = processGraph()
    You May Initialise Facebook GraphAPI with your own AppID and AppSecret
    >>> Graph = processGraph("<<App_ID>>|<<App_Secret>>")
    """
        if not key:
            while True:
                self.graph = GraphAPI(KEYS_FB[key_index])
                try:
                    self.graph.search("test","place")
                    break
                except:
                    key_index= (key_index+1)%len(KEYS_FB)
        else:
            self.graph = GraphAPI(key)

        # FOR STATE DATA TO BE USED BY Graph API
        self.state_data_rows = []
        file_name = glob.glob('./state_data/city_state.csv')
        state_file = open(file_name[0],'r')
        state_reader = csv.DictReader(state_file, dialect=csv.excel)
        self.state_data_rows.extend(state_reader)
        state_file.close()

    def get_state(self,city):
        state = ''
        found = False

        for row in self.state_data_rows:
            if row['Name of City'].strip().lower() == city.strip().lower():
                state = row['State']
                found = True
                break
        if not found:
            print('NO STATE MATCH FOR CITY');
            sys.exit()
        else:
            return state

    def number_parser(self,x):
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

        if x.find('+91') == 0 or x.find('91 ') == 0:
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

    def match_website(self,website,resp):
        if website == self.website_parser(resp):
            return True
        return False

    def match_phone_nos(self,phones,resp):
        # DECREASING SEPARATOR PRIORITY ORDER
        separators = [',', '/', ';', '&']

        resp_nos = []
        sep_found = False
        for separator in separators:
            if resp.find(separator) != -1:
                resp_nos.extend(resp.split(separator))
                sep_found = True
                break
        if not sep_found:
            resp_nos.append(resp)

        for i in range(len(resp_nos)):
            resp_nos[i] = resp_nos[i].encode('ascii',errors='ignore')

        for x in resp_nos:
            if self.number_parser(x) in phones:
                return True
        return False

    def analyze_prediction(self,row,query,allow_website_match):

        pin= row['Pincode']
        phones = []
        website = ''
        email = ''

        for i in range(1,6):
            if row['Phone'+str(i)]:
                phones.append(self.number_parser(row['Phone'+str(i)]))
        if row['Website']:
            website = self.website_parser(row['Website'])
        if row['Mail']:
            email = row['Mail'].strip()

        search_result=self.graph.get("search?q=%s&fields=location,phone,emails,website&type=place&limit=50"%(query))
        for place in search_result['data']:
            if 'location' in place:
                if 'zip' in place['location'] :
                    if unicode(pin) == unicode(place['location']['zip']) and unicode(pin):
                        node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                        return node

            if 'phone' in place and phones:
                if self.match_phone_nos(phones,place['phone']):
                    node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                    return node

            if 'emails' in place and email:
                for x in place['emails']:
                    if x == email:
                        node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                        return node

        # WEBSITE MATCH IS NOT SAFE. HENCE SHOULD BE DONE ONLY IF ABOVE MEASURES FAILS.
        if allow_website_match:
            match=False
            multiple_match=False
            correct_place_id=''

            for place in search_result['data']:
                if 'website' in place and website:
                    if self.match_website(website,place['website']):
                        if not match:
                            correct_place_id=place['id']
                            match=True
                        else:
                            multiple_match=True
                            break

            if match and not multiple_match:
                node = self.graph.get(correct_place_id+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                return node

        return dict()

    def searchPlace(self,row,state):
        query = row['Name']
        node = self.analyze_prediction(row,query,False)

        if not node and row['Locality']:
            query = row['Name'] + ', ' + row['Locality']
            node=self.analyze_prediction(row,query,True)

        if not node:
            query = row['Name'] + ', ' + state
            node=self.analyze_prediction(row,query,True)

        return node

    def _repairDetails(self,row,node):
        if 'description' in node and not row['Details']:
            row['Details'] = node['description']
            #print "Added description "+node['description'][:40]+" to "+row["Name"]+" from facebook"
            return 1
        return 0

    def _repairWebsite(self,row,node):
        if not row['Website']:
            if 'website' in node:
                row['Website'] = node['website']
                #print "Added website "+node['website']+" to "+row["Name"]+" from facebook"
                return 1
        return 0

    def _repairPin(self,row,node):
        if 'location' in node:
            if not row['Pincode'] and 'zip' in node['location'] :
                row['Pincode'] = node['location']['zip']
                #print "Added pin "+node['location']['zip']+" to "+row["Name"]+" from facebook"
                return 1
        return 0

    def _repairStreet(self,row,node):
        if 'location' in node:
            if not row['Street Address'] and 'street' in node['location']:
                row['Street Address'] = node['location']['street']
                #print "Added address "+node['location']['street']+" to "+row["Name"]+" from facebook"
                return 1
        return 0

    def _addPage(self,row,node):
        if 'link' in node:
            row['fb_page']= node['link']
            #print "Added page "+node['link']+" to "+row["Name"]+" from facebook"
            return 1
        return 0

    def _isVerified(self,row,node):
        if 'is_verified' in node:
            if node['is_verified']:
                row['fb_verified']= 'True'
                return 1
            row['fb_verified']= 'False'
        return 0

    def _addCover(self,row,node):
            if 'cover' in node:
                row['Images URL'] = node['cover']['source']+","+row['Images URL']
                #print "Added cover "+node['cover']['source']+" to "+row["Name"]+" from facebook"
                return 1
            return 0
    def _addEmails(self,row,node):
##        if row['Mail'] and not validate_email(row['Mail']):
##            print "Invalid mail removed:"+row['Mail']
##            row['Mail'] = ""
        check = 0
        if 'emails' in node:
            for i in node['emails']:
##                if validate_email(i):
                    if row['Mail'] and i.strip() not in row['Mail'].strip():
                        row['Mail2'] = i
                        return check+1
                    row['Mail'] = i
                    check = 1
##                else:
##                    print "Invalid mail not considered:"+i

        return check
    def _addPhone(self,row,node):
        if 'phone' in node:
            ph = map(UTF8,node['phone'].split(','))
            for i in range(1,6):
                if not row['Phone'+str(i)]:
                    break
            for j,p in zip(range(i+1,6),ph):
                row['Phone'+str(j)] = p.strip()
                #print "Added phone "+p.strip()+" in "+'Phone'+str(j)+" from facebook"+str(node['location'])
            return 1
        return 0



    def _addPicture(self,row,node):
        if not 'id' in node:
            return 0
        profile_pic=self.graph.get(node['id']+"/picture?height=500&width=500&redirect")
        if 'data' in profile_pic:
            if 'url' in profile_pic['data'] and 'is_silhouette' in profile_pic['data']:
                if not profile_pic['data']['is_silhouette']:
                    row['Images URL'] += profile_pic['data']['url']+","
                    return 1
        return 0
    def processSelective(self,rows,selection):
        """
    Available Selections are:
                _repairDetails
                _repairWebsite
                _repairPin
                _repairStreet
                _addPage
                _addCover
                _addPicture
                _addPhone
                _addEmail
        e.g.
        >>> Graph = processGraph()
        >>> Graph.processSelective(CSV_Dictionary,'_repairDetails')
        """
        stat=0
        if selection in dir(self):
            method = getattr(self,selection)
        for row in rows:
            try:
                node = self.searchPlace(row)
                stat+=method(row,node)
            except:
                logging.exception("Error loading %s from facebook for %s"%(selection,row['Name']))
        print("New Info Added from Facebook\n%s:%d"%(stat));

    def processAll(self,rows):
        details,link,cover,website,pincode,street,dp,verified,phone,email=0,0,0,0,0,0,0,0,0,0 #stats
        total = len(rows)
        state = self.get_state(rows[0]['City'])
        print('STATE : ',state);
        print("Fetching info from FB Graph")
        for progress,row in enumerate(rows):
            try:
                node = self.searchPlace(row,state)
                details += self._repairDetails(row,node)
                website += self._repairWebsite(row,node)
                pincode += self._repairPin(row,node)
                street += self._repairStreet(row,node)
                link += self._addPage(row,node)
                cover += self._addCover(row,node)
                dp += self._addPicture(row,node)
                phone += self._addPhone(row,node)
                email += self._addEmails(row,node)
                verified += self._isVerified(row,node)
                pro=int((float(progress)/total)*100)
                sys.stdout.write("\r%d%%"%pro)
                sys.stdout.flush()
            except:
               logging.exception("Error loading information from facebook for " + row['Name'])
        sys.stdout.write("\r100%")
        sys.stdout.flush()
        print("\nNew Info Added from Facebook\nDetails:%d Facebook Link:%d Cover:%d \nWebsite:%d Pincode:%d Address:%d Images:%d Verified %d/%d Phone:%d Emails:%d"%(details,link,cover,website,pincode,street,dp,verified,link,phone,email));
