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
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url, decode=True)
        if re.search(FilejungleCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(FilejungleCom.FILE_INFO_PATTERN, html)
            if found is not None:
                name, size, units = found.groups()
                size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]
                result.append((name, size, 2, url))
    yield result

class FilejungleCom(Hoster):
    __name__ = "FilejungleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filejungle\.com/f/([^/]+).*"
    __version__ = "0.2"
    __description__ = """Filejungle.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<div id="file_name">([^<]+) <span class="filename_normal">\(([0-9.]+) (KB|MB|GB)\)</span></div>'
    FILE_OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>'
    RECAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey='([^']+)'"
    WAIT_TIME_PATTERN = r'<h1>Please wait for (\d+) seconds to download the next file\.</h1>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url)
        self.getFileInfo(pyfile)
        self.handleFree(pyfile)

    def getFileInfo(self, pyfile):
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()
        
        found = re.search(self.FILE_INFO_PATTERN, self.html)
        if not found: self.fail("Parse error (file info)")
        pyfile.name, size, units = found.groups()
        pyfile.size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]

    def handleFree(self, pyfile):       
        file_id = re.search(self.__pattern__, pyfile.url).group(1)
        url = "http://www.filejungle.com/f/%s" % file_id 
        self.logDebug("File ID: %s" % file_id)        
           
        # Get captcha
        found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html) 
        if not found: self.fail("Captcha key not found")
        captcha_key = found.group(1)
        
        json_response = self.load(pyfile.url, post = {"checkDownload" :	"check"}, decode = True)
        self.logDebug(json_response)     
        if r'"success":"showCaptcha"' in json_response:
            recaptcha = ReCaptcha(self)
            for i in range(5):
                captcha_challenge, captcha_response = recaptcha.challenge(captcha_key)
                self.logDebug("RECAPTCHA: %s : %s : %s" % (captcha_key, captcha_challenge, captcha_response))

                json_response = self.load("http://www.filejungle.com/checkReCaptcha.php", post = {
                    "recaptcha_challenge_field" : captcha_challenge, 	
                    "recaptcha_response_field" : captcha_response,	
                    "recaptcha_shortencode_field" :	file_id 
                    }, decode = True)
                self.logDebug(json_response)  
                if r'{"success":1}' in json_response:
                    self.correctCaptcha() 
                    break
                else:
                    self.invalidCaptcha()
            else: self.fail("Invalid captcha")
        elif r'"fail":"timeLimit"' in json_response:
            self.html = self.load(url, post = {"checkDownload" :	"showError", "errorType" :	"timeLimit"})
            found = re.search(self.WAIT_TIME_PATTERN, self.html)
            self.retry(5, int(found.group(1)) if found else 1200, "Time limit reached")
        else:
            self.fail("Unknown server response")
      
        json_response = self.load(url, post = {"downloadLink" :	"wait"}, decode = True)
        self.logDebug(json_response[:30])   
        found = re.search(r'"waitTime":(\d+)', json_response)
        if not found: self.fail("Cannot get wait time")
        self.setWait(int(found.group(1)))
        self.wait()
        
        response = self.load(url, post = {"downloadLink" :	"show"})     
        self.download(url, post = {"download" :	"normal"})