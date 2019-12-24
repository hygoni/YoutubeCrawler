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

#local library
sys.path.append('.')
import db

#키워드로 최근 영상 찾는 함수
def getRecentVideos(driver, keyword):
	link = 'https://www.youtube.com/results?search_query={}&sp=CAISBAgBEAE%253D'.format(keyword)
	driver.get(link)
	scroll(driver, 4)
	recents = driver.find_elements_by_xpath('//*[@id="video-title"]')
	returnList = [recent.get_attribute('href') for recent in recents]
	for link in returnList:
		if link is not None: #광고 영상은 패스
			db.saveUnvisited(link, keyword)

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
	link, keyword = db.getVideo()
	if link is None:
		return
	title, count, youtuber = getVideoInfo(driver, link)
	channelLink = getYoutuberFromVideo(driver, link)
	crawlChannels(driver, channelLink)
	db.saveVideo(channelLink, title, link, count, keyword)

#카워드별 최근 동영상 크롤링
def crawlRecentVideos(driver):
	for keyword in keywords:
		getRecentVideos(driver, keyword)

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
	if db.doesExist('youtubers', 'link', link):
		return
	print('Crawling channel... : {}'.format(link))
	driver.get(link)
	name = driver.find_element_by_xpath('//*[@id="text-container"]').text
	subscribers = driver.find_element_by_xpath('//*[@id="subscriber-count"]').text
	db.saveYoutuber(name, link, subscribers)