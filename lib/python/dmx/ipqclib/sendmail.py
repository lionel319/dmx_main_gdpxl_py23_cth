#!/usr/bin/env python
""" Sendmail function to send IPQC dashboard to user and recipients
"""
# -*- coding: utf-8 -*
from __future__ import print_function
import os
import getpass
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dmx.ipqclib.settings import _DOMAIN, _BCC
from dmx.ipqclib.utils import run_command
from dmx.ipqclib.log import uiError
from dmx.ipqclib.ipqcException import IPQCSendmailException

_COMMASPACE = ', '

def get_user_mail():
    """Get user email"""
    user_id = getpass.getuser()
    (code, out) = run_command("finger {} | head -n 1 | awk -F'Name: ' '{{print $2}}'" \
            .format(user_id))

    if code != 0:
        uiError(out)

    sender = out.strip() + _DOMAIN
    return sender

def get_recipients_mail(recipients, to_mail):
    """Get recipients email"""
    with open(recipients, 'r') as f_recipients:
        for line in f_recipients:
            email = line.split()
            if email != []:
                to_mail.append(email[0])

    return to_mail

def sendmail(filepath, ip_name, ipqc=None, recipients=None, mode=""):
    """ Sendmail function to send IPQC dashboard to user and recipients
    """
    ### Process From (me), To (to) lists
    sender = get_user_mail()
    to_mail = [sender]

    ### Process recipients list
    if recipients != None:
        to_mail = get_recipients_mail(recipients, to_mail)

    file_extension = os.path.splitext(filepath)[1]

    ###########################
    # HTML format report
    ###########################
    if 'html' in file_extension:

        if (ipqc != None) and not ipqc.bom in ip_name:
            ipconfig = ip_name+'@'+ipqc.bom
            # Create the body of the message (a plain-text and an HTML version).
#            if (ipqc.report_nfs != None):
#                filepath = os.path.realpath(ipqc.report_nfs)
#            else:
#                filepath = os.path.realpath(ipqc.ip.report_nfs)
        else:
            ipconfig = ip_name

        try:
            # Create message container - the correct MIME type is multipart/alternative.
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "IPQC Report - " + mode + " - "+os.getenv("DB_DEVICE")+' - '+ipconfig
            msg['From'] = sender
            msg['To'] = _COMMASPACE.join(to_mail)
            msg['Bcc'] = _COMMASPACE.join(_BCC)

            with open(filepath, 'r') as fid:
                html = fid.read()

            # Record the MIME types
            composed = MIMEText(html, 'html')

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message, in this case
            # the HTML message, is best and preferred.
            msg.attach(composed)

            # Send the message via local SMTP server.
            smtp = smtplib.SMTP('localhost')
            # sendmail function takes 3 arguments: sender's address, recipient's address
            # and message to send - here it is sent as one string.

            to_mail = to_mail + _BCC
            smtp.sendmail(sender, to_mail, msg.as_string())
            smtp.quit()
        except Exception as err:
            raise IPQCSendmailException(err)

        return
