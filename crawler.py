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

keywords = ['오버워치', '롤', '배틀그라운드']

#키워드로 최근 영상 찾는 함수, 예외 처리 추가해야함
def getRecentVideos(driver, keyword):
	link = 'https://www.youtube.com/results?search_query={}&sp=CAISBAgBEAE%253D'.format(keyword)
	driver.get(link)
	scroll(driver, 4)
	recents = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [recent.get_attribute('href') for recent in recents]
	for link in returnList:
		if link is not None: #광고 영상은 패스
			saveUnvisited(link, keyword)

def getVideoInfo(driver, link):
	driver.get(link)
	title = driver.find_element_by_xpath('//*[@id="container"]/h1/yt-formatted-string').text
	count = driver.find_element_by_xpath('//*[@id="count"]/yt-view-count-renderer/span[1]').text
	youtuber = driver.find_element_by_xpath('//*[@id="text"]/a').text
	return title, count, youtuber

#한 영상의 관련 동영상을 불러옴 
def getRelatedLinks(driver, link):
	driver.get(link)
	lst = driver.find_elements_by_xpath('//*[@id="dismissable"]/div[1]/a')
	returnList = [elem.get_attribute('href') for elem in lst]
	print(returnList)
	return returnList

#댓글을 단 계정의 링크를 가져옴
def getCommentLinks(driver, link):
	driver.get(link)
	scroll(driver, 4)
	#코멘트 불러오기
	comments = driver.find_elements_by_xpath('//*[@id="author-text"]')
	returnList = [comment.get_attribute('href') for comment in comments]
	return returnList


#특정 사용자의 비디오 리스트를 불러옴
def getVideoList(driver, link):
	link = os.path.join(link, 'videos')
	driver.get(link)
	sleep(2)
	videos = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [video.get_attribute('href') for video in videos]
	return returnList	

#unvisited 동영상 중 하나를 가져와서 크롤링
def crawlVideos(driver):
	global videoList
	global channelList
	link, keyword = getVideo()
	if link is None:
		return
	title, count, youtuber = getVideoInfo(driver, link)
	channelLink = getYoutuberFromVideo(driver, link)
	crawlChannels(driver, channelLink)
	saveVideo(channelLink, title, link, count, keyword)

#카워드별 최근 동영상 크롤링
def crawlRecentVideos(driver):
	for keyword in keywords:
		getRecentVideos(driver, keyword)

#unvisited 동영상 중 하나를 가져온 후 DB에서 삭제함
def getVideo():
	try:
		con, cur = connect()
		sql = 'SELECT link, keyword FROM unvisited ORDER BY RANDOM() limit 1'
		print(sql)
		cur.execute(sql)
		row = cur.fetchall()
		link = row[0][0]
		keyword = row[0][1]
		if not isinstance(link, str):
			link = link.decode()
		sql = "DELETE FROM unvisited WHERE link = '{}'".format(link)
		print(sql)
		cur.execute(sql)
		con.commit()
		return link, keyword
	except:
		traceback.print_exc()
		print('No videos unvisited!')
		return None, None

def getChannel():
	con, cur = connect()
	sql = 'SELECT * FROM youtubers ORDER BY RANDOM() limit 1'
	cur.execute(sql)
	row = cur.fetchall()
	return row[0]

#DB에 연결
def connect():
	con = sqlite3.connect('data.db')
	cur = con.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS youtubers(name text, link text, subscribers int);")
	cur.execute("CREATE TABLE IF NOT EXISTS videos(youtuber_link text, title text, link text, visit int, keyword text);")
	cur.execute("CREATE TABLE IF NOT EXISTS unvisited(link text, keyword text);")
	return con, cur

def saveVideo(youtuberLink, title, link, visit, keyword):
	if doesExist('videos', 'link', link):
		return
	print('Saving video... : ' + link)
	visit = subscribersToInteger(visit) # '구독자 XX명' -> 숫자로 변환
	con, cur = connect()
	cur.execute("INSERT INTO videos VALUES(?, ?, ?, ?, ?)", (youtuberLink, title, link, visit, keyword))
	con.commit()
	con.close()

def saveYoutuber(name, link, subscribers):
	if doesExist('youtubers', 'link', link):
		return
	print('Saving youtuber... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO youtubers VALUES(?, ?, ?)", (name, link, subscribers))
	con.commit()
	con.close()

def saveUnvisited(link, keyword):
	if doesExist('unvisited', 'link', link) or doesExist('videos', 'link', link):
		return
	print('Saving unvisited... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO unvisited VALUES(?, ?)", (link, keyword))
	con.commit()
	con.close()

def doesExist(table, name, value, isString=True):
	con, cur = connect()
	sql = ''
	if isString:
		sql = "SELECT count(*) FROM {} WHERE {} = '{}'".format(table, name, value)
	else:
		sql = "SELECT count(*) FROM {} WHERE {} = {}".format(table, name, value)
	cur.execute(sql)
	count = cur.fetchone()[0]
	con.close()
	return count > 0

def getCount(table):
	con, cur = connect()
	sql = "SELECT count(*) FROM {}".format(table)
	cur.execute(sql)
	count = cur.fetchone()[0]
	con.close()
	return count

def scroll(driver, maxCnt):
	cnt = 0
	last_height = driver.execute_script("return document.documentElement.scrollHeight")
	while True:
		if cnt == maxCnt:
			break;
		cnt += 1
		#아래로 스크롤
		driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
		# 댓글 로딩
		time.sleep(2)
		#스크롤할 위치 갱신
		new_height = driver.execute_script("return document.documentElement.scrollHeight")
		if new_height == last_height:
			break
		last_height = new_height
		driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

def getYoutuberFromVideo(driver, link):
	driver.get(link)
	channel = driver.find_element_by_xpath('//*[@id="text"]/a').get_attribute('href')
	return channel

#채널 크롤링
def crawlChannels(driver, link):
	if doesExist('youtubers', 'link', link):
		return
	print('Crawling channel... : {}'.format(link))
	driver.get(link)
	name = driver.find_element_by_xpath('//*[@id="text-container"]').text
	subscribers = driver.find_element_by_xpath('//*[@id="subscriber-count"]').text
	saveYoutuber(name, link, subscribersToInteger(subscribers))

def subscribersToInteger(text):
	if text == None or text == '':
		return 0
	p = re.compile('[0-9]+(\.)?[0-9]*(만명|천명|명)')
	m = p.search(text)
	if m == None:
		return 0
	text = m.group()
	num = 0.0
	multiplier = 1
	p = re.compile('[0-9]+(\.)?[0-9]*')
	m = p.search(text)
	num = float(m.group())
	p = re.compile('(만명|천명|명)')
	m = p.search(text)
	text = m.group()
	if text == '만명':
		multiplier = 10000
	elif text == '천명':
		multiplier = 1000
	elif text == '명':
		multiplier = 1
	return int(num * multiplier)

#크롬 드라이버를 불러온다 (headless 버전 테스트하고 headless로 교체해야함 )
driver = webdriver.Chrome('./chromedriver.exe')
driver.implicitly_wait(3) #드라이버 로딩


while True:
	try:
		
		count = getCount('unvisited')
		print('Crawling {} vidoes...'.format(count))
		for i in range(count):
			crawlVideos(driver)
		crawlRecentVideos(driver)
	except:
		traceback.print_exc()
driver.close() #크롬 드라이버 반환