import streamlit as st
from database import MongoDB
from streamlit_chat import message
import requests
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate
from models import build_prompt_for_glm

st.set_page_config(
    page_title="教育领域对话",
    page_icon=":robot:"
)
API_URL = "http://localhost:9628/glm"
TEST_VERSION = "glm_base"
mdb = MongoDB(collection_name=TEST_VERSION)


def query(payload):
    if TEST_VERSION == "glm_base":
        prompt_str = build_prompt_for_glm(payload)
        payload = {"query": prompt_str, "limit": 30}
    response = requests.post(API_URL, json=payload)
    return response.json()


def get_text():
    input_text = st.text_input("学生用户: ", "你好", key="input")
    return input_text


def main_page():
    st.header(f"对话测试版本:{TEST_VERSION}")
    st.markdown("当前的场景是[学堂在线](https://www.xuetangx.com/)上的教育对话系统")
    st.markdown("您可以先阅读[测试文档]()")
    course_name = st.selectbox(
        '选择您的科目',
        ('逻辑学概论', '大学物理1', '有机化学', '算法设计与分析', '经济学原理', '马克思主义基本原理', '思想道德修养与法律基础', '体育与社会', 'C++语言程序设计基础', '数据结构（上）',
         '电路原理', '软件工程', '中国近现代史纲要', '唐宋词鉴赏', '毛泽东思想与中国特色社会主义理论体系概论', '不朽的艺术：走进大师与经典', '新闻摄影', '生活英语读写', '日语与日本文化',
         '现代生活美学——插画之道')
    )
    st.write("您所在的科目是", course_name)

    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []

    user_input = get_text()

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

        for i in range(len(st.session_state['generated']) - 1, -1, -1):
            message(st.session_state["generated"][i], key=str(i))
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')


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
