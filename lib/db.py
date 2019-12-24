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

sys.path.append('.')
import regex

# db.py : 데이터베이스와 관련된 기능들

#DB에 연결
def connect():
	con = sqlite3.connect('data.db')
	cur = con.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS youtubers(name text, link text, subscribers int);")
	cur.execute("CREATE TABLE IF NOT EXISTS videos(youtuber_link text, title text, link text, visit int, keyword text);")
	cur.execute("CREATE TABLE IF NOT EXISTS unvisited(link text, keyword text);")
	return con, cur

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

#unvisited 동영상 중 하나를 가져온 후 DB에서 삭제함
def getChannel():
	con, cur = connect()
	sql = 'SELECT * FROM youtubers ORDER BY RANDOM() limit 1'
	cur.execute(sql)
	row = cur.fetchall()
	return row[0]

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

def saveVideo(youtuberLink, title, link, visit, keyword):
	if doesExist('videos', 'link', link):
		return
	print('Saving video... : ' + link)
	visit = regex.visitorsToInteger(visit)
	con, cur = connect()
	cur.execute("INSERT INTO videos VALUES(?, ?, ?, ?, ?)", (youtuberLink, title, link, visit, keyword))
	con.commit()
	con.close()

def saveYoutuber(name, link, subscribers):
	if doesExist('youtubers', 'link', link):
		return
	print('Saving youtuber... : ' + link)
	con, cur = connect()
	subscribers = regex.subscribersToInteger(subscribers)
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