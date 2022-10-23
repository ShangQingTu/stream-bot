# -*- coding: gbk -*-
import pandas as pd
import re

# ��CSV�ļ�ת��ΪHTML�ļ�
# ��ǩͷ
seg1 = '''<!DOCTYPE html><html lang="en"><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><head>
<meta charset="GBK">
<title>Title</title>
</head>
<body>
<h2 align="center">xiaomu_130b</h2>\n
<table border="1" align="center" width="70%">\n
<tr bgcolor="orange">\n'''

# �����ݴ���<table>��ǩ��
# ��β��ǩ
seg2 = "</tr>\n"
seg3 = "</table>\n</body>\n</html>"


# ������ݣ�����Ϊ�б�ȫ��������ʾ������һ��tr
def fill_data(locls):
    seg = '<tr><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>\n'.format(
        *locls)
    return seg


# ��ȡcsv�ļ��������б���
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
        answer = "�����ʦû�н��ң�Ҫ�������ʱ�ġ�"
    ls.append([origin_id, category, course, question, answer])
# д��HTML��
with open("202210222340_CoT_v2.3_glm_130B.html", "w") as fw:
    fw.write(seg1)
    # ��ӱ�ͷ��ls[0]�Ǳ�ͷ
    print(ls[0])
    fw.write(
        '<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n<th width="25%">{}</th>\n'.format(
            *ls[0]))
    fw.write(seg2)
    # ���ÿһ��
    for i in range(1, len(ls)):
        fw.write(fill_data(ls[i]))
    # ��ӽ�β��ǩ
    fw.write(seg3)
