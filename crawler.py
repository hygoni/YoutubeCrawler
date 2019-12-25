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

keywords = ['오버워치', '롤', '배틀그라운드']

#크롬 드라이버를 불러온다 (headless 버전 테스트하고 headless로 교체해야함 )
driver = webdriver.Chrome('./chromedriver.exe')
driver.implicitly_wait(3) #드라이버 로딩

con = db.connect()

while True:
	try:
		count = db.getCount(con, 'unvisited')
		print('Crawling {} vidoes...'.format(count))
		for i in range(count):
			crawl.crawlVideos(con, driver)
		crawl.crawlRecentVideos(con, driver)
	except KeyboardInterrupt:
		exit()
	except:
		traceback.print_exc()
		
driver.close() #크롬 드라이버 반환