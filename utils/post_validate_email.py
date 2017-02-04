import dns.resolver
from dns.resolver import NoNameservers,NXDOMAIN, NoAnswer
import socket
import smtplib
from smtplib import SMTPServerDisconnected
import logging
import threading
import csv, glob
import requests,os,sys
csv.field_size_limit(sys.maxint)

class MailBoxLayer():
    def __init__(self):
        self.mailboxlayer_keys = [
                                'b1a65e65dff1e93fb5f9283820fbba4a',
                                '1955555c2c300784c2cc21274d0551d2','eabdeed7f1b28191840584118c3f1c07',
                                '0ebe9383b47d0027e5959918694f09a4','f578821fb823568f551675e8e6066a0c',
                                'c2d5df125595605fc33c17acfad677a2','0dbf3f0ad9e3a5aa631fc18c84619067',
                                '7b7ea008ae52906aea30d641c68a9ac0','c93a76c7df906b57d2d215acbad4f7f3',
                                'b0c7ca3ff27a9a78c85ae3790c7df9fc','afe24335c8e116ec0cacca27deaf3262',
                                'afe24335c8e116ec0cacca27deaf3262','ddeaa4d54802ae4503566c57b04ff130',
                                '06caf934d5ee4cd4e7aed6aae0df2f2c','5b853d821972f8a2bdded92a851f65a7',
                                '4513a044ade0beb9bd636cca2bde959f','082d30e5cac0ecddcf883339e3a75fd6',
                                'ae4237d313d6670983d30eae5f64ce6e','44671ea7b3211a6df6237bc4cb6e97b6',
                                'd0fe2340309f18e82099803a07c5c1d1','8d2cee1d996bcc8655f84a5142cf2c05',
                                '888b6ceb21edb3ab6a0977b8d4ab7fcc'
                                ]
        self.mailboxlayer_key_index = 0

    def mailbox_request(self,email):
        if not email:
            return None
        while True:
            url = "https://apilayer.net/api/check?access_key="+self.mailboxlayer_keys[self.mailboxlayer_key_index]+"&email="+email
            resp = requests.get(url).json()
            if 'error' not in resp:
                return resp['smtp_check']
            if resp['error']['code'] in [101,104] :
                self.mailboxlayer_key_index = (self.mailboxlayer_key_index+1)%len(self.mailboxlayer_keys)
                print '\tCHANGING KEY'
                print '\tNEW KEY : ',self.mailboxlayer_keys[self.mailboxlayer_key_index]
            else:
                print '\t## ERROR :',resp['error']['info']
                return None

class emailFilter(threading.Thread):
    def __init__(self,ThreadID,rows,start,end):
        threading.Thread.__init__(self)
        self.rows=rows[start:end]
        self.id=ThreadID
        self.rejected=[]
        self.accepted=[]

    def validate_email(self,email):
        try:
            records = dns.resolver.query(email[email.find('@')+1:], 'MX')
            mxRecord = records[0].exchange
            mxRecord = str(mxRecord)
            host = socket.gethostname()
            socket.setdefaulttimeout(120)
            server = smtplib.SMTP()
            server.set_debuglevel(0)
            server.connect(mxRecord)
            server.helo(host)
            server.mail('me%s@domain.com'%(self.id))
            code, message = server.rcpt(str(email))
            server.quit()
            if code == 250:
                self.accepted.append(email)
                return True
            self.rejected.append(email)
            return False
        except (NoNameservers,NXDOMAIN, NoAnswer) as e:
            self.rejected.append(email)
            return False
        # MAJOR CAUSE : SMTPServerDisconnected
        except:
            temp_obj = MailBoxLayer()
            if temp_obj.mailbox_request(email):
                self.accepted.append(email)
                return True
            self.rejected.append(email)
            return False

    def run(self):
        for i in self.rows:
            if i['claim_email'] and not self.validate_email(i['claim_email']):
                i['claim_email']=""
                i['listing_email']=""
            if i['Mail2'] and not self.validate_email(i['Mail2']):
                i['Mail2']=""
            if not i['claim_email']:
                i['claim_email'],i['listing_email'],i['Mail2'] = i['Mail2'],i['Mail2'],""

    def getRejected(self):
            return self.rejected
    def getAccepted(self):
            return self.accepted

class Manager:
    def __init__(self):
        self.processed_files = set()
        if os.path.exists('mail_session.dat'):
            with open('mail_session.dat','rb') as data_file:
                self.processed_files = set(data_file.read().splitlines())

    def read_csv(self,file_path,fields,rows):
        with open(file_path, 'rb') as csvFile:
            reader = csv.DictReader(csvFile, dialect=csv.excel)
            fields.extend(reader.fieldnames)
            rows.extend(reader)
        print '  ## FILE READ'

    def write_csv(self,file_path,fields,rows):
        with open(file_path, 'wb') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=fields)
            writer.writerow(dict(zip(fields,fields)))
            for row in rows:
                writer.writerow(row)
        print '  ## FILE WRITTEN'

        with open('mail_session.dat','ab') as data_file:
            self.processed_files.add(os.path.basename(file_path))
            data_file.write(os.path.basename(file_path)+'\n')

    def filterMails(self,rows,max_threads=100):
        print '  ## PROCESSING'
        threads=[]
        rejected=[]
        accepted=[]
        chunk= max(len(rows)//max_threads,1)
        for i in range(0,len(rows),chunk):
            try:
                t=emailFilter(i//chunk+1,rows, i, i+chunk)
                threads.append(t)
                t.start()
            except:
                logging.exception("\tfailed to start thread id %d"%(i))
        print("\tTotal %d threads are running"%len(threads))

        for t in threads:
            t.join()
            rejected+=t.getRejected()
            accepted+=t.getAccepted()
        print("\tTotal Rejected: %s Total Accepted: %s"%(len(rejected),len(accepted)))

    def main(self):
        files = glob.glob("../output/updated_*.csv")
        for file_path in files:
            print '\n',file_path
            if os.path.basename(file_path) in self.processed_files:
                print '  ## FILE ALREADY PROCESSED'
                continue
            fields = []
            rows = []
            self.read_csv(file_path,fields,rows)
            self.filterMails(rows)
            self.write_csv(file_path,fields,rows)
