from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import json
import psycopg2
from sklearn.externals import joblib
import numpy as np
import pandas as pd
import re
from config import *

cv = joblib.load('/home/vagrant/flask_site/classifiers/cv.pkl')
nb = joblib.load('/home/vagrant/flask_site/classifiers/nb.pkl')

def round_ten_min(n):
	return int(n) - (int(n) % 600) + 600

# create an auth object
auth = OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

conn = psycopg2.connect("dbname=testdb user=vagrant password=pwd")
cur = conn.cursor()




class listener(StreamListener):
    def on_data(self, data):
        try:
	    lang = data.split(',"lang":"')[1].split('","contributors_enabled')[0]
	    if lang == 'en':
	    	created = round_ten_min(time.time())
            	tweet = data.split(',"text":"')[1].split('","source')[0]
            	clean_tweet = re.sub("[']", "", tweet.lower())
		sent = nb.predict(cv.transform([tweet]))[0]
		cur.execute("INSERT INTO tweets (time, text, text_clean, sent) VALUES (%s, %s, %s, %s)", (created, tweet, clean_tweet, sent))
		cur.execute("DELETE FROM tweets WHERE time < %s;", [created - 43201])
	    	conn.commit()
            return True
        except BaseException, e:
            print 'failed ondata', str(e)
	    print data
	    conn.rollback()
            time.sleep(5)
	    
            
    def on_error(self, status):
        print status

twitterStream = Stream(auth, listener())
twitterStream.filter(track=['mcdonalds', 'burger king', 'starbucks', 'chipotle', 'taco bell', 'kfc'])
#'wendys', 'chipotle', 'shake shack', 'taco bell', 'kfc', 'pizza hut', 'dominos pizza', 'five guys', 'in-n-out', 'whataburger', 'starbucks', 'dunkin donuts', 'panera', 'arbys', 'popeyes', 'boston market'])
