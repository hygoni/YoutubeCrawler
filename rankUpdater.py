# -*- coding: utf-8 -*-
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
from lxml import etree
import os
import time
import sqlite3
import sys
import traceback
import re
sys.path.append('./lib')
import db 
import crawl
import pdb

dbName = input('db 파일 이름을 입력하세요 : ')

if not os.path.isfile(dbName):
	#pdb.set_trace()
	os.system('copy data.db {}'.format(dbName)) #기존 데이터베이스 복제
	con = db.connectUpdater(dbName)
	cur = con.cursor()
	sql = "DELETE FROM unvisited"
	cur.execute(sql)
	con.commit()
	sql = '''
	INSERT INTO unvisited(link, keyword)
	SELECT link, 'none' FROM youtubers
	'''
	cur.execute(sql)
	con.commit()
	sql = 'DELETE FROM youtubers'
	cur.execute(sql)
	con.commit()

con = db.connectUpdater(dbName)

#크롬 드라이버를 불러온다 (headless 버전 테스트하고 headless로 교체해야함 )
driver = webdriver.Chrome('./chromedriver.exe')
driver.implicitly_wait(3) #드라이버 로딩

while True:
	try:
		count = db.getCount(con, 'unvisited')
		if count == 0:	
			print('All youtubers\' are updated!')
			exit()
		print('Updating {} youtubers...'.format(count))
		for i in range(count):
			link = db.getUnvisited(con)[0]
			crawl.crawlChannel(con, driver, link)
	except:
		traceback.print_exc()
		driver.close()
		exit()

driver.close() #크롬 드라이버 반환