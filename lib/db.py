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
	return con

def connectUpdater(dbName):
	con = sqlite3.connect(dbName)
	cur = con.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS youtubers_updated(name text, link text, subscribers int);")
	return con

def removeYoutuber(con, dbName):
	cur = con.cursor()
	sql = "SELECT link from youtubers ORDER BY RANDOM() limit 1"
	cur.execute(sql)
	row = cur.fetchall()[0]
	link = row[0]
	sql = "DELETE FROM youtubers WHERE link = '{}'".format(link)
	cur.execute(sql)
	con.commit()
	return link


def doesExist(con, table, name, value, isString=True):
	cur = con.cursor()
	sql = ''
	if isString:
		sql = "SELECT count(*) FROM {} WHERE {} = '{}'".format(table, name, value)
	else:
		sql = "SELECT count(*) FROM {} WHERE {} = {}".format(table, name, value)
	print(sql)
	cur.execute(sql)
	count = cur.fetchone()[0]
	return count > 0

def getCount(con, table):
	cur = con.cursor()
	sql = "SELECT count(*) FROM {}".format(table)
	cur.execute(sql)
	count = cur.fetchone()[0]
	return count

#unvisited 동영상 중 하나를 가져온 후 DB에서 삭제함
def getChannel(con):
	cur = connect()
	sql = 'SELECT * FROM youtubers ORDER BY RANDOM() limit 1'
	cur.execute(sql)
	row = cur.fetchall()
	return row[0]

def getUnvisited(con):
	try:
		cur = con.cursor()
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

def saveVideo(con, youtuberLink, title, link, visit, keyword):
	if doesExist(con, 'videos', 'link', link):
		return
	print('Saving video... : ' + link)
	visit = regex.visitorsToInteger(visit)
	cur = con.cursor()
	cur.execute("INSERT INTO videos VALUES(?, ?, ?, ?, ?)", (youtuberLink, title, link, visit, keyword))
	con.commit()

def saveYoutuber(con, name, link, subscribers):
	if doesExist(con, 'youtubers', 'link', link):
		return
	print('Saving youtuber... : ' + link)
	cur = con.cursor()
	subscribers = regex.subscribersToInteger(subscribers)
	cur.execute("INSERT INTO youtubers VALUES(?, ?, ?)", (name, link, subscribers))
	con.commit()

def saveUnvisited(con, link, keyword):
	if doesExist(con, 'unvisited', 'link', link) or doesExist(con, 'videos', 'link', link):
		return
	print('Saving unvisited... : ' + link)
	cur = con.cursor()
	cur.execute("INSERT INTO unvisited VALUES(?, ?)", (link, keyword))
	con.commit()