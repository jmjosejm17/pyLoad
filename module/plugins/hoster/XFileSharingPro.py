# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from random import random
from urllib import unquote
from urlparse import urlparse
from pycurl import FOLLOWLOCATION
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.ReCaptcha import ReCaptcha
from module.utils import html_unescape

class XFileSharingPro(SimpleHoster):
    """
    Common base for XFileSharingPro hosters like EasybytezCom, CramitIn, FiledinoCom...
    Some hosters may work straight away when added to __pattern__
    However, most of them will NOT work because they are either down or running a customized version
    """
    __name__ = "XFileSharingPro"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*((aieshare|amonshare|asixfiles|azsharing|banashare|batubia|bebasupload|boosterking|buckshare|bulletupload|crocshare|ddlanime|divxme|dopeshare|downupload|eyesfile|eyvx|fik1|file(4safe|4sharing|band|beep|bit|box|dove|fat|forth|made|mak|planet|playgroud|race|rio|strack|upper|velocity)|fooget|4bytez|freefilessharing|glumbouploads|grupload|heftyfile|hipfile|host4desi|hulkshare.com|idupin|imageporter|isharefast|jalurcepat|kingsupload|laoupload|linkzhost|loombo|maknyos|migahost|mlfat4arab|movreel|netuploaded|ok2upload|180upload|1hostclick|ovfile|putshare|pyramidfiles|q4share|queenshare|ravishare|rockdizfile|sendmyway|share(76|beast|hut|run|swift)|sharingonline|6ybh-upload|skipfile|spaadyshare|space4file|speedoshare|upload(baz|boost|c|dot|floor|ic|dville)|uptobox|vidbull|zalaa|zomgupload)\.com|(kupload|movbay|multishare|omegave|toucansharing|uflinq)\.org|(annonhost|fupload|muchshare|supashare|tusfiles|usershare|xuploading)\.net|(banicrazy|flowhot|upbrasil)\.info|(shareyourfilez)|.biz|(bzlink|)\.us|(cloudcache|fileserver)\.cc|(farshare|kingshare)\.to|(filemaze|filehost)\.ws|(goldfile|xfileshare)\.eu|(filestock|moidisk)\.ru|4up\.me|kfiles\.kz|odsiebie\.pl|upchi\.co\.il|upit\.in|verzend\.be)/\w{12}" 
    __version__ = "0.02"
    __description__ = """XFileSharingPro common hoster base"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'
    FILE_OFFLINE_PATTERN = r'<(b|h2)>File Not Found</(b|h2)>'

    WAIT_PATTERN = r'<span id="countdown_str">.*?>(\d+)</span>'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'
    CAPTCHA_URL_PATTERN = r'(http://[^"\']+?/captchas/[^"\']+)'
    RECAPTCHA_URL_PATTERN = r'http://[^"\']+?recaptcha[^"\']+?\?k=([^"\']+)"'
    ERROR_PATTERN = r'class="err">(.*?)<'

    DIRECT_LINK_PATTERN = r'This direct link.*?href=["\'](.*?)["\']'
    
    def setup(self):
        self.HOSTER_NAME = re.search(self.__pattern__, self.pyfile.url).group(1)
        self.multiDL = True 

    def process(self, pyfile):
        self.captcha = self.errmsg = None
        self.passwords = self.getPassword().splitlines()

        if not re.match(self.__pattern__, self.pyfile.url):
            if self.premium:
                self.handleOverriden()
            else:
                self.fail("Only premium users can download from other hosters with %s" % self.HOSTER_NAME)
        else:
            self.html = self.load(pyfile.url, cookies = False, decode = True)
            try:
                self.file_info = self.getFileInfo()
            except:
                pyfile.name = html_unescape(unquote(urlparse(pyfile.url).path.split("/")[-1]))
                    
            self.header = self.load(self.pyfile.url, just_header = True, cookies = True)
            self.logDebug(self.header)

            if 'location' in self.header and re.match(self.DIRECT_LINK_PATTERN, self.header['location']):
                self.startDownload(self.header['location'])
            elif self.premium:
                self.handlePremium()
            else:
                self.handleFree()

    def handleFree(self):
        for i in range(5):
            data = self.getPostParameters()
            
            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.html = self.load(self.pyfile.url, post = data, ref = True)
            self.header = self.req.http.header
            self.req.http.c.setopt(FOLLOWLOCATION, 1)            
            
            found = re.search("Location\s*:\s*(.*)", self.header, re.I)
            if found:                
                break          
            elif not self.checkErrors():
                found = re.search(self.DIRECT_LINK_PATTERN, self.html, re.S)
                if not found: self.parseError('Download Link')
                break

        else: self.fail("No valid captcha code entered")
        
        self.startDownload(found.group(1))

    def handlePremium(self):
        self.html = self.load(self.pyfile.url, post = self.getPostParameters())
        found = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK')
        self.startDownload(found.group(1))

    def handleOverriden(self):
        self.html = self.load("http://www.%s" % self.HOSTER_NAME)
        action, inputs =  self.parseHtmlForm('')
        upload_id = "%012d" % int(random()*10**12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(action, inputs)
        self.html = self.load(action, post = inputs)

        action, inputs = self.parseHtmlForm('name="F1"')
        if not inputs: parseError('TEXTAREA')
        self.logDebug(inputs)
        if inputs['st'] == 'OK':
            self.html = self.load(action, post = inputs)
        else:
            self.fail(inputs['st'])

        found = re.search(self.OVR_DOWNLOAD_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK (OVR)')
        self.pyfile.url = found.group(1)
        self.retry()

    def startDownload(self, link):
        if self.captcha: self.correctCaptcha()
        self.logDebug('DIRECT LINK: %s' % link)
        self.download(link)

    def checkErrors(self):
        found = re.search(self.ERROR_PATTERN, self.html)
        if found:
            self.errmsg = found.group(1)
            self.logWarning(self.errmsg)

            if 'wait' in self.errmsg:
                wait_time = sum([int(v) * {"hour": 3600, "minute": 60, "second": 1}[u] for v, u in re.findall('(\d+)\s*(hour|minute|second)?', self.errmsg)])
                self.setWait(wait_time, True)
                self.wait()
            elif 'captcha' in self.errmsg:
                self.invalidCaptcha()
            elif 'countdown' in self.errmsg:
                self.retry(3)
            
        else:
            self.errmsg = None
        
        return self.errmsg

    def getPostParameters(self):
        for i in range(3):
            if not self.errmsg: self.checkErrors()

            action, inputs = self.parseHtmlForm("action=['\"]{2}")
            if not inputs: 
                if self.errmsg:
                    self.retry()
                else:
                    self.parseError("Form not found")
                    
            self.logDebug(inputs)

            if 'op' in inputs and inputs['op'] == 'download2':
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail("No or invalid passport")
            
                if not self.premium:                
                    found = re.search(self.WAIT_PATTERN, self.html)
                    if found:
                        wait_time = int(found.group(1)) + 1
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0
                    
                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time: self.wait()
                
                return inputs
            else:
                inputs['referer'] = self.pyfile.url

                if self.premium:
                    inputs['method_premium'] = "Premium Download"
                    if 'method_free' in inputs: del inputs['method_free']
                else:
                    inputs['method_free'] = "Free Download"
                    if 'method_premium' in inputs: del inputs['method_premium']

                self.html = self.load(self.pyfile.url, post = inputs, ref = True)
                self.errmsg = None

        else: self.parseError('FORM: %s' % (inputs['op'] if 'op' in inputs else 'UNKNOWN'))
    
    def handleCaptcha(self, inputs):
        found = re.search(self.RECAPTCHA_URL_PATTERN, self.html)
        if found:
            recaptcha_key = unquote(found.group(1))
            self.logDebug("RECAPTCHA KEY: %s" % recaptcha_key)
            recaptcha = ReCaptcha(self)
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key)
            return 1
        else:
            found = re.search(self.CAPTCHA_URL_PATTERN, self.html)
            if found:
                captcha_url = found.group(1)
                inputs['code'] = self.decryptCaptcha(captcha_url)
                return 2
        return 0
        
getInfo = create_getInfo(XFileSharingPro)