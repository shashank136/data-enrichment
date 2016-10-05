import requests
import json
from fbGraph import UTF8
import sys

keys = [ ("AC086728331b2e303cda499de8e36e3ba2","2fd8e3dcad09495f4b68ba20eef63344"),
        ]
key_index=0

class processMobile:
    def __init__(self,key=None):        
        self.key = keys[key_index]
        self.url = "https://lookups.twilio.com/v1/PhoneNumbers/%s"

    def _request(self,phone_no):
        global key_index
        start = key_index
        for i in range(len(keys)):
            try:
                return json.loads(requests.get(self.url%phone_no,auth=self.key).text)
            except:
                key_index = (key_index + 1) % len(keys)
                print("Switching to new key"+str(key_index))
                if start!=key_index:
                    key = keys[key_index]
                else:
                    break
        print "None of the keys worked!"
        return { 'national_format': "xx xx xx", 'phone_number': phone_no}

    def _isMobile(self,phone_no):
        result = self._request(phone_no)
        try:
            return result['national_format'].count(' ') == 1, result['phone_number']
        except:
            return False, phone_no
    
    def _addCountryCode(self,phone_no):
        if phone_no.startswith('0'):
            phone_no = phone_no[1:]
        if not phone_no.startswith('91') and not phone_no.startswith('+91'):
            return '+91-'+phone_no
        return phone_no

    def processAll(self,rows):
        total=len(rows)
        for progress,row in enumerate(rows):
            mobiles=[]
            for i in range(1,6):
                n = row["Phone"+str(i)]
                if not n:
                    continue
                isMob,cleaned_no = self._isMobile(self._addCountryCode(UTF8(n)))
                if isMob:
                    mobiles.append(cleaned_no)
            pro=int((float(progress)/total)*100)
            sys.stdout.write("\r%d%%"%pro)
            sys.stdout.flush()
            row['Mobiles'] = ','.join(mobiles)
            #print(row['Mobiles'])
            

