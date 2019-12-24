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

# regex.py : 정규표현식 관련 기능들

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

def visitorsToInteger(text):
	p = re.compile('[0-9]+.*[0-9]')
	m = p.search(text)
	if m == None:
		return 0
	text = m.group()
	p = re.compile('^(\d+|\d{1,3}(,\d{3})*)(\.\d+)?$')
	m = p.search(text)
	if m == None:
		return 0
	text = m.group()
	print
	return int(text.replace(',', ''))