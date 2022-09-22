import streamlit as st
from streamlit_chat import message
import requests
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate

st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)
API_URL = ""


def query(payload):
    response = requests.post(API_URL, json=payload)
    return response.json()


def get_text():
    input_text = st.text_input("You: ", "Hello, how are you?", key="input")
    return input_text


def main_page():
    API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"

    st.header("Streamlit Chat - Demo")
    # if st.session_state["authentication_status"]:
    #     st.write(f'Welcome *{st.session_state["name"]}*')
    st.markdown("[Github](https://github.com/ai-yash/st-chat)")

    if 'generated' not in st.session_state:\
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []

    user_input = get_text()

    if user_input:
        # output = query({
        #    "inputs": {
        #        "past_user_inputs": st.session_state.past,
        #        "generated_responses": st.session_state.generated,
        #        "text": user_input,
        #    },"parameters": {"repetition_penalty": 1.33},
        # })

        st.session_state.past.append(user_input)
        st.session_state.generated.append("Sorry, we are debugging")

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
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
    main_page()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')
