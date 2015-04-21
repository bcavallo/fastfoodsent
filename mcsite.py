import psycopg2 
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response, make_response, request, jsonify, Markup
from jinja2.ext import autoescape
import json
import pandas as pd
import numpy as np
import re
import time
import datetime
import random

app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def running_avg(arr1, arr2, N):
	'''
	Finds the running average where arr1 is a dataframe column containing
	values, arr2 is a dataframe column containing counts, and N is the span
	of the rolling average.

	@param arr1, dataframe column containing values to be average
	@param arr2, dataframe column containing counts of values to be 
        averaged
	@param N, span for rolling average

	returns, an array of the N-period rolling average
	'''

	i = 0
	size = len(arr1)
	res = []
	while i + N < size:
   		res.append(float(arr1.values[i:i+N].sum()) / arr2.values[i:i+N].sum())
        	i += 1
	return res


def grab_data(rest):
        '''
        grabs all data pertaining to a restaurant
	
	@param rest, a string corresponding to the name of a restaurant
	returns, a dataframe of all tweets pertaining to the restaurant
	'''

	time_now = time.time()
	conn = psycopg2.connect("dbname=fastfoodtweets user=vagrant")
	cur = conn.cursor()
	data = pd.read_sql("select * from mctweets where (text_cleaned like '%%%s%%') \
	and (time_adj < %s);" % (rest, (time_now)), conn)
	conn.close()
	data['c_times'] = data['time_adj'] * 1000
	counts = data.groupby(['c_times']).sents.count()
	sums = data.groupby(['c_times']).sents.sum()
	return (sorted(list(data.c_times.unique()))[6:], list(running_avg(sums, counts, 6))) 


app = Flask(__name__)

@app.route('/_get_tweets')	
def good_and_bad_tweets():
	rest = re.sub("[']", "", request.args.get('rest', 0, type=str).lower())
	ts = request.args.get('ts', 0, type=int)
	conn = psycopg2.connect("dbname=fastfoodtweets user=vagrant")
	cur = conn.cursor()
	data = pd.read_sql("select * from mctweets where (text_cleaned like '%%%s%%') \
        and (time_adj = %s);" % (rest, ts), conn)
        conn.close()
	good = data[data.sents == 1].sort(columns=['prob'])
	bad = data[data.sents == 0].sort(columns=['prob'])
	num_good = len(good)
	num_bad = len(bad)
	good = good.drop_duplicates(subset=['text_cleaned'])
	bad = bad.drop_duplicates(subset=['text_cleaned'])
	if len(good) >= 3:
		good = list(good.text.values[:3])
	else:
		good = list(good.text.values)
	if len(bad) >= 3:
		bad = list(bad.text.values[-3:])
	else:
		bad = list(bad.text.values)
        return jsonify(good=good, bad=bad, num_good=num_good, num_bad=num_bad)

@app.route('/')
def index():
        times, avgs = grab_data('mcdonalds')
	st_times, st_avgs = grab_data('starbucks')
	ch_times, ch_avgs = grab_data('chipotle')
	ta_times, ta_avgs = grab_data('taco bell')
	ph_times, ph_avgs = grab_data('pizza hut')
	kfc_times, kfc_avgs = grab_data('kfc')
	return render_template("hello.html", times=times, avgs=avgs,
		st_times=st_times, st_avgs=st_avgs, ch_times=ch_times, \
		ch_avgs=ch_avgs, ta_times=ta_times, ta_avgs=ta_avgs, \
		ph_times=ph_times, ph_avgs=ph_avgs, kfc_times=kfc_times, \
		kfc_avgs=kfc_avgs)	

	

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)


