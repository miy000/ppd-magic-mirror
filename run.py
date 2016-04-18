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
	# 舆情
	cursor.execute("select * from platform where major=1")
	platforms = cursor.fetchall()
	platNames = []
	for item in platforms:
		platNames.append(item['platName'])
	tmp = platNames
	tmp.append('p2p')
	cursor.execute("select * from sentiment where keyword in %s", [tmp])
	sentiments = cursor.fetchall()

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
				platforms[item['keyword']]['newskeywords'] = [[], [], [], [], []]
				continue
			tmp = item['content'].split(',')
			t1 = []
			t2 = []
			t3 = []
			t4 = []
			t5 = []
			for x in tmp:
				x = x.split(':')
				t1.append(x[0])
				t2.append(x[1])
				t3.append(x[2])
				t4.append(x[3])
				t5.append(x[4])
 			platforms[item['keyword']]['newskeywords'] = [t1, t2, t3, t4, t5]
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
			platforms[item['keyword']]['commentkeywords'] = [[], [], [], []]
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

	# 数据
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
	tmp.sort(lambda x,y:cmp(x,y), reverse=False)
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

	cursor.execute("select * from flow")
	flows = cursor.fetchall()
	for x in xrange(0, len(flows)):
		flows[x]['content'] = json.loads(flows[x]['content'])
	platCount['flow'] = flows

	closedb(db, cursor)

	return render_template('index.html', platforms=json.dumps(platforms), platNames=platNames, platNamesJson=json.dumps(platNames), platCount=json.dumps(platCount))

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
		if item[0].properties['name'] == '' or item[1].properties['name'] == '':
			continue
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
				tmp['group'] = 7

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
				tmp['group'] = 7

			forces['nodes'].append(tmp)

		if flag:
			forces['links'].append({'source': nodes_idx[item[0].properties['name']], 'target': nodes_idx[item[1].properties['name']], 'value': 1})
	return json.dumps({"ok": True, "knowledge": forces})

@app.route('/news', methods=['POST'])
def news():
	data = request.form
	(db, cursor) = connectdb()
	cursor.execute("select timestamp, title from news where keyword=%s order by timestamp asc", [data['keyword']])
	news = cursor.fetchall()
	closedb(db, cursor)

	tmp = {}
	for x in xrange(0, len(news)):
		news[x]['x'] = random.random()
		news[x]['y'] = random.random()
		news[x]['timestamp'] = int(news[x]['timestamp'])
		if news[x]['title'].find(data['keyword']) >= 0:
			if not tmp.has_key(str(news[x]['timestamp'])):
				tmp[str(news[x]['timestamp'])] = []
			tmp[str(news[x]['timestamp'])].append(news[x])

	news = []
	for key, value in tmp.items():
		if len(value) > 10:
			for x in xrange(0, len(value)):
				news.append(value[x])
		else:
			for item in value:
				news.append(item)

	news.sort(lambda x,y:cmp(x['timestamp'],y['timestamp']))

	begintime = np.min([x['timestamp'] for x in news])
	endtime = np.max([x['timestamp'] for x in news])
	interval = (endtime - begintime) / 10
	axis = []
	for x in xrange(0, 11):
		axis.append(time.strftime('%Y-%m-%d', time.localtime(float(begintime + interval * x))))

	interval = (endtime - begintime) / 100
	news_count = []
	tmp = 0
	last_timestamp = begintime + interval
	current = 0
	while current < len(news):
		item = news[current]
		if item['timestamp'] > last_timestamp:
			news_count.append(tmp)
			tmp = 0
			last_timestamp += interval
		else:
			tmp += 1
			current += 1

	curve = []
	curve.append([50, 440])
	max_count = np.max(news_count)
	for x in xrange(0, len(news_count)):
		curve.append([59 + x * 9, 440 - 440 * float(news_count[x]) / max_count])
	curve.append([59 + (len(news_count) - 1) * 9, 440])

	return json.dumps({"ok": True, "news": news, "axis": axis, "curve": curve})

@app.route('/people', methods=['POST'])
def people():
	data = request.form
	platPin = data['platPin']
	(db, cursor) = connectdb()
	cursor.execute("select * from people where platPin=%s",[platPin])
	people = list(cursor.fetchall())
	closedb(db, cursor)

	for x in xrange(0, len(people)):
		people[x]['number'] = x + 1
		if people[x]['position'].find(' ') >= 0:
			people[x]['position'] = people[x]['position'].split(' ')[0]
		if people[x]['position'].find('，') >= 0:
			people[x]['position'] = people[x]['position'].split('，')[0]
		if people[x]['position'].find('、') >= 0:
			people[x]['position'] = people[x]['position'].split('、')[0]

	if len(people) > 6:
		people = people[:6]

	return json.dumps({"ok": True, "people": people, "platPin": platPin})

@app.route('/platform/<platName>')
def platform(platName):
	(db, cursor) = connectdb()

	cursor.execute('select * from platform where platName=%s',[platName])
	platform = cursor.fetchone()
	if platform == None:
		cursor.execute('select * from platform where platName=%s',['拍拍贷'])
		platform = cursor.fetchone()

	cursor.execute('select * from people where platPin=%s', [platform['platPin']])
	people = cursor.fetchall()

	for x in xrange(0, len(people)):
		people[x]['number'] = x + 1
		if people[x]['position'].find(' ') >= 0:
			people[x]['position'] = people[x]['position'].split(' ')[0]
		if people[x]['position'].find('，') >= 0:
			people[x]['position'] = people[x]['position'].split('，')[0]
		if people[x]['position'].find('、') >= 0:
			people[x]['position'] = people[x]['position'].split('、')[0]

	if platform['score'] == '':
		platform['score'] == '暂无'

	if platform['lng'] == '':
		platform['lng'] = 121.48
		platform['lat'] = 31.22

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

	if platform['basicdata'] in ['', None, 'null']:
		platRadar = {'name':[],'value':[],'data':[],'unit':[]}
	else:
		tmp = json.loads(platform['basicdata'])
		if tmp.has_key('data'):
			tmp = tmp['data']
			platRadar = {'name':[],'value':[],'data':[],'unit':[]}
			units = ['万元','%','万元','万元','人','人','元','万元','个','月','人','人']
			for x in xrange(0, len(tmp['x'])):
				platRadar['name'].append(tmp['x'][x])
				if tmp.has_key('y2'):
					platRadar['value'].append(tmp['y2'][x])
				else:
					platRadar['value'].append(0)
				if tmp.has_key('y1'):
					platRadar['data'].append(tmp['y1'][x])
				else:
					platRadar['data'].append(0)
				platRadar['unit'].append(units[x])

	platformJson = {'peopleNumber':len(people), 'bidTimeDist':bidTimeDist, 'bidMoneyDist':bidMoneyDist, 'radar': platRadar}

	cursor.execute("select * from news where keyword=%s",[platform['platName']])
	news = cursor.fetchall()
	platformJson['newsCount'] = len(news)
	tmp = {}
	news_tmp = []
	if np.sum([x['title'].find(platform['platName']) >= 0 for x in news]) == 0:
		news_ratio = -1
	else:
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
		if item['content'] == '':
			continue
		data = json.loads(item['content'])
		if not data.has_key('x'):
			continue
		if not tmp.has_key('x'):
			tmp['x'] = data['x']
		tmp[data['titles'][0]] = [data['units'], data['y1']]
	platformdata = tmp
	
	platformJson['platformdata'] = platformdata

	cursor.execute("select * from timeline")
	timeline = list(cursor.fetchall())
	for x in xrange(0, len(timeline)):
		timestamp = timeline[x]['timestamp']
		timeline[x]['x'] = (0.5 + float(timestamp[:4]) - 2007) / 9.0
		timeline[x]['y'] = int(timestamp[5:])
		timeline[x]['timestamp'] = int(time.mktime(time.strptime(timeline[x]['timestamp'], '%Y-%m')))
	timeline.sort(lambda x,y:cmp(float(x['timestamp']),float(y['timestamp'])))
	for x in xrange(0, len(timeline)):
		timeline[x]['timestamp'] = time.strftime('%Y-%m', time.localtime(float(timeline[x]['timestamp'])))
	tmp = {}
	for x in xrange(0, len(timeline)):
		timestamp = timeline[x]['timestamp'][:4]
		if not tmp.has_key(timestamp):
			tmp[timestamp] = 0
		timeline[x]['y'] = tmp[timestamp]
		tmp[timestamp] += 1
	max_y = np.max([x['y'] for x in timeline]) + 1
	for x in xrange(0, len(timeline)):
		timeline[x]['y'] = float(timeline[x]['y']) / max_y

	platformJson['timeline'] = timeline

	keywords = platform['keywords']
	if keywords == '':
		keywords = []
	else:
		keywords = keywords.split(',')
	if len(keywords) > 60:
		keywords = keywords[:60]
	tmp = []
	colors = ['rgba(84, 148, 191, 0.8)','rgba(221, 107, 102, 0.8)','rgba(230, 157, 135, 0.8)','rgba(234, 126, 83, 0.8)','rgba(243, 230, 162, 0.8)']
	for item in keywords:
		c = int(np.random.random() * 5)
		if c == 5:
			c = 4
		tmp.append({'name':item.split(':')[0], 'value':int(float(item.split(':')[1]) * 30 + 10), 'itemStyle':{'normal':{'color':colors[c]}}})

	platformJson['keywords'] = tmp

	closedb(db, cursor)

	return render_template('platform.html', platform=platform, people=people, platformJson=json.dumps(platformJson))

@app.route('/compare')
def compare():
	(db, cursor) = connectdb()
	cursor.execute("select * from platform where score != '' and tSNEx != '' and tSNEy != '' order by score desc")
	platforms = list(cursor.fetchall())

	for x in xrange(0, len(platforms)):
		if platforms[x]['tags'] == '':
			platforms[x]['tags'] = []
		else:
			platforms[x]['tags'] = platforms[x]['tags'].split(',')

		platforms[x]['score'] = float(platforms[x]['score'])
		platforms[x]['bidDistribution'] = json.loads(platforms[x]['bidDistribution'])
		platforms[x]['basicdata'] = json.loads(platforms[x]['basicdata'])
		platforms[x]['averageProfit'] = float(platforms[x]['averageProfit'][:-1])
		platforms[x]['registMoney'] = float(platforms[x]['registMoney'][:platforms[x]['registMoney'].find('万元')])
		platforms[x]['location'] = platforms[x]['location'].replace('|', ' ')
		
		if platforms[x]['location'] == '':
			platforms[x]['location'] = '-'
		platforms[x]['location'] = platforms[x]['location'].strip('')
		if platforms[x]['category'] == '':
			platforms[x]['category'] = '-'
		platforms[x]['category'] = platforms[x]['category'].replace(' ', '')
		if platforms[x]['autobid'] == '':
			platforms[x]['autobid'] = '-'
		platforms[x]['autobid'] = platforms[x]['autobid'].replace(' ', '')
		if platforms[x]['stockTransfer'] == '':
			platforms[x]['stockTransfer'] = '-'
		platforms[x]['stockTransfer'] = platforms[x]['stockTransfer'].replace(' ', '')
		if platforms[x]['fundsToken'] == '':
			platforms[x]['fundsToken'] = '-'
		if len(platforms[x]['fundsToken']) > 15:
			platforms[x]['fundsToken'] = platforms[x]['fundsToken'][:15] + '...'
		platforms[x]['fundsToken'] = platforms[x]['fundsToken'].replace(' ', '')
		if platforms[x]['bidGuarantee'] == '':
			platforms[x]['bidGuarantee'] = '-'
		if len(platforms[x]['bidGuarantee']) > 15:
			platforms[x]['bidGuarantee'] = platforms[x]['bidGuarantee'][:15] + '...'
		platforms[x]['bidGuarantee'] = platforms[x]['bidGuarantee'].replace(' ', '')
		if platforms[x]['guaranteeMode'] == '':
			platforms[x]['guaranteeMode'] = '-'
		if len(platforms[x]['guaranteeMode']) > 15:
			platforms[x]['guaranteeMode'] = platforms[x]['guaranteeMode'][:15] + '...'
		platforms[x]['guaranteeMode'] = platforms[x]['guaranteeMode'].replace(' ', '')
		if platforms[x]['guaranteeOrg'] == '':
			platforms[x]['guaranteeOrg'] = '-'
		if len(platforms[x]['guaranteeOrg']) > 15:
			platforms[x]['guaranteeOrg'] = platforms[x]['guaranteeOrg'][:15] + '...'
		platforms[x]['guaranteeOrg'] = platforms[x]['guaranteeOrg'].replace(' ', '')

		platforms[x]['positive_date'] = platforms[x]['positive_date'].split(',')
		if len(platforms[x]['positive_date']) == 1 and platforms[x]['positive_date'][0] == '':
			platforms[x]['positive_date'] = []
		else:
			for i in xrange(0, len(platforms[x]['positive_date'])):
				platforms[x]['positive_date'][i] = int(time.mktime(time.strptime(platforms[x]['positive_date'][i], '%Y-%m-%d')))

		platforms[x]['negative_date'] = platforms[x]['negative_date'].split(',')
		if len(platforms[x]['negative_date']) == 1 and platforms[x]['negative_date'][0] == '':
			platforms[x]['negative_date'] = []
		else:
			for i in xrange(0, len(platforms[x]['negative_date'])):
				platforms[x]['negative_date'][i] = int(time.mktime(time.strptime(platforms[x]['negative_date'][i], '%Y-%m-%d')))

	platforms.sort(lambda x,y:cmp(float(x['score']),float(y['score'])), reverse=True)

	# xmin = np.min([float(x['tSNEx']) for x in platforms])
	# xmax = np.max([float(x['tSNEx']) for x in platforms])
	# ymin = np.min([float(x['tSNEy']) for x in platforms])
	# ymax = np.max([float(x['tSNEy']) for x in platforms])
	# smin = np.min([float(x['score']) for x in platforms])
	# smax = np.max([float(x['score']) for x in platforms])

	# for x in xrange(0, len(platforms)):
	# 	platforms[x]['x'] = 60 + (float(platforms[x]['tSNEx']) - xmin) * 820 / (xmax - xmin)
	# 	platforms[x]['y'] = 580 - (float(platforms[x]['tSNEy']) - ymin) * 540 / (ymax - ymin)
	# 	platforms[x]['nscore'] = (float(platforms[x]['score']) - smin) / (smax - smin)

	closedb(db, cursor)
	return render_template('compare.html', platforms=json.dumps(platforms))

@app.route('/matrix', methods=['POST'])
def matrix():
	data = request.form

	(db, cursor) = connectdb()
	cursor.execute("select * from matrix where platName1=%s and platName2=%s",[data['platName1'], data['platName2']])
	matrix = cursor.fetchone()

	tmp = matrix['keywords1'].split(',')
	t1 = tmp[0].split(':')
	t2 = tmp[1].split(':')
	t3 = tmp[2].split(':')
	for x in xrange(0, len(t1)):
		t2[x] = int(t2[x])
		t3[x] = int(t3[x])
	keywords1 = [t1,t2,t3]

	tmp = matrix['keywords2'].split(',')
	t1 = tmp[0].split(':')
	t2 = tmp[1].split(':')
	t3 = tmp[2].split(':')
	for x in xrange(0, len(t1)):
		t2[x] = int(t2[x])
		t3[x] = int(t3[x])
	keywords2 = [t1,t2,t3]

	matrix = matrix['matrix'].split(',')
	t1 = []
	t2 = []
	t3 = []
	t4 = []
	t5 = []
	for item in matrix:
		item = item.split(':')
		t1.append(abs(float(item[2])))
		t2.append(int(item[3]))
		t3.append(int(item[4]))
		t4.append(int(item[5]))
		t5.append(int(item[6]))
	matrix = [t1,t2,t3,t4,t5]

	closedb(db, cursor)

	data = {'keywords1':keywords1, 'keywords2':keywords2, 'matrix':matrix}

	return json.dumps({"ok": True, 'data': data})

@app.route('/compare_trade', methods=['POST'])
def compare_trade():
	data = request.form

	(db, cursor) = connectdb()
	cursor.execute("select * from platformdata where platId=%s and type=1",[data['platId1']])
	data1 = json.loads(cursor.fetchone()['content'])
	start1 = int(time.mktime(time.strptime(data1['x'][0], '%Y-%m-%d')))
	end1 = int(time.mktime(time.strptime(data1['x'][-1], '%Y-%m-%d')))
	data1 = data1['y1']
	max1 = np.max(data1)
	cursor.execute("select * from platformdata where platId=%s and type=1",[data['platId2']])
	data2 = json.loads(cursor.fetchone()['content'])
	start2 = int(time.mktime(time.strptime(data2['x'][0], '%Y-%m-%d')))
	end2 = int(time.mktime(time.strptime(data2['x'][-1], '%Y-%m-%d')))
	data2 = data2['y1']
	max2 = np.max(data2)

	closedb(db, cursor)

	return json.dumps({"ok": True, "data1": [start1, end1, (end1 - start1) / (len(data1) - 1), data1, max1], "data2": [start2, end2, (end2 - start2) / (len(data2) - 1), data2, max2]})

@app.route('/question')
def question():
	colors = ['rgba(84, 148, 191, 0.8)','rgba(221, 107, 102, 0.8)','rgba(230, 157, 135, 0.8)','rgba(234, 126, 83, 0.8)','rgba(243, 230, 162, 0.8)', 'rgba(117, 179, 117, 0.8)']

	data = []
	idx = 0
	# data.append({'id':idx, 'name':'找平台', 'group':0, 'order':0, 'size':36})
	# idx += 1
	# data.append({'id':idx, 'name':'搜人员', 'group':0, 'order':0, 'size':36})
	# idx += 1
	# data.append({'id':idx, 'name':'查数据', 'group':0, 'order':0, 'size':36})
	# idx += 1

	data.append({'id':idx, 'name':'河南', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'北京', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'广东', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'上海', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'江苏', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'湖南', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'河北', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'浙江', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'四川', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'湖北', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'山西', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'山东', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'广西', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'江西', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'天津', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'新疆', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'安徽', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'贵州', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'重庆', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'福建', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'辽宁', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'陕西', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'海南', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'云南', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'黑龙江', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'宁夏', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'甘肃', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'内蒙', 'group':3, 'order':1, 'size':16})
	idx += 1
	data.append({'id':idx, 'name':'吉林', 'group':3, 'order':1, 'size':16})
	idx += 1

	data.append({'id':idx, 'name':'2007', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2009', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2010', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2011', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2012', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2013', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2014', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2015', 'group':4, 'order':1, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'2016', 'group':4, 'order':1, 'size':18})
	idx += 1

	data.append({'id':idx, 'name':'国资系', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'上市公司系', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'跑路', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'经侦介入', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'股权上市', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'银行系', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'加入协会', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'停业', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'提现困难', 'group':6, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'加入第三方征信', 'group':6, 'order':1, 'size':14})
	idx += 1

	data.append({'id':idx, 'name':'股份制', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'私营', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'联营', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'股份合作', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'港、澳、台投资', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'国有', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'集体所有制', 'group':5, 'order':1, 'size':14})
	idx += 1
	data.append({'id':idx, 'name':'外商投资', 'group':5, 'order':1, 'size':14})
	idx += 1

	data.append({'id':idx, 'name':'发展指数', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'平均利率', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'注册资金', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'平均投资期限', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'人均投资金额', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'人均借款金额', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'成交量', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'历史待还', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'资金净流入', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'投资人数', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'借款人数', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'借款标数', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'待收投资人数', 'group':1, 'order':2, 'size':20})
	idx += 1
	data.append({'id':idx, 'name':'待还借款人数', 'group':1, 'order':2, 'size':20})
	idx += 1

	data.append({'id':idx, 'name':'最大', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最多', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最高', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最长', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最小', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最少', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最低', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'最短', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'前三', 'group':2, 'order':3, 'size':18})
	idx += 1
	data.append({'id':idx, 'name':'前十', 'group':2, 'order':3, 'size':18})
	idx += 1

	# group: 7

	for x in xrange(0, len(data)):
		if data[x]['group'] == 3:
			data[x]['size'] = 18
		if data[x]['group'] == 2:
			data[x]['size'] = 22

	datadict = {}
	for item in data:
		item['color'] = colors[item['group'] - 1]
		datadict[item['name']] = item

	return render_template('question.html', data=json.dumps(data), datadict=json.dumps(datadict))

@app.route('/question1', methods=['POST'])
def question1():
	data = dict(request.form)
	querys = []
	if data.has_key('year'):
		if data['year'][0] == '0':
			querys.append("question_year!='' and question_year>=2")
		elif data['year'][0] == '1':
			querys.append("question_year!='' and question_year<2")

	if data.has_key('location'):
		if data['location'][0] == '0':
			querys.append("question_location!='' and question_location in ('北京','上海','广州')")
		elif data['location'][0] == '1':
			querys.append("question_location!='' and question_location not in ('北京','上海','广州')")

	if data.has_key('month'):
		if data['month'][0] == '0':
			querys.append("question_month!='' and question_month>=6")
		elif data['month'][0] == '1':
			querys.append("question_month!='' and question_month<6")

	if data.has_key('amount'):
		if data['amount'][0] == '0':
			querys.append("question_amount!='' and question_amount>=10000")
		elif data['amount'][0] == '1':
			querys.append("question_amount!='' and question_amount<10000")

	if data.has_key('rate'):
		if data['rate'][0] == '0':
			querys.append("question_rate!='' and question_rate>=12")
		elif data['rate'][0] == '1':
			querys.append("question_rate!='' and question_rate<12")

	if data.has_key('regist'):
		if data['regist'][0] == '0':
			querys.append("question_regist!='' and question_regist>=5000")
		elif data['regist'][0] == '1':
			querys.append("question_regist!='' and question_regist<5000")

	querys = "select platName, question_type from platform where " + (' and ').join(querys) + " order by score desc"

	(db, cursor) = connectdb()
	cursor.execute(querys)
	platforms = cursor.fetchall()
	closedb(db, cursor)

	return json.dumps({"ok": True, "platforms": platforms})

@app.route('/question2', methods=['POST'])
def question2():
	query = dict(request.form)
	tmp = []
	for key, value in query.items():
		tmp.append(value[0])

	(db, cursor) = connectdb()

	select = 'select platName,'
	query = ' from platform '
	torder = ''
	tlimit = ''
	param = ''
	unit = ''
	condition = False
	for item in tmp:
		if item in ['河南','北京','广东','上海','江苏','湖南','河北','浙江','四川','湖北','山西','山东','广西','江西','天津','新疆','安徽','贵州','重庆','福建','辽宁','陕西','海南','云南','黑龙江','宁夏','甘肃','内蒙','吉林']:
			if not condition:
				condition = True
				query += 'where question_location="' + item + '" '
			else:
				query += 'and question_location="' + item + '" '
		if item in ['2007','2009','2010','2011','2012','2013','2014','2015','2016']:
			if not condition:
				condition = True
				query += 'where question_launch="' + item + '" '
			else:
				query += 'and question_launch="' + item + '" '
		if item in ['国资系','上市公司系','跑路','经侦介入','股权上市','银行系','加入协会','停业','提现困难','加入第三方征信']:
			if not condition:
				condition = True
				query += 'where tags like "%' + item + '%" '
			else:
				query += 'and tags like "%' + item + '%" '
		if item in ['股份制','私营','联营','股份合作','港、澳、台投资','国有','集体所有制','外商投资']:
			if not condition:
				condition = True
				query += 'where category="' + item + '" '
			else:
				query += 'and category="' + item + '" '
		if item in ['发展指数','平均利率','注册资金','平均投资期限','人均投资金额','人均借款金额','成交量','历史待还','资金净流入','投资人数','借款人数','借款标数','待收投资人数','待还借款人数']:
			if item == '发展指数':
				torder = 'order by score '
				select += 'score'
				param = 'score'
				unit = ''
			elif item == '平均利率':
				torder = 'order by question_rate '
				select += 'question_rate'
				param = 'question_rate'
				unit = '%'
			elif item == '注册资金':
				torder = 'order by question_regist '
				select += 'question_regist'
				param = 'question_regist'
				unit = '万元'
			elif item == '平均投资期限':
				torder = 'order by question_month '
				select += 'question_month'
				param = 'question_month'
				unit = '月'
			elif item == '人均投资金额':
				torder = 'order by question_amount '
				select += 'question_amount'
				param = 'question_amount'
				unit = '元'
			elif item == '人均借款金额':
				torder = 'order by question_borrow '
				select += 'question_borrow'
				param = 'question_borrow'
				unit = '万元'
			elif item == '成交量':
				torder = 'order by question_trade '
				select += 'question_trade'
				param = 'question_trade'
				unit = '万元'
			elif item == '历史待还':
				torder = 'order by question_history '
				select += 'question_history'
				param = 'question_history'
				unit = '万元'
			elif item == '资金净流入':
				torder = 'order by question_flow '
				select += 'question_flow'
				param = 'question_flow'
				unit = '万元'
			elif item == '投资人数':
				torder = 'order by question_invest_num '
				select += 'question_invest_num'
				param = 'question_invest_num'
				unit = '人'
			elif item == '借款人数':
				torder = 'order by question_borrow_num '
				select += 'question_borrow_num'
				param = 'question_borrow_num'
				unit = '人'
			elif item == '借款标数':
				torder = 'order by question_bid_num '
				select += 'question_bid_num'
				param = 'question_bid_num'
				unit = '个'
			elif item == '待收投资人数':
				torder = 'order by question_earn_num '
				select += 'question_earn_num'
				param = 'question_earn_num'
				unit = '人'
			elif item == '待还借款人数':
				torder = 'order by question_pay_num '
				select += 'question_pay_num'
				param = 'question_pay_num'
				unit = '人'
		if item in ['最大','最多','最高','最长']:
			tlimit = 'desc limit 1'
		if item in ['最小','最少','最低','最短']:
			tlimit = 'asc limit 1'
		if item == '前三':
			tlimit = 'desc limit 3'
		if item == '前十':
			tlimit = 'desc limit 10'

	cursor.execute(select + query + torder + tlimit)
	answer = cursor.fetchall()

	result = []
	for item in answer:
		if param in ['question_invest_num', 'question_borrow_num', 'question_earn_num', 'question_pay_num']:
			item[param] = int(item[param])
		result.append(item['platName'] + ' ' + str(item[param]) + unit)

	closedb(db, cursor)

	return json.dumps({"ok": True, "query": tmp, "answer": result})

@app.route('/question3', methods=['POST'])
def question3():
	data = request.form

	location = data['location']
	category = data['category']
	year = data['year']
	tag = data['tag']
	similar = data['similar']

	query1 = "match (p:Platform)"
	query2 = " where p.name={name} return p,q"
	if location == 'true':
		query1 += ",(p)-[:LOCATION]-(s1:Sublocation)-[:LOCATION]-(t1:Location)-[:LOCATION]-(s2:Sublocation)-[:LOCATION]-(q:Platform)"
		query2 += ",t1"
	if category == 'true':
		query1 += ",(p)-[:CATEGORY]-(t2)-[:CATEGORY]-(q:Platform)"
		query2 += ",t2"
	if year == 'true':
		query1 += ",(p)-[:YEAR]-(t3)-[:YEAR]-(q:Platform)"
		query2 += ",t3"
	if tag == 'true':
		query1 += ",(p)-[:TAG]-(t4)-[:TAG]-(q:Platform)"
		query2 += ",t4"
	if similar == 'true':
		query1 += ",(p)-[:SIMILAR]-(t5)-[:SIMILAR]-(q:Platform)"
		query2 += ",t5"

	records = graph.cypher.execute(query1 + query2, name=data['name'])

	tmp = []
	for x in xrange(0, len(records)):
		for y in xrange(0, len(records[x])):
			if list(records[x][y].labels)[0] == 'Platform' and (not records[x][y].properties['name'] in tmp):
				tmp.append(records[x][y].properties['name'])
	platCount = len(tmp) - 1

	forces = {'nodes': [], 'links': []}
	idx = 0
	nodes = []
	nodes_idx = {}
	stat = {}
	for item in records:
		flag = False
		for x in xrange(0, len(item)):
			it = item[x]
			label = list(it.labels)[0]

			if not [it.properties['name'], label] in nodes:
				nodes.append([it.properties['name'], label])
				nodes_idx[it.properties['name']] = idx
				idx += 1
				if idx > 100:
					flag = True

				tmp = {}
				tmp['name'] = it.properties['name']
				if label == 'Platform':
					tmp['group'] = 1
					if tmp['name'] == data['name']:
						tmp['group'] = 2
					tmp['fundsToken'] = it.properties['fundsToken']
					tmp['guaranteeOrg'] = it.properties['guaranteeOrg']
					tmp['address'] = it.properties['address']
					tmp['lauchTime'] = it.properties['lauchTime']
					tmp['registMoney'] = it.properties['registMoney']
					tmp['averageProfit'] = it.properties['averageProfit']
					tmp['score'] = it.properties['score']
					tmp['autobid'] = it.properties['autobid']
					tmp['platPin'] = it.properties['platPin']
					tmp['guaranteeMode'] = it.properties['guaranteeMode']
					tmp['bidGuarantee'] = it.properties['bidGuarantee']
					tmp['logo'] = it.properties['logo']
					tmp['stockTransfer'] = it.properties['stockTransfer']
					tmp['homepage'] = it.properties['homepage']
				elif label == 'Person':
					tmp['group'] = 2
					tmp['description'] = it.properties['description']
					tmp['portrait'] = it.properties['portrait']
				elif label == 'Category':
					tmp['group'] = 3
				elif label == 'Location':
					tmp['group'] = 4
				elif label == 'Tag':
					tmp['group'] = 5
				elif label == 'Year':
					tmp['group'] = 6
				elif label == 'Position':
					tmp['group'] = 7

				forces['nodes'].append(tmp)

			if x >= 2:
				if not stat.has_key(it.properties['name']):
					stat[it.properties['name']] = []
				if not item[0].properties['name'] in stat[it.properties['name']]:
					stat[it.properties['name']].append(item[0].properties['name'])
					forces['links'].append({'source': nodes_idx[item[0].properties['name']], 'target': nodes_idx[it.properties['name']], 'value': 1})
				if not item[1].properties['name'] in stat[it.properties['name']]:
					stat[it.properties['name']].append(item[1].properties['name'])
					forces['links'].append({'source': nodes_idx[item[1].properties['name']], 'target': nodes_idx[it.properties['name']], 'value': 1})
		if flag:
			break

	return json.dumps({"ok": True, "knowledge": forces, "platCount": platCount})

if __name__ == '__main__':
	app.run(debug=True)