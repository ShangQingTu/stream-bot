#!/usr/bin/env python
# coding=utf-8
from pymongo import MongoClient
from bson.objectid import ObjectId


class MongoDB(object):

    def __init__(self):
        # 连接MongoDB 方式一
        # self.client = MongoClient(host='localhost', port=27017)
        # 连接MongoDB 方式二
        self.client = MongoClient("mongodb://tsq:liverpool@localhost:27017/?authSource=chatbot")
        # 指定数据库
        self.db = self.client['chatbot']

    # 添加一条数据
    def add_one(self, data):
        # demo集合名字【表名】
        result = self.db.demo.insert_one(data)
        print(result)

    # 添加多条
    def add_many(self, data):
        result = self.db.demo.insert_many(data)
        print(result)

    # 获取一条数据
    def get_one(self):
        return self.db.demo.find_one()

    # 获取多条数据
    def get_many(self):
        return self.db.demo.find()

    # 通过条件获取
    def get_data(self, data):
        return self.db.demo.find(data)

    # 单条更新
    def up_one(self, query, data):
        result = self.db.demo.update_one(query, data)
        print(result)

    # 多条更新
    def up_many(self, query, data):
        result = self.db.demo.update_many(query, data, True)
        print(result)

    # 删除数据
    def del_one(self, query):
        result = self.db.demo.delete_one(query)
        print(result)

    def del_many(self, query):
        result = self.db.demo.delete_many(query)
        print(result)


if __name__ == '__main__':
    mdb = MongoDB()
    # 添加
    # mdb.add_one({"title": "java", "content": "教育"})
    # dt = [
    #     {"title": "c++", "content": "C++"},
    #     {"title": "php", "content": "PHP"},
    # ]
    # mdb.add_many(dt)

    # 获取
    # result = mdb.get_one()
    # print(result)
    # 获取多条
    # res = mdb.get_many()
    # for da in res:
    #     print(da)

    # 条件获取
    # query = {"title": "python"}
    # res = mdb.get_data(query)
    # for da in res:
    #     print(da)

    # 通过_id查询导入包from bson.objectid import ObjectId
    # query = {"_id": ObjectId("625410ab39d8d7eec64e2c90")}
    # res = mdb.get_data(query)
    # for da in res:
    #     print(da)

    # 更新一条
    # q = {"title": "php"}
    # d = {"$set": {"title": "c#", "content": "C#"}}
    # mdb.up_one(q, d)

    # 更新多条
    # q = {"title": "php"}
    # d = {"$set": {"title": "python", "content": "MongoDB"}}
    # mdb.up_many(q, d)

    # 删除单条
    # q = {"title": "c#"}
    # mdb.del_one(q)

    # 删除多条
    q = {"title": {"$regex": "c++"}}
    mdb.del_many(q)