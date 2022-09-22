import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.authenticate import Authenticate

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

try:
    if authenticator.register_user('Register user', preauthorization=False):
        st.success('User registered successfully')
        print("user is registered")
        with open('../config.yaml', 'w') as file:
            print("Dump config into yaml")
            yaml.dump(config, file, default_flow_style=False)
except Exception as e:
    st.error(e)
