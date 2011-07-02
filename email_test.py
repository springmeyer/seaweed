import smtplib
from email.mime.text import MIMEText

gmail_acct = 'username@gmail.com'
to_addr = gmail_acct
password = 'password'

def email(use_gmail=True):
    msg = MIMEText('test')
    msg['Subject'] = 'test'
    msg['From'] = gmail_acct
    msg['To'] = to_addr
    s = smtplib.SMTP()
    s.set_debuglevel(0)
    if use_gmail:
        s.connect('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(gmail_acct, password)
    else:
        s.connect(host='localhost',port=587)
    # sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[])
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.close()

if __name__ == "__main__":
    email()