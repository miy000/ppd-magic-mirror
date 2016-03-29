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
from py2neo import *
from config import *
import pprint
import random

app = Flask(__name__)
app.config.from_object(__name__)

authenticate(NEOHOST + ":7474", NEOUSER, NEOPASSWORD)
graph = Graph("http://" +  NEOHOST + ":7474/db/data")

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
	platNames = []
	for item in platforms:
		platNames.append(item['platName'])
	tmp = platNames
	tmp.append('p2p')
	cursor.execute("select * from sentiment where keyword in %s", [tmp])
	sentiments = cursor.fetchall()
	closedb(db, cursor)

	tmp = {}
	for item in platforms:
		tmp[item['platName']] = item
	platforms = tmp
	platforms['p2p'] = {}

	days = []
	start = 1167580800
	while start <= 1451491200:
		days.append(time.strftime('%Y-%m-%d', time.localtime(float(start))))
		start += 3600 * 24
	platforms['days'] = days

	for item in sentiments:
		if item['type'] == 'newskeyword':
			if item['content'] == '':
				platforms[item['keyword']]['newskeywords'] = [[], []]
				continue
			tmp = item['content'].split(',')
 			platforms[item['keyword']]['newskeywords'] = [[x.split(':')[0] for x in tmp], [x.split(':')[1] for x in tmp]]
		if item['type'] == 'newspositive':
			if item['content'] == '':
				platforms[item['keyword']]['newspositive'] = [0 for x in xrange(0, len(days))]
				continue
			tmp = item['content'].split(',')
			tmp1 = {}
			for t in tmp:
				tmp1[time.strftime('%Y-%m-%d', time.localtime(float(t.split(':')[0])))] = int(t.split(':')[1])
			tmp2 = []
			for t in days:
				if tmp1.has_key(t):
					tmp2.append(tmp1[t])
				else:
					tmp2.append(0)
			platforms[item['keyword']]['newspositive'] = tmp2
		if item['type'] == 'newsnegative':
			if item['content'] == '':
				platforms[item['keyword']]['newsnegative'] = [0 for x in xrange(0, len(days))]
				continue
			tmp = item['content'].split(',')
			tmp1 = {}
			for t in tmp:
				tmp1[time.strftime('%Y-%m-%d', time.localtime(float(t.split(':')[0])))] = int(t.split(':')[1])
			tmp2 = []
			for t in days:
				if tmp1.has_key(t):
					tmp2.append(tmp1[t])
				else:
					tmp2.append(0)
			platforms[item['keyword']]['newsnegative'] = tmp2
		if item['type'] == 'commentkeyword':
			if item['content'] == '':
				platforms[item['keyword']]['commentkeywords'] = [[], []]
				continue
			tmp = item['content'].split(',')
			platforms[item['keyword']]['commentkeywords'] = [[x.split(':')[0] for x in tmp], [x.split(':')[1] for x in tmp]]
		if item['type'] == 'commentpositive':
			if item['content'] == '':
				platforms[item['keyword']]['commentpositive'] = [0 for x in xrange(0, len(days))]
				continue
			tmp = item['content'].split(',')
			tmp1 = {}
			for t in tmp:
				tmp1[time.strftime('%Y-%m-%d', time.localtime(float(t.split(':')[0])))] = int(t.split(':')[1])
			tmp2 = []
			for t in days:
				if tmp1.has_key(t):
					tmp2.append(tmp1[t])
				else:
					tmp2.append(0)
			platforms[item['keyword']]['commentpositive'] = tmp2
		if item['type'] == 'commentnegative':
			if item['content'] == '':
				platforms[item['keyword']]['commentnegative'] = [0 for x in xrange(0, len(days))]
				continue
			tmp = item['content'].split(',')
			tmp1 = {}
			for t in tmp:
				tmp1[time.strftime('%Y-%m-%d', time.localtime(float(t.split(':')[0])))] = int(t.split(':')[1])
			tmp2 = []
			for t in days:
				if tmp1.has_key(t):
					tmp2.append(tmp1[t])
				else:
					tmp2.append(0)
			platforms[item['keyword']]['commentnegative'] = tmp2

	return render_template('index.html', platforms=json.dumps(platforms), platNames=platNames, platNamesJson=json.dumps(platNames))

@app.route('/knowledge', methods=['POST'])
def knowledge():
	data = request.form
	name = data['name']
	records = graph.cypher.execute("match (p),(p)-[]-(n) where p.name={name} return p, n", name=name)

	forces = {'nodes': [], 'links': []}
	idx = 0
	nodes = []
	nodes_idx = {}
	for item in records:
		flag = False
		label = list(item[0].labels)[0]
		if not [item[0].properties['name'], label] in nodes:
			nodes.append([item[0].properties['name'], label])
			nodes_idx[item[0].properties['name']] = idx
			idx += 1
			flag = True

			tmp = {}
			tmp['name'] = item[0].properties['name']
			if label == 'Platform':
				tmp['group'] = 1
				tmp['fundsToken'] = item[0].properties['fundsToken']
				tmp['guaranteeOrg'] = item[0].properties['guaranteeOrg']
				tmp['address'] = item[0].properties['address']
				tmp['lauchTime'] = item[0].properties['lauchTime']
				tmp['registMoney'] = item[0].properties['registMoney']
				tmp['averageProfit'] = item[0].properties['averageProfit']
				tmp['score'] = item[0].properties['score']
				tmp['autobid'] = item[0].properties['autobid']
				tmp['platPin'] = item[0].properties['platPin']
				tmp['guaranteeMode'] = item[0].properties['guaranteeMode']
				tmp['bidGuarantee'] = item[0].properties['bidGuarantee']
				tmp['logo'] = item[0].properties['logo']
				tmp['stockTransfer'] = item[0].properties['stockTransfer']
				tmp['homepage'] = item[0].properties['homepage']
			elif label == 'Person':
				tmp['group'] = 2
				tmp['description'] = item[0].properties['description']
				tmp['portrait'] = item[0].properties['portrait']
			elif label == 'Category':
				tmp['group'] = 3
			elif label == 'Sublocation':
				tmp['group'] = 4
			elif label == 'Tag':
				tmp['group'] = 5
			elif label == 'Year':
				tmp['group'] = 6
			elif label == 'Position':
				tmp['group'] = 6

			forces['nodes'].append(tmp)

		label = list(item[1].labels)[0]
		if not [item[1].properties['name'], label] in nodes:
			nodes.append([item[1].properties['name'], label])
			nodes_idx[item[1].properties['name']] = idx
			idx += 1
			flag = True

			tmp = {}
			tmp['name'] = item[1].properties['name']
			if label == 'Platform':
				tmp['group'] = 1
				tmp['fundsToken'] = item[1].properties['fundsToken']
				tmp['guaranteeOrg'] = item[1].properties['guaranteeOrg']
				tmp['address'] = item[1].properties['address']
				tmp['lauchTime'] = item[1].properties['lauchTime']
				tmp['registMoney'] = item[1].properties['registMoney']
				tmp['averageProfit'] = item[1].properties['averageProfit']
				tmp['score'] = item[1].properties['score']
				tmp['autobid'] = item[1].properties['autobid']
				tmp['platPin'] = item[1].properties['platPin']
				tmp['guaranteeMode'] = item[1].properties['guaranteeMode']
				tmp['bidGuarantee'] = item[1].properties['bidGuarantee']
				tmp['logo'] = item[1].properties['logo']
				tmp['stockTransfer'] = item[1].properties['stockTransfer']
				tmp['homepage'] = item[1].properties['homepage']
			elif label == 'Person':
				tmp['group'] = 2
				tmp['description'] = item[1].properties['description']
				tmp['portrait'] = item[1].properties['portrait']
			elif label == 'Category':
				tmp['group'] = 3
			elif label == 'Sublocation':
				tmp['group'] = 4
			elif label == 'Tag':
				tmp['group'] = 5
			elif label == 'Year':
				tmp['group'] = 6
			elif label == 'Position':
				tmp['group'] = 6

			forces['nodes'].append(tmp)

		if flag:
			forces['links'].append({'source': nodes_idx[item[0].properties['name']], 'target': nodes_idx[item[1].properties['name']], 'value': 1})
	return json.dumps({"ok": True, "knowledge": forces})

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

@app.route('/platform/<platName>')
def platform(platName):
	(db, cursor) = connectdb()

	cursor.execute('select * from platform where platName=%s',[platName])
	platform = cursor.fetchone()

	cursor.execute('select * from people where platPin=%s', [platform['platPin']])
	people = cursor.fetchall()

	for x in xrange(0, len(people)):
		people[x]['number'] = x + 1

	if platform['score'] == '':
		platform['score'] == '暂无'

	platform['homepage'] = platform['homepage'].split('/')[-1]

	tmp = json.loads(platform['bidDistribution'])
	tmp1 = tmp['deadline']
	bidTimeDist = []
	for item in tmp1:
		bidTimeDist.append({'name':item['name'],'value':item['y']})
	tmp2 = tmp['platamount']
	bidMoneyDist = []
	for item in tmp2:
		bidMoneyDist.append({'name':item['name'],'value':item['y']})

	tmp = json.loads(platform['basicdata'])['data']
	platRadar = {'name':[],'value':[],'data':[],'unit':[]}
	units = ['万元','%','万元','万元','人','人','元','万元','个','月','人','人']
	for x in xrange(0, len(tmp['x'])):
		platRadar['name'].append(tmp['x'][x])
		platRadar['value'].append(tmp['y2'][x])
		platRadar['data'].append(tmp['y1'][x])
		platRadar['unit'].append(units[x])

	platformJson = {'peopleNumber':len(people), 'bidTimeDist':bidTimeDist, 'bidMoneyDist':bidMoneyDist, 'radar': platRadar}

	cursor.execute("select * from news where keyword=%s",[platform['platName']])
	news = cursor.fetchall()
	platformJson['newsCount'] = len(news)
	tmp = {}
	news_tmp = []
	news_ratio = 1 - 100 / float(np.sum([x['title'].find(platform['platName']) >= 0 for x in news]))
	for item in news:
		if not tmp.has_key(item['source']):
			tmp[item['source']] = 0
		tmp[item['source']] += 1

		if random.random() > news_ratio and item['title'].find(platform['platName']) >= 0:
			item['timestamp'] = time.strftime('%Y-%m-%d', time.localtime(float(item['timestamp'])))
			news_tmp.append(item)
	news = news_tmp
	newsStat = []
	for key, value in tmp.items():
		newsStat.append({"value": value, "name": key, "path": key})
	newsStat.sort(lambda x,y:cmp(x['value'],y['value']), reverse=True)
	platformJson['news'] = news
	platformJson['newsStat'] = newsStat

	cursor.execute("select * from comment where platName=%s",[platform['platName']])
	comment = cursor.fetchall()

	for x in xrange(0, len(comment)):
		comment[x]['timestamp'] = time.strftime('%Y-%m-%d', time.localtime(float(comment[x]['timestamp'])))

	platformJson['comment'] = comment

	cursor.execute('select * from platformdata where platId=%s',[platform['platId']])
	platformdata = list(cursor.fetchall());
	platformdata.sort(lambda x,y:cmp(int(x['type']),int(y['type'])))

	tmp = {}
	for item in platformdata:
		if int(item['type']) > 12:
			continue
		data = json.loads(item['content'])
		if not tmp.has_key('x'):
			tmp['x'] = data['x']
		tmp[data['titles'][0]] = [data['units'], data['y1']]
	platformdata = tmp
	
	platformJson['platformdata'] = platformdata

	closedb(db, cursor)

	return render_template('platform.html', platform=platform, people=people, platformJson=json.dumps(platformJson))

@app.route('/compare')
def compare():
	(db, cursor) = connectdb()
	cursor.execute("select * from platform where score != '' and tSNEx != '' and tSNEy != ''")
	platforms = list(cursor.fetchall())

	for x in xrange(0, len(platforms)):
		platforms[x]['bidDistribution'] = json.loads(platforms[x]['bidDistribution'])
		platforms[x]['basicdata'] = json.loads(platforms[x]['basicdata'])
	platforms.sort(lambda x,y:cmp(float(x['score']),float(y['score'])), reverse=True)

	xmin = np.min([float(x['tSNEx']) for x in platforms])
	xmax = np.max([float(x['tSNEx']) for x in platforms])
	ymin = np.min([float(x['tSNEy']) for x in platforms])
	ymax = np.max([float(x['tSNEy']) for x in platforms])
	smin = np.min([float(x['score']) for x in platforms])
	smax = np.max([float(x['score']) for x in platforms])

	for x in xrange(0, len(platforms)):
		platforms[x]['x'] = 10 + (float(platforms[x]['tSNEx']) - xmin) * 880 / (xmax - xmin)
		platforms[x]['y'] = 490 - (float(platforms[x]['tSNEy']) - ymin) * 460 / (ymax - ymin)
		platforms[x]['score'] = (float(platforms[x]['score']) - smin) / (smax - smin)

	closedb(db, cursor)
	return render_template('compare.html', platforms=json.dumps(platforms))

if __name__ == '__main__':
	app.run(debug=True)