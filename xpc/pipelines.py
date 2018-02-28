# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql

class MysqlPipeline(object):
    def __init__(self):
        self.conn = None
        self.cur = None

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='rock1204',
            db='xpc',
            charset='utf8',
        )
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        if not hasattr(item, 'table_name'):
            return item
        # cols, values = zip(*[(col, item[col]) for col in item.keys()])
        cols, values = zip(*item.items())

        sql = "INSERT INTO `%s`(%s) VALUES (%s);" % (item.table_name, ','.join(cols), ','.join(['%s'] * len(values)))
        # 防止sql注入: execute方法会将特殊字符转义,如果字符中具有sql语句会被注入
        # 将values列表作为参数传入可以防止被转义
        self.cur.execute(sql, values)
        print(sql)
        print(values)
        self.conn.commit()
        return item