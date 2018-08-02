# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
import MySQLdb
import MySQLdb.cursors
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    #自定义Json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()

#
# class MysqlPipeline(object):
#     def __init__(self):
#         self.conn = MySQLdb.connect('39.108.226.91', 'thorne', 'Assassin779!8', 'test', charset='utf8', use_unicode=True)
#         self.cursor = self.conn.cursor()
#
#     def process_item(self, item, spider):
#         insert_sql = "insert into article (title,url_object_id) VALUES ('{0}','{1}')".format(item['title'],item['url_object_id'])
#         print(insert_sql)
#         self.cursor.execute(insert_sql)
#         self.conn.commit()

class MysqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):

        dbparms = dict(
                        host = settings['MYSQL_HOST'],
                        db = settings['MYSQL_DBNAME'],
                        user = settings['MYSQL_USER'],
                        passwd = settings['MYSQL_PASSWORD'],
                        charset = 'utf8',
                        cursorclass = MySQLdb.cursors.DictCursor,
                        use_unicode = True
                        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将数据入库变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)

    def do_insert(self, cursor, item):
        insert_sql = "insert into article (title,url_object_id) VALUES ('{0}','{1}')".format(item['title'],item['url_object_id'])
        cursor.execute(insert_sql)

    def handle_error(self, failure, item, spider):
        #处理异步插入异常
        print(failure)



class JsonExporterPipeline(object):
    #调用scrapy提供的JsonExporter导出Json文件
    def __init__(self):
        self.file = open('articleexporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()
    def close_spider(self):
        self.exporter.finish_exporting()
        self.file.close()
    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class ArtilceImagePipline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for ok, value in results:
            image_file_path = value['path']
        item['front_image_path'] = image_file_path
        return item
