import dns.resolver
from dns.resolver import NoNameservers,NXDOMAIN, NoAnswer
import socket
import smtplib
from smtplib import SMTPServerDisconnected
import logging
import threading
import csv
class emailFilter(threading.Thread):


        def __init__(self,ThreadID,rows,start,end):
                threading.Thread.__init__(self)
                self.rows=rows[start:end]
                self.id=ThreadID
                self.rejected=[]
                self.accepted=[]
                self.missed=[]

               
        def validate_email(self,email):
                try:
                        records = dns.resolver.query(email[email.find('@')+1:], 'MX')
                        mxRecord = records[0].exchange
                        mxRecord = str(mxRecord)
                        host = socket.gethostname()
                        server = smtplib.SMTP()
                        server.set_debuglevel(0)
                        server.connect(mxRecord)
                        server.helo(host)
                        server.mail('me%s@domain.com'%(self.id))
                        code, message = server.rcpt(str(email))
                        server.quit()
                        if code == 250:
##                                print("%s was accepted in thread %s"%(email,self.id))
                                self.accepted.append(email)
                                return True
##                        print("%s was rejected in thread %s"%(email,self.id))
                        self.rejected.append(email)
                        return False
                except (NoNameservers,NXDOMAIN, NoAnswer) as e:
##                        print("%s was rejected due to domain error in thread %s because %s"%(email,self.id,e))
                        self.rejected.append(email)
                        return False
                except SMTPServerDisconnected as e:
##                        print("%s was deemed accepted in thread %s because server didn't behave as expected(%s)"%(email,self.id,e))
                        self.accepted.append(email)
                        return True
                except:
                        #logging.exception("This error is not a problem, email: %s"%(email))
##                        print("%s was deemed to be accepted in thread %s"%(email,self.id))
                        self.accepted.append(email)
                        self.missed.append(email)
                        return True

        def run(self):
                for i in self.rows:
                        if i['Mail'] and not self.validate_email(i['Mail']):
                                i['Mail']=""
                        if i['Mail2'] and not self.validate_email(i['Mail2']):
                                i['Mail2']=""
                        if not i['Mail']:
                                i['Mail'],i['Mail2']=i['Mail2'],""

        def getRejected(self):
                return self.rejected
        
        def getAccepted(self):
                return self.accepted
        def getMissed(self):
                return self.missed


def filterMails(rows,fname,max_threads=100):
        threads=[]
        rejected=[]
        accepted=[]
        missed=[]
        chunk= max(len(rows)//max_threads,1)
        for i in range(0,len(rows),chunk):
                try:
                        t=emailFilter(i//chunk+1,rows, i, i+chunk)
                        threads.append(t)
                        t.start()
                except:
                       logging.exception("failed to start thread id %d"%(i))
        print("Total %d threads are running"%len(threads))



        for t in threads:
            t.join()
            rejected+=t.getRejected()
            accepted+=t.getAccepted()
            missed+=t.getMissed()

        print("Total Rejected: %s Total Accepted: %s Total Missed: %s"%(len(rejected),len(accepted),len(missed)))
        #open('rejected_from_%s.txt'%fname,'w').write(','.join(rejected))

        with open('email.csv','a') as f:
                fieldnames=['Accepted_mails','Rejected_mails','%s'%fname]
                writer = csv.DictWriter(f,fieldnames=fieldnames,dialect=csv.excel)

                writer.writeheader()

                for accept in accepted:
                    writer.writerow({fieldnames[0]:accept})
                for reject in rejected:
                    writer.writerow({fieldnames[1]:reject})
                ##later on we can specially look into those email ids which did not responded

                f.close()
