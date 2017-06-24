# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlTwistPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):

        dbparms = dict(
            host = settings["MYSQL_HOST"],
            passwd = settings["MYSQL_PASSWORD"],
            user = settings["MYSQL_USER"],
            db = settings["MYSQL_DBNAME"],
            charset = "utf8",
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb",**dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self,failure,item,spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self,cursor,item):
        # 执行具体的插入d
        insert_sql, params = item.get_insert_sql
        cursor.execute(insert_sql,params)