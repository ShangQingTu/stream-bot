# -*- coding: gbk -*-
import pandas as pd
import re

# 将CSV文件转化为HTML文件
# 标签头
seg1 = '''<!DOCTYPE html><html lang="en"><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><head>
<meta charset="GBK">
<title>Title</title>
</head>
<body>
<h2 align="center">xiaomu_130b</h2>\n
<table border="1" align="center" width="70%">\n
<tr bgcolor="orange">\n'''

# 将数据存入<table>标签中
# 结尾标签
seg2 = "</tr>\n"
seg3 = "</table>\n</body>\n</html>"


# 填充数据，参数为列表，全部居中显示，返回一个tr
def fill_data(locls):
    seg = '<tr><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>\n'.format(
        *locls)
    return seg


# 获取csv文件，存入列表中
df = pd.read_csv("202210222340_CoT_v2.3_glm_130B.csv")
print(df)
ls = [["origin_id", "category", "course", "question", "answer"]]
for index, row in df.iterrows():
    origin_id = row[1]
    category = row[2]
    course = row[3]
    question = row[4]
    answer = row[5]
    print(answer)
    try:
        answer = re.sub("\n", "<br>", answer)
    except TypeError:
        answer = "这个老师没有教我，要不你问问别的～"
    ls.append([origin_id, category, course, question, answer])
# 写入HTML中
with open("202210222340_CoT_v2.3_glm_130B.html", "w") as fw:
    fw.write(seg1)
    # 添加表头：ls[0]是表头
    print(ls[0])
    fw.write(
        '<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n'.format(
            *ls[0]))
    fw.write(seg2)
    # 添加每一行
    for i in range(1, len(ls)):
        fw.write(fill_data(ls[i]))
    # 添加结尾标签
    fw.write(seg3)
