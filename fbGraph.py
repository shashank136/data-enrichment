# -*- coding: utf-8 -*-
from facepy import GraphAPI
import logging
import sys


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

    def searchPlace(self,row):
        name,city,pin=row['Name'],row['City'].lower(),row['Pincode']
        city=unicode(city.lower())
        search_result=self.graph.get("search?q=%s&fields=location&type=place&limit=50"%(name))
        probable = None
        for place in search_result['data']:
            if not 'location' in place:
                continue
            if 'zip' in place['location'] :
                if unicode(pin) == unicode(place['location']['zip'])  and unicode(pin):
                    return self.graph.get(place['id']+"?fields=location,is_verified,description,phone,link,cover,website,emails")
            if 'city' in place['location'] :
                if city == unicode(place['location']['city'].lower()) and not probable:
                    probable = place['id']            
        if probable:
            return self.graph.get(probable+"?fields=location,description,is_verified,phone,link,cover,website,emails")
        return dict()
                            
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
        print "New Info Added from Facebook\n%s:%d"%(stat)
    
    def processAll(self,rows):
        details,link,cover,website,pincode,street,dp,verified,phone,email=0,0,0,0,0,0,0,0,0,0 #stats
        total = len(rows)
        print("Fetching info from FB Graph")
        for progress,row in enumerate(rows):
            try:
                node = self.searchPlace(row)
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
        print "\nNew Info Added from Facebook\nDetails:%d Facebook Link:%d Cover:%d \nWebsite:%d Pincode:%d Address:%d Images:%d Verified %d/%d Phone:%d Emails:%d"%(details,link,cover,website,pincode,street,dp,verified,link,phone,email)


