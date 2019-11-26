# -*- coding: utf-8 -*-
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
from lxml import etree
import os
import time
import sqlite3

keywords = ['오버워치', '롤', '리그오브레전드']

#키워드로 최근 영상 찾는 함수, 예외 처리 추가해야함
def getRecentVideos(driver, keyword):
	url = 'https://www.youtube.com/results?search_query={}&sp=CAISBAgBEAE%253D'.format(keyword)
	driver.get(url)
	recents = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [recent.get_attribute('href') for recent in recents]
	for link in returnList:
		saveUnvisited(link)

def getVideoInfo(driver, url):
	driver.get(url)
	title = driver.find_element_by_xpath('//*[@id="container"]/h1/yt-formatted-string').text
	count = driver.find_element_by_xpath('//*[@id="count"]/yt-view-count-renderer/span[1]').text
	youtuber = driver.find_element_by_xpath('//*[@id="text"]/a').text
	return title, count, youtuber

def getRelatedLinks(driver, url):
	driver.get(url)
	lst = driver.find_elements_by_xpath('//*[@id="dismissable"]/div[1]/a')
	returnList = [elem.get_attribute('href') for elem in lst]
	print(returnList)
	return returnList

def getCommentLinks(driver, url):
	driver.get(url)
	cnt = 0
	maxCnt = 4
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
	#코멘트 불러오기
	comments = driver.find_elements_by_xpath('//*[@id="author-text"]')
	returnList = [comment.get_attribute('href') for comment in comments]
	return returnList


def getVideoList(driver, url):
	url = os.path.join(url, 'videos')
	driver.get(url)
	sleep(2)
	videos = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [video.get_attribute('href') for video in videos]
	return returnList	

def crawlVideos(driver):
	global videoList
	global channelList
	url = getVideo()
	title, count, youtuber = getVideoInfo(driver, url)
	saveVideo(title, url, count)

def crawlChannels(driver):
	global videoList
	global channelList
	url = getChannel()
	videoList += getVideoList(driver, url)

def crawlRecentVideos(driver):
	for keyword in keywords:
		getRecentVideos(driver, keyword)

def getVideo():
	con, cur = connect()
	sql = 'SELECT * FROM unvisited ORDER BY RANDOM() limit 1'
	cur.execute(sql)
	row = cur.fetchall()
	sql = "DELETE FROM unvisited WHERE link = '{}'".format(row[0][0])
	cur.execute(sql)
	con.commit()
	return row[0][0]

def getChannel():
	con, cur = connect()
	sql = 'SELECT * FROM youtubers ORDER BY RANDOM() limit 1'
	cur.execute(sql)
	row = cur.fetchall()
	return row[0]

def connect():
	con = sqlite3.connect('data.db')
	cur = con.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS youtubers(name text, link text, subscribers int);")
	cur.execute("CREATE TABLE IF NOT EXISTS videos(title text, link text, visit int);")
	cur.execute("CREATE TABLE IF NOT EXISTS unvisited(link text);")
	return con, cur

def saveVideo(title, link, visit):
	print('Saving video... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO videos VALUES(?, ?, ?)", (title, link, visit))
	con.commit()
	con.close()

def saveYoutuber(name, link, subscribers):
	print('Saving video... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO youtubers VALUES(?, ?, ?)", (name, link, subscribers))
	con.commit()
	con.close()

def saveUnvisited(link):
	print('Saving unvisited... : ' + link)
	con, cur = connect()
	cur.execute("INSERT INTO unvisited VALUES(?)", (link, ))
	con.commit()
	con.close()


#크롬 드라이버를 불러온다 (headless 버전 테스트하고 headless로 교체해야함 )
driver = webdriver.Chrome('./chromedriver.exe')
driver.implicitly_wait(3) #드라이버 로딩

while True:
	crawlRecentVideos(driver)
	for i in range(3):
		crawlVideos(driver)

driver.close() #크롬 드라이버 반환