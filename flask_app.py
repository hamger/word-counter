#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request, jsonify
import json
import pymysql
from db_connection import connect

app = Flask(__name__)

from functools import wraps
from flask import make_response
import html_downloader, html_parser


# 爬取网页信息
def carw(url):
    text = html_downloader.download(url)
    return html_parser.prase(text)


# 规定接口的数据返回格式
def baseReturn(data='', msg='OK', success=True):
    json_data = json.dumps({'data': data, 'success': success, 'msg': msg})
    return json_data


# 允许跨域访问
def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        allow_headers = "Referer,Accept,Origin,User-Agent"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst

    return wrapper_fun


# 查询所有书名的列表
@app.route('/book', methods=['get'])
@allow_cross_domain
def getbook():
    db = connect()
    cursor = db.cursor()
    sql = "select table_name from information_schema.tables where table_schema='words'"
    cursor.execute(sql)
    data = cursor.fetchall()
    db.close()
    list = []
    for x in data:
        if not str(x[0]) == 'my_words':
            list.append(str(x[0]))
    return baseReturn(list)


# 列表查询
@app.route('/list', methods=['get'])
@allow_cross_domain
def getList():
    bookName = request.args.get('bookName')
    proFrom = request.args.get('proFrom')
    proTo = request.args.get('proTo')
    if proFrom == None:
        proFrom = 0
    if proTo == None:
        proTo = 10000
    db = connect()
    cursor = db.cursor()
    # 获取 过滤掉 my_words 表中的单词，且指定出现概率范围下的，倒序排列的数据
    sql = 'select * from ' + bookName + ' where (select count(1) as num from my_words where my_words.word =' + bookName + '.word) = 0 and probability >= %s and probability <= %s ORDER BY probability DESC'

    cursor.execute(sql,
                   (request.args.get('proFrom'), request.args.get('proTo')))
    data = cursor.fetchall()
    db.close()
    return baseReturn(data)


# 过滤单词
@app.route('/filterWord', methods=['post'])
@allow_cross_domain
def filterWord():
    words = json.loads(request.get_data())
    db = connect()
    for word in words:
        # 获取会话指针
        with db.cursor() as cursor:
            # 创建一条 sql 语句，如果表名或字段名中带 - ，需要使用 ` 包裹
            sql = "REPLACE INTO my_words (word, type) VALUES(%s, %s)"
            # 执行sql语句
            cursor.execute(sql, (word, 'normal'))
            # 提交
            db.commit()
    db.close()
    return baseReturn('', '加入成功')


# 过滤列表查询
@app.route('/wordList', methods=['get'])
@allow_cross_domain
def getWordList():
    word = request.args.get('word')
    type_ = request.args.get('type')
    # 字符串需要用单引号包裹
    sql = "select * from my_words where word like '" + word + "%' and type like '" + type_ + "%'"
    db = connect()
    # 游标设置为字典类型
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute(sql)
    data = cursor.fetchall()
    db.close()
    return baseReturn(data)


# 更新过滤表中单词
@app.route('/fixWord', methods=['post'])
@allow_cross_domain
def fixWord():
    try:
        word = json.loads(request.get_data())
        db = connect()
        cursor = db.cursor()
        sql = "replace into my_words (word, phonetic, meaning, type) values(%s, %s, %s, %s)"
        # word.word 报错，应该使用 word['word']
        cursor.execute(
            sql,
            (word['word'], word['phonetic'], word['meaning'], word['type']))
        db.commit()
        db.close()
        return baseReturn('', '更新成功')
    except ValueError:
        return baseReturn(ValueError, '更新失败', False)


# 删除过滤表中单词
@app.route('/delWord', methods=['post'])
@allow_cross_domain
def delWord():
    try:
        word = json.loads(request.get_data())
        db = connect()
        cursor = db.cursor()
        # 使用了 %s，就不能用引号包裹
        sql = "delete from my_words where word=%s"
        cursor.execute(sql, (word['word']))
        db.commit()
        db.close()
        return baseReturn('', '删除成功')
    except ValueError:
        return baseReturn(ValueError, '删除失败', False)


# 查询单词
@app.route('/checkWord', methods=['get'])
@allow_cross_domain
def checkWord():
    word = request.args.get('word')
    print(word)
    url = 'http://dict.youdao.com/search?q=' + word
    data = carw(url)
    print(data)
    return baseReturn(data, '查询成功')


if __name__ == '__main__':
    # 开启热更新
    app.debug = True
    # 指定 IP 和 端口
    app.run(host='127.0.0.1', port=5001)
