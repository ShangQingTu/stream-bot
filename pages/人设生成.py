import streamlit as st
from database import MongoDB
from streamlit_chat import message
import requests
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate
from models import build_prompt_for_glm, filter_glm
from fix_his_questions import version2api

st.set_page_config(
    page_title="教育领域对话",
    page_icon=":robot:"
)
init_history_num = 4
turn_utt_num = 6
API_VERSION = 'glm_base'
API_URL = version2api[API_VERSION]
mdb = MongoDB(collection_name=f'persona_{API_VERSION}')
type2tags = {
    "introduction": [0, 1, 2, 3],
    # "emotion": ['惊喜', '激动', '愤怒', '骄傲', '伤心', '工作上的烦恼', '感激'],
    "emotion": ['surprised', 'excited', 'angry', 'proud', 'sad', 'annoyed', 'grateful'],
    "logic": ['compare', 'why', 'how', 'enumerate', 'recommend'],
}


def query(payload):
    background = 'Q是一个正在学堂在线慕课网站上学习的学生,他需要情感帮助,小木正在开导他'
    if API_VERSION == "glm_base":
        prompt_str = build_prompt_for_glm(payload, background=background, init=False)
        payload = {"query": prompt_str, "limit": 30}
        response = requests.post(API_URL, json=payload)
        raw_str = response.json()['data']
        final_response = filter_glm(raw_str)
        return final_response
    elif API_VERSION == "glm130b_base":
        prompt_str = build_prompt_for_glm(payload, mask_token='', past_num=4, init=False)
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
    else:
        response = requests.post(API_URL, json=payload)
        return response.json()


def query_candidates(payload, sample_times=5):
    res = []
    if st.session_state['type'] == 'introduction':
        persona_name = st.session_state['persona_name']
        res = [f'你好,我是{persona_name}小木', '初始化介绍请标注者帮小木写', '其他']
    else:
        for i in range(sample_times):
            res.append(query(payload))
    return res


def get_text_with_tag():
    q_type, tag = st.session_state['type_tag_lst'][st.session_state['type_tag_pos']]
    if q_type == 'introduction':
        user_q_prompt = f'现在是学生与小木最初见面后的第*{tag}*句对白'
    elif q_type == 'emotion':
        user_q_prompt = f'学生想说一句带有*{tag}*情感的话'
    else:
        user_q_prompt = f'学生想问一个*{tag}*的逻辑问题'
    st.markdown(user_q_prompt)
    # 未来可以换成用模型生成
    input_text = st.text_input("学生用户: ", key="input")
    return input_text


def get_introduction(persona_name):
    st.session_state['generated'] = []
    st.session_state['past'] = []
    type_tag_lst = []
    for k, v_lst in type2tags.items():
        for v in v_lst:
            type_tag_lst.append((k, v))
    st.session_state['type_tag_lst'] = type_tag_lst
    st.session_state['type_tag_pos'] = 0


def main_page():
    st.header(f"对话测试版本:{API_VERSION}")
    st.markdown("当前的场景是[学堂在线](https://www.xuetangx.com/)上的教育对话系统小木,它现在具有特定的**人设**")
    st.markdown("您可以先阅读[测试文档](https://kvbpkpddff.feishu.cn/docx/FY2GdXFHtoSQ1dxhrjGc2BsBn6b)")
    persona_name = st.selectbox('选择小木的人设', ('学姐', '学长', '学弟', '学妹', '老师'))
    st.write("小木当前的人设是", persona_name)
    if 'persona_name' not in st.session_state:
        # new user!
        st.session_state['persona_name'] = persona_name
        st.session_state['fix_history_pos'] = 0
    elif st.session_state['persona_name'] != persona_name:
        # new persona_name!
        st.session_state['persona_name'] = persona_name
        st.session_state['fix_history_pos'] = 0
        get_introduction(persona_name)
    # new user!
    if 'generated' not in st.session_state or 'past' not in st.session_state:
        get_introduction(persona_name)
    # 规定用户的请求类型
    user_input = get_text_with_tag()
    # print(st.session_state['fix_history_pos'])

    if user_input:
        candidates = query_candidates({
            "past_user_inputs": st.session_state.past,
            "generated_responses": st.session_state.generated,
            "text": user_input,
        })
        _output = st.selectbox('请选择符合小木的人设的回答', candidates)
        st.markdown(_output)
        output = st.text_input("小木最终回答(您可以修改生成结果后填入): ", key="input")
        # add into db
        if output:
            _id = len(list(mdb.get_many()))
            record = {
                "id": _id,  # 自增
                "persona": f"{persona_name}",  # persona
                "user_name": f"{st.session_state['name']}",  # 用户名
                "type": f"{st.session_state['type']}",  # 问题的类型
                "tag": f"{st.session_state['tag']}",  # 标签(比如，情绪的细分类,逻辑类型等)
                "query": f"{user_input}",  # 用户的输入
                "answer": f"{output}",  # 系统的回复
                "candidates": f"{candidates}",  # glm在sample中产生的候选
            }
            # log
            mdb.add_one(record)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)

    if st.session_state['generated']:
        st.session_state['type_tag_pos'] += 1
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
