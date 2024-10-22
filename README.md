# stream-bot
chat-bot front page build on streamlit





# Requirements

```
pip install streamlit-chat 
```

```
pip install streamlit
```



# Start server

First activate:

```
conda activate blink37
```

On our 32 server, you can enter`/home/tsq/stream-bot`

run this to start mongodb  server at`/home/tsq/mongodb/bin/`:

```
nohup mongod --dbpath ./ &
```

run this to start the web page :

```
nohup streamlit run app.py > streamlit_server_922.log &
```



Everyone can view the page at http://103.238.162.32:8501/



# For Mongo

```
./mongo
```

Create Collection:

```
use chatbot
db.createCollection("glm_base")
```

在 MongoDB 中，你不需要创建集合。当你插入一些文档时，MongoDB 会自动创建集合。



Each data should be like:

```
{
	"id":"", #自增
	"user_name":"",#用户名
	"query":"",#用户的输入
	"answer":"",#系统的回复
	"course_name":"",#课程名
}
```

检查一下是不是链接咯：

```
import pymongo
client = pymongo.MongoClient("mongodb://tsq:liverpool@localhost:27017/?authSource=edubot")
db = client['edubot']
collection = db['glm_base']
collection.insert_one({"title":"你好"})
collection.find_one()
```

返回的

```
{'code': 0, 'data': \"[CLS]|USER:晚安|BOT:{'code': 0, 'data': '[CLS]|USER:晚安|BOT:[gMASK]<|startofpiece|>|SERVER: /DATE:[DATE_LONG=2020-03-25]|PASS:[PASSWORD=GET', 'cost': 1.11320161819458, 'msg': 'okay'}|USER:你好|BOT:[gMASK]<|startofpiece|>{'site: node|HOST: 'GOD, Helios', 'path: '<|startofpiece|>'${GOD, Helios}', 'username: 'Jim', 'password: 'jd'}\", 'cost': 2.3700530529022217, 'msg': 'okay'}
```

