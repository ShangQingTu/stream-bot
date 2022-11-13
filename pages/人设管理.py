import streamlit as st
from database import MongoDB
import pandas as pd
from bson.objectid import ObjectId
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate
from fix_his_questions import version2api, type2tags, personas

super_users = ['tsq22']
st.set_page_config(
    page_title="人设管理",
    page_icon=":shark:"
)
API_VERSION = 'glm_base'
mdb = MongoDB(collection_name=f'persona_{API_VERSION}')
pid_mdb = MongoDB(collection_name=f'pid_list_{API_VERSION}')


def load_persona_db():
    res = mdb.get_many()
    res_lst = list(res)
    for res in res_lst:
        res['_id'] = str(res['_id'])
        res['id'] = str(res['id'])
    df = pd.DataFrame(res_lst)
    return df


def show_db(option_persona, option_type):
    df = load_persona_db()
    # Boolean to resize the dataframe, stored as a session state variable
    # st.checkbox("Use container width", value=False, key="use_container_width")
    # Display the dataframe and allow the user to stretch the dataframe
    # across the full width of the container, based on the checkbox value
    if option_persona != 'all':
        df = df[df["persona"] == option_persona]
    if option_type != 'all':
        df = df[df["type"] == option_type]
    st.dataframe(df)
    return len(df)


def del_db(to_delete_lst):
    df = load_persona_db()
    del_df = df.iloc[to_delete_lst, :]
    for object_id in del_df['_id']:
        query = {"_id": ObjectId(object_id)}
        mdb.del_one(query)


def select_db(option_persona, to_select_lst):
    df = load_persona_db()
    sel_df = df.iloc[to_select_lst, :]
    pid_lst = [object_id for object_id in sel_df['_id']]
    # 建立version的id
    num_op = 0
    res = pid_mdb.get_many()
    res_lst = list(res)
    res_vid_lst = []
    for res in res_lst:
        res_vid = str(res['vid'])
        if res_vid not in res_vid_lst:
            res_vid_lst.append(res_vid)
    print(f"res_vid_lst, {res_vid_lst}")
    while f"{option_persona}_{name}_{num_op}" in res_vid_lst:
        num_op += 1
    print(f"pid_lst {pid_lst}")
    vid = f"{option_persona}_{name}_{num_op}"
    version_data = {"vid": vid, "pid_list": pid_lst}
    pid_mdb.add_one(version_data)
    return vid


def main_page():
    st.header(f"对话版本:{API_VERSION}")
    # 根据条件显示
    option_persona = st.selectbox(
        '人设类型',
        personas)
    types = ['all'] + list(type2tags.keys())
    option_type = st.selectbox(
        '问题类型',
        types)
    df_len = show_db(option_persona, option_type)
    # 使用多选　和　delete button实现删除
    to_delete_lst_str = st.text_input("需要删除的数据行号(空格隔开)", key="to_delete")
    if st.button("确定删除"):
        to_delete_lst = [int(a) for a in to_delete_lst_str.strip().split()]
        del_db(to_delete_lst)
        print(to_delete_lst)
        print(len(to_delete_lst))
        st.success(f"已经删除了, {to_delete_lst}")
    # 使用多选　和　select button实现建立新版本的QA集合
    loc_lst = [i for i in range(df_len)]
    select_options = st.multiselect(
        '选择数据行号,建立新版本的人设',
        loc_lst,
        loc_lst)
    if st.button("确定选择"):
        print(f"选择 {select_options}")
        version_id = select_db(option_persona, select_options)
        st.success(f"已经创建了由　{select_options}行的数据构建的人格,版本号为{version_id}")


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
if st.session_state["authentication_status"] and st.session_state["name"] in super_users:
    authenticator.logout('Logout', 'main')
    st.write(f'欢迎! *{st.session_state["name"]}*')
    main_page()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')
