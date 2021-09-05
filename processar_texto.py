#!/usr/bin/python3

import os
import sys
import math
import zlib
import sqlite3
import tempfile

# parameters
document = sys.argv[1]

# variables
database_file = "database.db"
stopwords_file = 'stopwords.txt'

# n-grams
ngram1 = {}
ngram2 = {}
ngram3 = {}

# black list
stopwords = []

print("Processando o arquivo '%s'" % document)

# expected file name format: "TITLE - AUTHOR.txt"
filename = document.split("/")[::-1][0]
title =  filename.split("-")[0].strip()
author = filename.split("-")[1].replace('.txt.preparado','').strip()

f = open(document, 'r')

def insert_document(author, title, countsum):
	docid = get_hash(author + title)
	con = sqlite3.connect(database_file)
	cur = con.cursor()
	cur.execute("INSERT INTO tb_document (docid, author, title, countsum) VALUES (%d, '%s', '%s', %d);" % (docid, author, title, countsum))
	con.commit()
	con.close()

def insert_tokens(ngram, n):
	con = sqlite3.connect(database_file)
	cur = con.cursor()
	
	for i in ngram:
		token = i
		tokid = get_hash(token)
		cur.execute('SELECT token FROM tb_token WHERE tokid = %d;' % (tokid));
		if cur.fetchone() is None:
			cur.execute("INSERT INTO tb_token (tokid, token, ng) VALUES (%d, '%s', %d);" % (tokid, token, n))

	con.commit()
	con.close()
	
def insert_document_tokens(ngram, n, countsum):
	con = sqlite3.connect(database_file)
	cur = con.cursor()
	
	document_tokens = []
	
	for i in ngram:
		token = i
		tokid = get_hash(token)
		docid = get_hash(author + title)
		count = ngram[i]
		tf = count / countsum
		document_tokens.append((tokid, docid, count, tf))
		
	cur.executemany("INSERT INTO tb_document_token (tokid, docid, count, tf) VALUES (?, ?, ?, ?);", document_tokens)

	con.commit()
	con.close()

def get_hash(text):
	# [Compare hashes in Python](https://gist.github.com/fabiolimace/507eac3d35900050eeb9772e5b1871ba)
	return (zlib.crc32(text.encode('utf-8')) << 32 | zlib.adler32(text.encode('utf-8'))) & 0x7fffffffffffffff # 2^63-1

def get_count_sum(ngram):
	sum = 0;
	for i in ngram:
		sum = sum + ngram[i]

for line in f:
	itens = line.split()
	
	## ngram 1
	for i in itens:
		if i in ngram1:
			ngram1[i] = ngram1[i] + 1
		else:
			ngram1[i] = 1
			
	## ngram 2
	temp = []
	for i in itens:
		temp.append(i)
		if len(temp) == 2:
			s = ' '.join(temp)
			if s in ngram2:
				ngram2[s] = ngram2[s] + 1
			else:
				ngram2[s] = 1
			temp = temp[1:]
			
	## ngram 3
	temp = []
	for i in itens:
		temp.append(i)
		if len(temp) == 3:
			s = ' '.join(temp)
			if s in ngram3:
				ngram3[s] = ngram3[s] + 1
			else:
				ngram3[s] = 1
			temp = temp[1:]
f.close()

# carregar as stop words
s = open(stopwords_file, 'r')
for line in s:
	word = line.strip()
	if len(word) > 0 and word[0] != '#':
		stopwords.append(word)
s.close()

# remover as stop words
ngram1 = { k:v for (k,v) in ngram1.items() if k not in stopwords}

# remover 2-grams que so ocorrem 1x
ngram2 = { k:v for (k,v) in ngram2.items() if not ngram2[k] < 2}

# remover 3-grams que so ocorrem 2x ou menos
ngram3 = { k:v for (k,v) in ngram3.items() if not ngram3[k] < 3}

# calculando quantidades de tokens por documento
countsum = 0
for i in ngram1:
	countsum = countsum + ngram1[i]
for i in ngram2:
	countsum = countsum + ngram2[i]
for i in ngram3:
	countsum = countsum + ngram3[i]

# inserir os tokens no banco
insert_document(author, title, countsum)
insert_tokens(ngram1, 1)
insert_tokens(ngram2, 2)
insert_tokens(ngram3, 3)
insert_document_tokens(ngram1, 1, countsum)
insert_document_tokens(ngram2, 2, countsum)
insert_document_tokens(ngram3, 3, countsum)


