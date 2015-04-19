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
from nltk.corpus import stopwords
import langid
import nltk

nltk.data.path.append("/home/vagrant/flask_site/nltk_data")

cv = joblib.load('/home/vagrant/flask_site/classifiers/cv.pkl')
nb = joblib.load('/home/vagrant/flask_site/classifiers/nb.pkl')

my_stop = stopwords.words('english') + ['mcdonalds','pizza hut', \
	'starbucks','taco bell','chipotle','kfc', 'rt', 'http', 'https']

def round_ten_min(n):
	return n - (n % 600) + 600

def rem_stop_words(s):
    return ' '.join([word for word in s.split() if word not in my_stop])

# create an auth object
auth = OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

conn = psycopg2.connect("dbname=fastfoodtweets user=vagrant password=pwd")
cur = conn.cursor()

class listener(StreamListener):
    def on_data(self, data):
        try:
	    tweet = data.split(',"text":"')[1].split('","source')[0]
	    tweet = re.sub(r'\shttps?:(.+)','', tweet)
	    lang = langid.classify(tweet)[0]
	    if lang == 'en':
		created = int(time.time())
	    	created_adj = round_ten_min(created)
            	clean_tweet = re.sub("['@]", "", tweet.lower())
		sent = nb.predict(cv.transform([clean_tweet]))[0]
		prob = nb.predict_proba(cv.transform([rem_stop_words(clean_tweet)]))[0][0]
		cur.execute("INSERT INTO mctweets (time, time_adj, text, text_cleaned, \
		sents, prob) VALUES (%s, %s, %s, %s, %s, %s)", (created, created_adj, \
		tweet, clean_tweet, sent, prob))
		cur.execute("DELETE FROM mctweets WHERE time < %s;", [created - 90001])
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
twitterStream.filter(track=['mcdonalds', 'pizza hut', 'starbucks', 'chipotle', 'taco bell', 'kfc'], languages=['en'])
#'wendys', 'chipotle', 'shake shack', 'taco bell', 'kfc', 'pizza hut', 'dominos pizza', 'five guys', 'in-n-out', 'whataburger', 'starbucks', 'dunkin donuts', 'panera', 'arbys', 'popeyes', 'boston market'])
