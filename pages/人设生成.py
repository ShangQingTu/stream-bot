import streamlit as st
from database import MongoDB
from streamlit_chat import message
import requests
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate
from models import build_prompt_for_glm, filter_glm
from fix_his_questions import version2api, type2tags, personas
import pandas as pd
import time

st.set_page_config(
    page_title="教育领域对话",
    page_icon=":robot:"
)
m = st.markdown("""
<style>div.stButton > button:first-child {
    background-color: #0099ff;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #00ff00;
    color:#ff0000;
    }
</style>""", unsafe_allow_html=True)
init_history_num = 4
turn_utt_num = 6
API_VERSION = 'glm_base'
API_URL = version2api[API_VERSION]
mdb = MongoDB(collection_name=f'persona_{API_VERSION}')
pid_mdb = MongoDB(collection_name=f'pid_list_{API_VERSION}')


def add_version_persona(payload):
    if 'version_qa_df' not in st.session_state:
        return payload
    # 添加版本人格的对话历史
    version_qa_df = st.session_state['version_qa_df']
    # add all introduction and emotions
    query_lst = list(version_qa_df["query"])
    answer_lst = list(version_qa_df["answer"])
    payload["past_user_inputs"] = query_lst + payload["past_user_inputs"]
    payload["generated_responses"] = answer_lst + payload["generated_responses"]
    return payload


def query(payload):
    background = 'Q是一个正在学堂在线慕课网站上学习的学生,他需要情感帮助,小木正在开导他'
    payload = add_version_persona(payload)
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
    print("query_candidates is called")
    res = []
    if st.session_state['type'] == 'introduction':
        persona_name = st.session_state['persona_name']
        res = [f'你好,我是{persona_name}小木', '初始化介绍请标注者帮小木写', '其他', f"{time.strftime('%Y-%m-%d %H:%M:%S')}"]
    else:
        for i in range(sample_times):
            res.append(query(payload))
    return res


def get_text_with_tag():
    pos_lst = [i for i in st.session_state['type_tag_lst']]
    select_pos = st.selectbox("您想跳转到哪个对话类型?", pos_lst)
    q_type, tag = st.session_state['type_tag_lst'][st.session_state['type_tag_pos']]
    if st.button("确定跳转"):
        q_type, tag = select_pos
        for i, _pos in enumerate(st.session_state['type_tag_lst']):
            if _pos == select_pos:
                st.session_state['type_tag_pos'] = i
                break
    st.session_state['type'] = q_type
    st.session_state['tag'] = tag
    if q_type == 'introduction':
        user_q_prompt = f'现在是学生与小木最初见面后的第**{tag + 1}**句对白'
    elif q_type == 'emotion':
        user_q_prompt = f'学生想说一句带有**{tag}**情感的话'
    else:
        user_q_prompt = f'学生想问一个**{tag}**的逻辑问题'
    label_prompt = "请在每次点击完`小木说好了`后**删除**学生输入框中的内容,并按下**回车**,就可以更新学生的对话意图"
    st.markdown(f"#### 学生对话意图: {user_q_prompt}")
    st.markdown(label_prompt)
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


def get_version_qa_df(pid_lst):
    # select df that has the _id in pid_lst
    res = mdb.get_many()
    res_lst = list(res)
    final = []
    for res in res_lst:
        res['_id'] = str(res['_id'])
        if res['_id'] in pid_lst:
            final.append(res)
    df = pd.DataFrame(final)
    return df


def set_persona():
    persona_name = st.selectbox('选择小木的人设', personas)
    # 　可以选择的vid
    vid_lst = []
    res_lst = list(pid_mdb.get_many())
    # 　这里开销有些大,或许以后等数据多了可以做一个dict的cache
    vid2pid_lst = {}
    for res in res_lst:
        vid = str(res['vid'])
        pid_lst = res['pid_list']
        version_persona = vid.split("_")[0]
        if version_persona == persona_name:
            vid_lst.append(vid)
            vid2pid_lst[vid] = pid_lst
    if vid_lst:
        vid = st.selectbox('选择小木的人设版本', [""] + vid_lst)
        if vid:
            _persona, _user, _num = vid.split("_")
            person_str = f"> 小木是由*{_user}*创建的{_persona}人格**{_num}**号机"
            st.markdown(person_str)
            # 　选完之后更新state
            st.session_state['version_qa_df'] = get_version_qa_df(vid2pid_lst[vid])
    
    return persona_name


def main_page():
    st.header(f"对话测试版本:{API_VERSION}")
    st.markdown("当前的场景是[学堂在线](https://www.xuetangx.com/)上的教育对话系统小木,它现在具有特定的**人设**")
    st.markdown("您可以先阅读[测试文档](https://kvbpkpddff.feishu.cn/docx/FY2GdXFHtoSQ1dxhrjGc2BsBn6b)")
    # 　设置人设　与　默认版本
    persona_name = set_persona()
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
    if st.button('学生说好了', key="stu"):
        # choice_st = st.empty()
        candidates = query_candidates({
            "past_user_inputs": st.session_state.past,
            "generated_responses": st.session_state.generated,
            "text": user_input,
        })
        st.markdown('请选择符合小木的人设的回答:')
        for _output in candidates:
            # chosen_st = st.empty()
            st.markdown("- " + _output)
        st.session_state['candidates'] = candidates
    # after_query_st = st.empty()
    output = st.text_input("小木最终回答(您可以修改生成结果后填入): ", key="output")
    # add into db
    if st.button('小木说好了', key="final"):
        _time = time.strftime('%Y-%m-%d %H:%M:%S')
        _id = f"{len(list(mdb.get_many()))}_{_time}"
        record = {
            "id": _id,  # 自增
            "persona": f"{persona_name}",  # persona
            "user_name": f"{st.session_state['name']}",  # 用户名
            "type": f"{st.session_state['type']}",  # 问题的类型
            "tag": f"{st.session_state['tag']}",  # 标签(比如，情绪的细分类,逻辑类型等)
            "query": f"{user_input}",  # 用户的输入
            "answer": f"{output}",  # 系统的回复
            "candidates": f"{st.session_state['candidates']}",  # glm在sample中产生的候选
        }
        # log
        st.session_state['type_tag_pos'] += 1
        mdb.add_one(record)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)

    if st.session_state['generated']:
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
