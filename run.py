#!/usr/bin/env python
# coding:utf8

import sys
reload(sys)
sys.setdefaultencoding( "utf8" )
from flask import *
import warnings
warnings.filterwarnings("ignore")
import MySQLdb
import MySQLdb.cursors
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
	cursor.execute("select * from overalldata where name='platform_of_last_12_month'")
	tmp1 = json.loads(cursor.fetchone()['content'])
	cursor.execute("select * from overalldata where name='platform_with_problem_of_last_12_month'")
	tmp2 = json.loads(cursor.fetchone()['content'])

	platCount = {}
	platCount['x'] = tmp1['x']
	platCount['x'].reverse()
	platCount['y1'] = tmp1['y2']
	platCount['y1'].reverse()
	platCount['y2'] = tmp1['y1']
	platCount['y2'].reverse()
	platCount['y3'] = tmp2['y1']
	platCount['y3'].reverse()
	platCount['y4'] = tmp2['y2']
	platCount['y4'].reverse()
	platCount['pie1'] = tmp2['pie1']
	platCount['pie2'] = tmp2['pie2']

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