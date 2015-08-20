"""
The MIT License (MIT)

Copyright (c) 2014 Alexandre Passant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import time
import smtplib
from email.mime.text import MIMEText

import twitter

class TwitterCleaner(object):
    """
    TwitterCleaner, a bot to clean your Twitter followees.

    Automatically removes people who haven't send any Tweet for X days
    from your followees (30 by default). Better to use as a crontab.
    
    Parameters
    ----------
    consumer_key : string
        Your Twitter app consumer_key
    consumer_secret : string
        Your Twitter app consumer_secret
    access_token_key : string
        Your Twitter app access_token_key
    access_token_secret : string
        Your Twitter app access_token_secret
    whitelist : list, optional
        A list of user to whitelist, i.e. not remove.
        Needs to be a list of screennames, not user ids 
    mailto : string, optional
        An e-mail to receive notification report
    max_days : integer, optional, default = 30
        The number of days after which a user is considered as inactive,
        i.e. will be removed if no post more recent than this
    list_name : string, optional
        The slug (aka short name) of the list to add followees to
    handle : string, optional (required if list_name is defined)
        Your Twitter handle, used for adding followees to list
    """
    def __init__(self, consumer_key, consumer_secret, 
                    access_token_key, access_token_secret,
                    whitelist=None, mailto=None, max_days=30,
                    handle=None, list_name=None):
        self.api = twitter.Api(consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=access_token_key,
                      access_token_secret=access_token_secret)
        self.whitelist = whitelist
        self.mailto = mailto
        self.max_days = max_days
        self.handle = handle
        self.list_name = list_name
        self.deleted = []

    def run(self):
        """Main handler to run the deletion."""
        self._delete_followees()
        if self.mailto:
            self._email_summary()

    def _delete(self, followee, days):
        """Effective deletion of Twitter followees."""
        self.api.DestroyFriendship(followee.id)
        self.deleted.append((followee.screen_name, days))

        """Add users to the list"""
        if self.list_name:
          # print "adding %s to %s:%s" % (followee.id, self.handle, self.list_name)
          self.api.CreateListsMember(slug=self.list_name,user_id=followee.id,owner_screen_name=self.handle)
 
    def _email_summary(self):
        """Send summary e-mail."""
        self.deleted.sort(key=lambda x: x[0])
        body = """
The following users had been removed from your followee list:

- %s

They've also been added to your inactive list.

Have an A1 day!

-- 
TwitterCleaner, your Twitter bot.
        """%('\n- '.join(['%s (last message: %s)' %(f[0], f[1]) 
                                    for f in self.deleted]))
        message = MIMEText(body, 'plain')
        message['Subject'] = 'Your daily report for TwitterCleaner'
        message['From'] = self.mailto
        message['To'] = self.mailto

        """Print output, just in case SMTP fails (i.e. no MTA running)"""
        print "%s" % body

        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(self.mailto, [self.mailto], message.as_string())

    def _delete_followees(self):
        """Delete followees, unless there's in the whitelist."""
        for f in self.api.GetFriends(count=200):
            if f.screen_name in self.whitelist:
                continue
            if not f.status:
                self._delete(f, 'None')
            else:
                last_status = f.status.created_at
                time_last_status = time.mktime(time.strptime(last_status, 
                                        '%a %b %d %H:%M:%S +0000 %Y'))
                now = time.mktime(time.localtime())
                days = (now-time_last_status)/(3600*24)
                if days > self.max_days:
                    self._delete(f, '%s days ago' %int(days))

""" EOF """
