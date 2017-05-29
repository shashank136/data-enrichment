import requests
import json
from fbGraph import safe_dec_enc
import sys
import re


keys = [ ("AC086728331b2e303cda499de8e36e3ba2","2fd8e3dcad09495f4b68ba20eef63344"),
        ]
key_index=0


class processMobileSTDcode:

    def processSTD(self,city,n):

        telephone = n
        ph_len = len(telephone.replace('-',''))
        # print("length of telephone number is: "+str(ph_len))

        readfile = open('std_data.csv',"r")
        filereader = csv.reader(readfile)

        if ph_len < 9:
            city = ro['City']

            for row in filereader:
                for field in row:
                    if field == city.upper():
                        stdno = eval(row[2])
                        # print(stdno)
                        # print(len(str(stdno)))
                        x=len(str(stdno))
                        if x==2:
                            std_str = '%0*d' % (3,stdno)
                        elif x==3:
                            std_str = '%0*d' % (4,stdno)
                        else:
                            std_str = '%0*d' % (5,stdno)
                        print(std_str)
                        # print(len(std_str))
                    
                        new_tele = std_str + telephone.replace('-','')
                        # print(new_tele)

                        if len(new_tele) == 11:
                            telephone = new_tele
                            return telephone
                            # print('telephone no: '+telephone)
                        else:
                            telephone = 'NA'
                            return telephone
                            # print('telephone no: '+telephone)

        readfile.close()

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
        phone_no=filter(lambda x: not x.isalpha(),str(phone_no))
        result = self._request(phone_no)
        try:
            #print phone_no
            return result['national_format'].count(' ') == 1, result['phone_number']
        except:
            print "Bad Phone number "+str(phone_no)
            return False, phone_no

    def _addCountryCode(self,phone_no):
        phone_no=phone_no.replace(' ','').replace('(','').replace(')','')
        if '0091' in phone_no[0:len(phone_no)/2+1]:
            phone_no=phone_no.replace('0091','')
        elif '091' in phone_no[0:len(phone_no)/2+1]:
            phone_no=phone_no.replace('091','')
        if phone_no.startswith('0'):
            phone_no = phone_no[1:]
        if not phone_no.startswith('91') and not phone_no.startswith('+91'):
            return '+91-'+phone_no
        return phone_no

    def checkNo(self,rows):
        for row in rows:
            noslist=[]
            noslist1=[]
            phn_no_ls=''
            for i in range(1,6):
                nphn=''
                if row['Phone'+str(i)] is not None:
                    y=(filter(lambda x: not x.isalpha(),safe_dec_enc(row['Phone'+str(i)])).strip().replace(' ',''))
                    noslist1.append(y)
                    row['Phone'+str(i)]=None
                    # nphn=row['Phone'+str(i)].replace(' ','').replace('(','').replace(')','').replace('-','')
                    # if len(nphn)>=20:
                    #     phn_no_ls+=
                    # phn_no_ls+=row['Phone'+str(i)]+','

            noslist1=filter(None,noslist1);
            noslist1=list(set(noslist1))
            #print 'noslist1',noslist1
            for i in range(len(noslist1)):
                # row['Phone'+str((i+1))]=noslist1[i]
                phn_no_ls+=noslist1[i]+','
            phn_no_ls=phn_no_ls.split(',')
            phn_no_ls=filter(None,phn_no_ls)

            #phn_no_ls=map(str,phn_no_ls)

            for i in range(len(phn_no_ls)):
                if len(phn_no_ls[i])>=20:
                    n=1
                    if len(phn_no_ls[i])%2==0:
                        n=0
                    #print 'phn no',phn_no_ls[i]
                    splt_no=phn_no_ls[i][0:-len(phn_no_ls[i])/2+n]+'/'+phn_no_ls[i][-len(phn_no_ls[i])/2+n:]
                    phn_no_ls[i]=splt_no
                    #print 'splt_no',splt_no
            for no in phn_no_ls:
                if '/' not in no:
                    noslist.append(no)
                elif '/' in no:
                    splt_list=no.split('/')
                    for i in range(1,len(splt_list)):
                        if len(splt_list[i])>=10:
                            continue
                        splt_list[i]=splt_list[0][0:-len(splt_list[i])]+splt_list[i]
                    noslist=noslist+splt_list
            noslist=set(noslist)
            noslist=list(noslist)


            # print noslist
            p_col=0
            for i in range(0,len(noslist)):
                phn_no=''
                if i==5:
                    break;
                else:
                    phn_no=self._addCountryCode(noslist[i])
                    try:
                        result=self._request(phn_no)
                        y=result['phone_number']
                        if '+91' in noslist[i][:len(noslist[i])/2]:
                            noslist[i]=noslist[i].replace('+91','0')
                        row['Phone'+str(p_col+1)]=noslist[i]
                        p_col+=1
                    except:
                        print "Bad Phone number "+safe_dec_enc(noslist[i])+" Deleted..."
                    

    def processAll(self,rows):
        self.checkNo(rows)
        total=len(rows)
        #value = False

        try:

            for progress,row in enumerate(rows):
                mobiles=[]
                for i in range(1,6):
                    n = safe_dec_enc(row["Phone"+str(i)])
                    if not n:
                        continue

                    if len(n)<9:
                        city = safe_dec_enc(row["City"])
                        n = processMobileSTDcode.processSTD(city,n)

                    isMob,cleaned_no = self._isMobile(self._addCountryCode(n))
                    if isMob:
                        cleaned_no= cleaned_no.replace('+91','')
                        if cleaned_no[0:2]=='91':
                            cleaned_no=cleaned_no[2:]
                        
                            
                        mobiles.append(cleaned_no)
    ##            pro=int((float(progress)/total)*100) #Avoiding bad characters in log file
    ##            sys.stdout.write("\r%d%%"%pro)
    ##            sys.stdout.flush()
                row['Mobiles'] = ', '.join(list(set(mobiles)))
                #print(row['Mobiles'])
                value = True
                return value
        except:
            return value        
