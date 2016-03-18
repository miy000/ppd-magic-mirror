#!/usr/bin/env python
# coding:utf8

import time
import sys
reload(sys)
sys.setdefaultencoding( "utf8" )
from flask import *
import warnings
warnings.filterwarnings("ignore")
import MySQLdb
import MySQLdb.cursors
import numpy as np
from config import *
import pprint

app = Flask(__name__)
app.config.from_object(__name__)

# 连接数据库
def connectdb():
	db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db=DATABASE, port=PORT, charset=CHARSET, cursorclass = MySQLdb.cursors.DictCursor)
	db.autocommit(True)
	cursor = db.cursor()
	return (db,cursor)

# 关闭数据库
def closedb(db,cursor):
	db.close()
	cursor.close()

# 首页
@app.route('/')
def index():
	(db, cursor) = connectdb()
	cursor.execute("select * from platform where major=1")
	platforms = cursor.fetchall()
	closedb(db, cursor)

	return render_template('index.html', platforms=platforms)

@app.route('/knowledge', methods=['POST'])
def knowledge():
	data = request.form
	name = data['name']
	return json.dumps({"ok": True, "knowledge": name})

@app.route('/data')
def data():
	(db, cursor) = connectdb()
	cursor.execute("select * from overalldata where name='platform_with_problem_of_last_12_month'")
	tmp = json.loads(cursor.fetchone()['content'])

	platCount = {}
	platCount['pie1'] = tmp['pie1']
	platCount['pie2'] = tmp['pie2']

	cursor.execute("select tags,lng,lat from platform where address != ''")
	tmp = cursor.fetchall()
	platCount['map'] = [[],[],[],[],[]]
	for item in tmp:
		if item['lng'] == '' or item['lat'] == '':
			continue
		if item['tags'].find('停业') >= 0:
			platCount['map'][1].append([float(item['lng']),float(item['lat']),1])
		elif item['tags'].find('提现困难') >= 0:
			platCount['map'][2].append([float(item['lng']),float(item['lat']),1])
		elif item['tags'].find('跑路') >= 0:
			platCount['map'][3].append([float(item['lng']),float(item['lat']),1])
		elif item['tags'].find('经侦介入') >= 0 or item['tags'].find('争议') >= 0:
			platCount['map'][4].append([float(item['lng']),float(item['lat']),1])
		else:
			platCount['map'][0].append([float(item['lng']),float(item['lat']),1])

	cursor.execute("select distinct(month) from rank")
	tmp = cursor.fetchall()
	tmp = [x['month'] for x in tmp]
	tmp.sort(lambda x,y:cmp(x,y), reverse=True)
	platCount['rank'] = []
	for t in tmp:
		cursor.execute("select * from rank where month=%s order by score desc limit 20", [t])
		t1 = cursor.fetchall()
		for x in xrange(0, len(t1)):
			t1[x]['rank'] = 20 - x
			t1[x]['distribution'] = float(t1[x]['distribution'])
			t1[x]['flooding'] = float(t1[x]['flooding'])
			t1[x]['opacity'] = float(t1[x]['opacity'])
			t1[x]['popularity'] = float(t1[x]['popularity'])
			t1[x]['score'] = float(t1[x]['score'])
			t1[x]['trade'] = float(t1[x]['trade'])
			t1[x]['weight'] = float(t1[x]['weight'])
		platCount['rank'].append([t, t1])

	cursor.execute("select * from overalldata where name='index_of_last_one_month'")
	tmp = json.loads(cursor.fetchone()['content'])
	platCount['index'] = [tmp['date'], tmp['interestRate'], tmp['popularity'], tmp['volume']]

	cursor.execute("select * from overalldata where name like 'place_%%'")
	tmp = cursor.fetchall()
	result = []
	for item in tmp:
		month = item['name'].split('_')[1]
		month = int(time.mktime(time.strptime(month, '%Y-%m')))
		result.append([month, json.loads(item['content'])])
	result.sort(lambda x,y:cmp(x[0],y[0]))	
	platCount['places'] = {'places':[],'series':[],'months':[]}
	for item in result[0][1]:
		if item['province'] == '全国':
			continue
		platCount['places']['places'].append(item['province'])

	maxnum = [0,-1,-1,-1,-1,-1,-1,-1,-1,-1]
	for item in result:
		platCount['places']['months'].append(time.strftime('%Y-%m', time.localtime(float(item[0]))))
		tmp = item[1]
		tmp.sort(lambda x,y:cmp(x['province'],y['province']), reverse=True)
		tmp1 = []
		for t in tmp:
			if t['province'] == '全国':
				continue
			tmp1.append([t['province'],t['amount'],t['operatePlatNumber'],t['problemPlatNumber'],t['problemPlatNumberTotal'],t['balanceLoans'],t['incomeRate'],t['loanPeriod'],t['bidderNum'],t['borrowerNum']])
			if t['amount'] > maxnum[1]:
				maxnum[1] = t['amount']
			if t['operatePlatNumber'] > maxnum[2]:
				maxnum[2] = t['operatePlatNumber']
			if t['problemPlatNumber'] > maxnum[3]:
				maxnum[3] = t['problemPlatNumber']
			if t['problemPlatNumberTotal'] > maxnum[4]:
				maxnum[4] = t['problemPlatNumberTotal']
			if t['balanceLoans'] > maxnum[5]:
				maxnum[5] = t['balanceLoans']
			if t['incomeRate'] > maxnum[6]:
				maxnum[6] = t['incomeRate']
			if t['loanPeriod'] > maxnum[7]:
				maxnum[7] = t['loanPeriod']
			if t['bidderNum'] > maxnum[8]:
				maxnum[8] = t['bidderNum']
			if t['borrowerNum'] > maxnum[9]:
				maxnum[9] = t['borrowerNum']
		platCount['places']['series'].append(tmp1)
	platCount['places']['max'] = maxnum

	cursor.execute("select * from overalldata where name like 'type_%%'")
	tmp = cursor.fetchall()
	result = []
	for item in tmp:
		month = item['name'].split('_')[1]
		month = int(time.mktime(time.strptime(month, '%Y-%m')))
		result.append([month, json.loads(item['content'])])
	result.sort(lambda x,y:cmp(x[0],y[0]))	
	platCount['types'] = {'types':[],'series':[],'months':[], 'max':[]}
	for item in result[0][1]:
		platCount['types']['types'].append({'name':item['province']})

	for item in result:
		platCount['types']['months'].append(time.strftime('%Y-%m', time.localtime(float(item[0]))))
		tmp = item[1]
		tmp.sort(lambda x,y:cmp(x['province'],y['province']), reverse=True)
		tmp1 = []
		maxnum = [0,-1,-1,-1,-1,-1,-1,-1,-1,-1]
		for t in tmp:
			tmp1.append({'value':[t['amount'],t['operatePlatNumber'],t['problemPlatNumber'],t['problemPlatNumberTotal'],t['balanceLoans'],t['incomeRate'],t['loanPeriod'],t['bidderNum'],t['borrowerNum']], 'name':t['province'].rstrip('系')})
			if t['amount'] > maxnum[1]:
				maxnum[1] = t['amount']
			if t['operatePlatNumber'] > maxnum[2]:
				maxnum[2] = t['operatePlatNumber']
			if t['problemPlatNumber'] > maxnum[3]:
				maxnum[3] = t['problemPlatNumber']
			if t['problemPlatNumberTotal'] > maxnum[4]:
				maxnum[4] = t['problemPlatNumberTotal']
			if t['balanceLoans'] > maxnum[5]:
				maxnum[5] = t['balanceLoans']
			if t['incomeRate'] > maxnum[6]:
				maxnum[6] = t['incomeRate']
			if t['loanPeriod'] > maxnum[7]:
				maxnum[7] = t['loanPeriod']
			if t['bidderNum'] > maxnum[8]:
				maxnum[8] = t['bidderNum']
			if t['borrowerNum'] > maxnum[9]:
				maxnum[9] = t['borrowerNum']
		platCount['types']['series'].append(tmp1)
		platCount['types']['max'].append(maxnum)

	closedb(db, cursor)

	return render_template('data.html', platCount=json.dumps(platCount))

@app.route('/platform')
def platform():
	return render_template('platform.html')

@app.route('/compare')
def compare():
	return render_template('compare.html')

if __name__ == '__main__':
	app.run(debug=True)