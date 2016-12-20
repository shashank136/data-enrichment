# -*- coding: utf-8 -*-
from facepy import GraphAPI
import logging
import sys
import glob,csv,json
from random import randint
import parseFBWorkHours

KEYS_FB=['1812886018965623|a43d798be9fba8e94d3f4f98d0333b62',   #Anon
         '1327435673986191|8bfc29c57479473a77257f75377d88f3',   #Anon
         '1040517959329660|c7e458dd968fca33d05a18fddbcd86ab',   #Rohit
         '1697721727215546|a372f9c8b412e8b053094042fc4b42e6',   #Shantanu
          ]# format is AppID|AppSecret, API version: 2.7

key_index = 0

def UTF8(data):
    try:
        return data.encode('utf-8','ignore')
    except:
        return data

# SAFE DECODING ENCODING
def safe_dec_enc(data,basic=False):
    if data:
        if isinstance(data, unicode):
            if basic:
                return data.encode('ascii','ignore')
            return data.encode('utf-8','ignore')
        else:
            if basic:
                # REMOVE NON-STANDARD UNICODE-POINTS FROM BYTE-STRING
                return data.decode('ascii','ignore').encode('ascii')
            return data.decode('utf-8','ignore').encode('utf-8')
    return ''

class processGraph:
    def __init__(self, key=None):
        global key_index
        self.viewFactor=0
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
        if not x:
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
        websites = []
        emails = []

        for i in range(1,6):
            if row['Phone'+str(i)]:
                phones.append(self.number_parser(row['Phone'+str(i)]))
        if row['Website']:
            websites.append(row['Website'].strip())
        if row['Website2']:
            websites.append(row['Website2'].strip())
        if row['Mail']:
            emails.append(row['Mail'].strip())
        if row['Mail2']:
            emails.append(row['Mail2'].strip())

        search_result=self.graph.get("search?q=%s&fields=location,phone,emails,website&type=place&limit=50"%(query))
        for place in search_result['data']:
            if 'location' in place:
                if 'zip' in place['location'] :
                    if unicode(pin) == unicode(place['location']['zip']) and unicode(pin):
                        node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                        return node

            if 'phone' in place and phones:
                if self.match_phone_nos(phones, safe_dec_enc(place['phone'])):
                    node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                    return node

            for email in emails:
                if 'emails' in place and email:
                    for x in place['emails']:
                        if email == safe_dec_enc(x):
                            node = self.graph.get(place['id']+"?fields=name,location,is_verified,description,phone,link,cover,website,emails")
                            return node

        # WEBSITE MATCH IS NOT SAFE. HENCE SHOULD BE DONE ONLY IF ABOVE MEASURES FAILS.
        if allow_website_match:
            for website in websites:
                website = self.website_parser(website)
                match=False
                multiple_match=False
                correct_place_id=''

                for place in search_result['data']:
                    if 'website' in place and website:
                        if self.match_website(website, safe_dec_enc(place['website'])):
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
        ################
        row['Name'] = safe_dec_enc(row['Name'],True)
        row['Locality'] = safe_dec_enc(row['Locality'],True)
        row['City'] = safe_dec_enc(row['City'],True)
        ################
        self.viewFactor=0
        node = None

        if row['Locality']:
            query = row['Name'] + ', ' + row['Locality']
            node=self.analyze_prediction(row,query,True)
        if not node and row['City']:
            query = row['Name'] + ', ' + row['City']
            node=self.analyze_prediction(row,query,True)
        if not node:
            query = row['Name'] + ', ' + state
            node=self.analyze_prediction(row,query,True)
        if not node:
            query = row['Name']
            node = self.analyze_prediction(row,query,False)
        return node

    def _repairDetails(self,row,node):
        if 'description' in node and not row['Details']:
            row['Details'] = node['description']
            #print "Added description "+node['description'][:40]+" to "+row["Name"]+" from facebook"
            self.viewFactor+=1
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
            self.viewFactor+=1
            return 1
        return 0

    def _isVerified(self,row,node):
        if 'is_verified' in node:
            if node['is_verified']:
                row['fb_verified']= 'True'
                self.viewFactor+=2
                return 1
            row['fb_verified']= 'False'
        return 0

    def _addCover(self,row,node):
            if 'cover' in node:
                row['Images URL'] = node['cover']['source']+","+row['Images URL']
                #print "Added cover "+node['cover']['source']+" to "+row["Name"]+" from facebook"
                self.viewFactor+=1
                return 1
            return 0
    def _addEmails(self,row,node):
        check = 0
        if 'emails' in node:
            for i in node['emails']:
                if row['Mail'] and i.encode('utf-8','ignore').strip() not in row['Mail'].strip():
                    row['Mail2'] = i
                    return check+1
                row['Mail'] = i
                check = 1
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
                    row['Images URL'] = profile_pic['data']['url'] + "," + row['Images URL']
                    self.viewFactor+=2
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

    def _addViews(self,row):
        if row['Total Views']:
            row['Total Views']+=self.viewFactor*randint(100,200)
        else:
            row['Total Views']=self.viewFactor*randint(100,200)

    def _nodePhotos(self,row,node):
        if 'id' not in node:
            return
        photos = []
        after = ''
        while True:
            resp = self.graph.get(node['id']+'/photos?type=uploaded&fields=source&limit=10&after=%s'%after)
            if 'data' in resp:
                for i in resp['data']:
                    photos.append(i['source'])
            if 'paging' in resp:
                after = resp['paging']['cursors']['after']
                if 'next' not in resp['paging']:
                    break
            else:
                break
            # TO GUARANTEE QUICK TERMINATION
            if len(photos) >= 10:
                break

        row_data = ''
        for photo in photos:
            if row_data:
                row_data += ','+ photo
            else:
                row_data = photo
        row['fb_photos'] = row_data

    def _nodeVideos(self,row,node):
        if 'id' not in node:
            return
        videos = []
        after = ''
        while True:
            resp = self.graph.get(node['id']+'/videos?type=uploaded&fields=source,title,description&limit=10&after=%s'%after)
            if 'data' in resp:
                for i in resp['data']:
                    videos.append(i)
            if 'paging' in resp:
                after = resp['paging']['cursors']['after']
                if 'next' not in resp['paging']:
                    break
            else:
                break
            # TO GUARANTEE QUICK TERMINATION
            if len(videos) >= 10:
                break

        row_data = ''
        for video in videos:
            x = ''
            if 'title' in video:
                x = '{"title":"%s","link":"%s"}'%(video['title'].encode('ascii','ignore').replace('"',''),video['source'])
            elif 'description' in video:
                x = '{"title":"%s","link":"%s"}'%(video['description'].encode('ascii','ignore').replace('"',''),video['source'])
            else:
                x = '{"title":"%s","link":"%s"}'%('',video['source'])

            if row_data:
                row_data += ','+ x
            else:
                row_data = x
        row['fb_videos'] = row_data

    def _nodeWorkingHours(self,row,node):
        if 'id' not in node:
            return
        resp = self.graph.get(node['id']+'?fields=hours')
        row_data = ''
        if 'hours' in resp:
            try:
                row_data = parseFBWorkHours.parse(resp['hours'])
            except:
                logging.exception("Error parsing Working Hours for" + row['Name'])

        row['fb_workingHours'] = row_data

    def _nodePosts(self,row,node):
        if 'id' not in node:
            return
        posts = []
        after = ''
        while True:
            resp = self.graph.get(node['id']+'/posts?fields=message,type,created_time&limit=90&next=%s'%after)
            if 'data' in resp:
                for i in resp['data']:
                    if i['type'] == 'status' and 'message' in i:
                        posts.append(i)
            if 'paging' in resp:
                after = resp['paging']['next']
            else:
                break
            # TO GUARANTEE QUICK TERMINATION
            if len(posts) >= 10:
                break

        row_data = ''
        for post in posts:
            x = '{"created_time":"%s","message":"%s"}'%(post['created_time'],post['message'].encode('ascii','ignore').replace('"',''))
            if row_data:
                row_data += ','+ x
            else:
                row_data = x
        row['fb_posts'] = row_data

    def _mergeData(self,row):
        # Merge Photos
        if row['fb_photos']:
            if row['Images URL']:
                row['Images URL'] = row['fb_photos'] + ',' + row['Images URL']
            else:
                row['Images URL'] = row['fb_photos']

        if not row['Working Hours'] and row['fb_workingHours']:
            row['Working Hours'] = row['fb_workingHours']

    def processAll(self,rows,state):
        details,link,cover,website,pincode,street,dp,verified,phone,email=0,0,0,0,0,0,0,0,0,0 #stats
        total = len(rows)
        print("Fetching info from FB Graph")
        print 'STATE : ',state
        for progress,row in enumerate(rows):
            try:
                node = self.searchPlace(row,state)
                details += self._repairDetails(row,node)
                website += self._repairWebsite(row,node)
                pincode += self._repairPin(row,node)
                street += self._repairStreet(row,node)
                link += self._addPage(row,node)
                phone += self._addPhone(row,node)
                email += self._addEmails(row,node)
                verified += self._isVerified(row,node)
                self._addViews(row)

                #self._nodePosts(row,node)
                self._nodeVideos(row,node)
                self._nodePhotos(row,node)
                self._nodeWorkingHours(row,node)

                self._mergeData(row)
                # ENSURES COVER/DP AS THE FIRST PICTURE
                cover += self._addCover(row,node)
                dp += self._addPicture(row,node)

##                pro=int((float(progress)/total)*100) # Comment out to avoid Bad characters in logs
##                sys.stdout.write("\r%d%%"%pro)
##                sys.stdout.flush()
            except:
               logging.exception("Error loading information from facebook for " + row['Name'])
##        sys.stdout.write("\r100%")
##        sys.stdout.flush()
        print("\nNew Info Added from Facebook\nDetails:%d Facebook Link:%d Cover:%d \nWebsite:%d Pincode:%d Address:%d Images:%d Verified %d/%d Phone:%d Emails:%d"%(details,link,cover,website,pincode,street,dp,verified,link,phone,email));
