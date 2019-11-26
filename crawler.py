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

keywords = ['오버워치', '롤', '배틀그라운드']

#키워드로 최근 영상 찾는 함수, 예외 처리 추가해야함
def getRecentVideos(driver, keyword):
	url = 'https://www.youtube.com/results?search_query={}&sp=CAISBAgBEAE%253D'.format(keyword)
	driver.get(url)
	scroll(driver, 4)
	recents = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [recent.get_attribute('href') for recent in recents]
	for link in returnList:
		if link is not None: #광고 영상은 패스
			saveUnvisited(link, keyword)

def getVideoInfo(driver, url):
	driver.get(url)
	title = driver.find_element_by_xpath('//*[@id="container"]/h1/yt-formatted-string').text
	count = driver.find_element_by_xpath('//*[@id="count"]/yt-view-count-renderer/span[1]').text
	youtuber = driver.find_element_by_xpath('//*[@id="text"]/a').text
	return title, count, youtuber

#한 영상의 관련 동영상을 불러옴 
def getRelatedLinks(driver, url):
	driver.get(url)
	lst = driver.find_elements_by_xpath('//*[@id="dismissable"]/div[1]/a')
	returnList = [elem.get_attribute('href') for elem in lst]
	print(returnList)
	return returnList

#댓글을 단 계정의 링크를 가져옴
def getCommentLinks(driver, url):
	driver.get(url)
	scroll(driver, 4)
	#코멘트 불러오기
	comments = driver.find_elements_by_xpath('//*[@id="author-text"]')
	returnList = [comment.get_attribute('href') for comment in comments]
	return returnList


#특정 사용자의 비디오 리스트를 불러옴
def getVideoList(driver, url):
	url = os.path.join(url, 'videos')
	driver.get(url)
	sleep(2)
	videos = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [video.get_attribute('href') for video in videos]
	return returnList	

#unvisited 동영상 중 하나를 가져와서 크롤링
def crawlVideos(driver):
	global videoList
	global channelList
	url, keyword = getVideo()
	if url is None:
		return
	title, count, youtuber = getVideoInfo(driver, url)
	saveVideo(title, url, count, keyword)

#채널 크롤링
def crawlChannels(driver):
	global videoList
	global channelList
	url = getChannel()
	videoList += getVideoList(driver, url)

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
		url = row[0][0]
		keyword = row[0][1]
		if not isinstance(url, str):
			url = url.decode()
		sql = "DELETE FROM unvisited WHERE link = '{}'".format(url)
		print(sql)
		cur.execute(sql)
		con.commit()
		return url, keyword
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
	cur.execute("CREATE TABLE IF NOT EXISTS videos(title text, link text, visit int, keyword text);")
	cur.execute("CREATE TABLE IF NOT EXISTS unvisited(link text, keyword text);")
	return con, cur

def saveVideo(title, link, visit, keyword):
	if doesExist('videos', 'link', link):
		return
	print('Saving video... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO videos VALUES(?, ?, ?, ?)", (title, link, visit, keyword))
	con.commit()
	con.close()

def saveYoutuber(name, link, subscribers):
	print('Saving video... : ' + link)
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

#크롬 드라이버를 불러온다 (headless 버전 테스트하고 headless로 교체해야함 )
driver = webdriver.Chrome('./chromedriver.exe')
driver.implicitly_wait(3) #드라이버 로딩


while True:
	try:
		crawlRecentVideos(driver)
		count = getCount('unvisited')
		print('Crawling {} vidoes...'.format(count))
		for i in range(count):
			crawlVideos(driver)
	except:
		traceback.print_exc()
driver.close() #크롬 드라이버 반환