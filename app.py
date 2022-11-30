import streamlit as st
from database import MongoDB, TEST_VERSION
from streamlit_chat import message
import os
import requests
import pandas as pd
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate
from models import build_prompt_for_glm, filter_glm
from fix_his_questions import version2api, merge_chat_history

st.set_page_config(
    page_title="教育领域对话",
    page_icon=":robot:"
)
init_history_num = 4
turn_utt_num = 6
API_URL = version2api[TEST_VERSION]
mdb = MongoDB(collection_name=TEST_VERSION)


def query(payload):
    if TEST_VERSION == "glm_base":
        prompt_str = build_prompt_for_glm(payload)
        payload = {"query": prompt_str, "limit": 30}
        response = requests.post(API_URL, json=payload)
        raw_str = response.json()['data']
        final_response = filter_glm(raw_str)
        return final_response
    elif TEST_VERSION == "cpm2":
        prompt_str = build_prompt_for_glm(payload, mask_token='')
        payload = {"query": prompt_str, "limit": 30}
        response = requests.post(API_URL, json=payload)
        final_response = response.json()
        return final_response
    elif TEST_VERSION == "glm130b_base":
        prompt_str = build_prompt_for_glm(payload, mask_token='', past_num=4)
        if len(prompt_str) > 512:
            prompt_str = prompt_str[-512:]
        payload = {
            "contexts": [prompt_str]
        }
        print(f"send payload is {payload}")
        response = requests.post(API_URL, json=payload)
        raw_str_lst = response.json()['outputs']
        print(f"raw_str_lst is {raw_str_lst}")
        _lst = [filter_glm(raw_str) for raw_str in raw_str_lst]
        _lst = [''.join(res.split()) for res in _lst]
        return _lst[0]
    elif TEST_VERSION == "cdail_gpt":
        glm_api = "http://0.0.0.0:9600/cdial"
        _payload = {
            "question": payload["text"],
            "chat_history": merge_chat_history(payload["past_user_inputs"], payload["generated_responses"])
        }
        print(f"send payload is {_payload}")
        response = requests.post(glm_api, json=_payload)
        # print(response.json()["answer"])
        # print("payload", payload)
        # _send = {"question": payload["text"]}
        # print("_send", _send)
        # print("API_URL", API_URL)
        # response = requests.post(API_URL, json=_send)
        print("response", response)
        print("response.json()", response.json())
        raw_str = response.json()['answer']
        return "".join(raw_str.split())
    elif TEST_VERSION == "eva":
        glm_api = "http://0.0.0.0:9601/eva"
        _payload = {
            "question": payload["text"],
            "chat_history": merge_chat_history(payload["past_user_inputs"], payload["generated_responses"])
        }
        print(f"send payload is {_payload}")
        response = requests.post(glm_api, json=_payload)
        print("response", response)
        print("response.json()", response.json())
        raw_str = response.json()['answer']
        return "".join(raw_str.split())
    elif TEST_VERSION == "gpt3":
        glm_api = "http://0.0.0.0:9602/gpt"
        _payload = {
            "question": payload["text"],
            "chat_history": merge_chat_history(payload["past_user_inputs"], payload["generated_responses"])
        }
        print(f"send payload is {_payload}")
        response = requests.post(glm_api, json=_payload)
        raw_str = response.json()['answer']
        return "".join(raw_str.split())
    else:
        response = requests.post(API_URL, json=payload)
        return response.json()


def get_text():
    input_text = st.text_input("学生用户: ", key="input")
    return input_text


def get_fix_history(course_name):
    v1_csv_path = os.path.join('/data/tsq/xiaomu', f'glm130b_base_v3_history_question.csv')
    v1_df = pd.read_csv(v1_csv_path, header=None)
    st.session_state['generated'] = []
    st.session_state['past'] = []
    pos = 0
    for index, row in v1_df.iterrows():
        if index == 0:
            continue
        course = row[3]
        question = row[4]
        answer = row[5]
        if course != course_name:
            continue
        if pos < st.session_state['fix_history_pos']:
            pos += 1
            continue
        st.session_state['past'].append(question)
        if type(answer) != str:
            answer = ""
        # print("answer: ", answer)
        st.session_state['generated'].append(answer)
        if len(st.session_state['past']) >= init_history_num:
            st.session_state['fix_history_pos'] += init_history_num
            break


def main_page():
    st.header(f"对话测试版本:{TEST_VERSION}")
    st.markdown("当前的场景是[学堂在线](https://www.xuetangx.com/)上的教育对话系统")
    st.markdown("您可以先阅读[测试文档](https://kvbpkpddff.feishu.cn/docx/FY2GdXFHtoSQ1dxhrjGc2BsBn6b)")
    course_name = st.selectbox(
        '选择您的科目',
        ('逻辑学概论', '大学物理1', '有机化学', '算法设计与分析', '经济学原理', '马克思主义基本原理', '思想道德修养与法律基础', '体育与社会', 'C++语言程序设计基础', '数据结构（上）',
         '电路原理', '软件工程', '中国近现代史纲要', '唐宋词鉴赏', '毛泽东思想与中国特色社会主义理论体系概论', '不朽的艺术：走进大师与经典', '新闻摄影', '生活英语读写', '日语与日本文化',
         '现代生活美学——插画之道')
    )
    st.write("您所在的科目是", course_name)
    if 'course_name' not in st.session_state:
        # new user!
        st.session_state['course_name'] = course_name
        st.session_state['fix_history_pos'] = 0
    elif st.session_state['course_name'] != course_name:
        # new course!
        st.session_state['course_name'] = course_name
        st.session_state['fix_history_pos'] = 0
        get_fix_history(course_name)
    # new user!
    if 'generated' not in st.session_state or 'past' not in st.session_state:
        get_fix_history(course_name)
    user_input = get_text()
    # print(st.session_state['fix_history_pos'])
    st.write(
        f"您在此课程已经聊了{st.session_state['fix_history_pos'] // init_history_num - 1}轮, 每轮{turn_utt_num}句对话,在每轮结束时,会有新的{init_history_num}句对话背景")
    st.write("每轮的最后一句对话不会打出,但会存在数据库里,每轮的第一句对话后轮数会更新～")
    st.write("当您看到没有新的对话背景的时候,这门课就聊完了～")

    if user_input:
        output = query({
            "past_user_inputs": st.session_state.past,
            "generated_responses": st.session_state.generated,
            "text": user_input,
        })
        # add into db
        id = len(list(mdb.get_many()))
        record = {
            "id": id,  # 自增
            "user_name": f"{st.session_state['name']}",  # 用户名
            "query": f"{user_input}",  # 用户的输入
            "answer": f"{output}",  # 系统的回复
            "course_name": f"{course_name}",  # 课程名
        }
        # log
        mdb.add_one(record)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)

    if st.session_state['generated']:
        if len(st.session_state['past']) >= init_history_num + turn_utt_num:
            # new turn !
            get_fix_history(course_name)
        # print messages
        for i in range(len(st.session_state['generated']) - 1, -1, -1):
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))


# Loading config file
with open('/home/tsq/stream-bot/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Creating the authenticator object
authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# creating a login widget
name, authentication_status, username = authenticator.login('Login', 'main')
if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main')
    st.write(f'欢迎! *{st.session_state["name"]}*')
    main_page()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')
