import dns.resolver
import socket
import smtplib
def validate_email(email):
        if not 'gmail' in email:
                return True #For now we are not filtering out non gmail addresses
        try:
                records = dns.resolver.query(email[email.find('@')+1:], 'MX')
                mxRecord = records[0].exchange
                mxRecord = str(mxRecord)
                host = socket.gethostname()
                server = smtplib.SMTP()
                server.set_debuglevel(0)
                server.connect(mxRecord)
                server.helo(host)
                server.mail('me@domain.com')
                code, message = server.rcpt(str(email))
                server.quit()
                if code == 250:
                        return True
                return False
        except:
                return True
