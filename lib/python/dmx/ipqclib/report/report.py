from dmx.ipqclib.report.html.report_ip import ReportHTML
from dmx.ipqclib.report.json.report import ReportJSON
from dmx.ipqclib.backup import trace
from dmx.ipqclib.sendmail import sendmail
from dmx.ipqclib.log import uiInfo, uiDebug
from dmx.ipqclib.settings import _VIEW

class Report():

    def __init__(self, ip_name, report_format, ipqc=None, msg=None, report_template=_VIEW, filter_status=[]):

        self._ipqc = ipqc

        uiDebug("DEBUG >> Generates report  {} {}" .format(ip_name, report_format))

        if report_format == 'html':
            self._report = ReportHTML(ip_name, ipqc=ipqc, msg=msg, report_template=report_template, filter_status=filter_status)
        
        if report_format == "json":
            self._report =  ReportJSON(ip_name, ipqc=ipqc)


        if (ipqc != None) and (ipqc.top == True) and (ipqc.cache == False):
            uiDebug(">>> report/report.py - backup ipqc data")
            self._report.filename = trace(ipqc, report_format, report_template=report_template)
           

    def mail(self, ip_name, recipients=None, mode=""):
        sendmail(self._report.filename, ip_name, ipqc=self._ipqc, recipients=recipients, mode=mode)

    @property
    def report(self):
        return self._report
