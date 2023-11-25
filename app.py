import streamlit as st
from openai import OpenAI
from io import BytesIO
from PIL import Image
import base64

if 'initialized' not in st.session_state:
    st.session_state['history'] = [{'role': 'system', 'content': ''}]
    st.session_state['cost'] = 0.0
    st.session_state['initialized'] = True

st.markdown('# GPT-4 Vision Client')
api_key = st.text_input('OpenAI API Key', '', type='password')

# display cost
if st.session_state['cost'] > 0:
    st.info('Session Cost: ${:f}'.format(st.session_state['cost']), icon='💰')

# make tabs
chatTab, settingsTab = st.tabs(['Chat', 'Settings'])

# set openai settings
with settingsTab:
    image_detail = st.selectbox('Image Detail', ['low', 'high'])
    temperature = st.slider('Temperature', 0.0, 2.0, 0.7)
    max_tokens = st.slider('Max Token Output', 100, 1000, 300)

with chatTab:
    # optional system message
    with st.expander('System Message'):
        st.session_state['history'][0]['content'] = st.text_area('sys message',
                                                                 st.session_state['history'][0]['content'],
                                                                 label_visibility='collapsed')

    # display chat
    for msg in st.session_state['history'][1:]:
        if msg['role'] == 'user':
            for i in msg['content']:
                if i['type'] == 'text':
                    st.markdown(f"<span style='color: #c4c4c4'>You: {i['text']}</span>", unsafe_allow_html=True)
                else:
                    with st.expander('Attached Image'):
                        img = Image.open(BytesIO(base64.b64decode(i['image_url']['url'][23:])))
                        st.image(img)
        else:
            msg_content = ''.join(['  ' + char if char == '\n' else char for char in msg['content']])  # fixes display issue
            st.markdown('Assistant: ' + msg_content)

    # get user inputs
    text_input = st.text_input('Prompt', '')
    img_input = st.file_uploader('Images', accept_multiple_files=True)

    cols = st.columns(9)

    # send api request
    with cols[0]:
        if st.button('Send'):
            if api_key:
                if text_input or img_input:
                    msg = {'role': 'user', 'content': []}
                    if text_input:
                        msg['content'].append({'type': 'text', 'text': text_input})
                    if img_input:
                        for img in img_input:
                            encoded_img = base64.b64encode(img.read()).decode('utf-8')
                            msg['content'].append(
                                {
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': f'data:image/jpeg;base64,{encoded_img}',
                                        'detail': image_detail
                                    }
                                }
                            )
                    st.session_state['history'].append(msg)
                    history = (
                        st.session_state['history']
                        if st.session_state['history'][0]['content']
                        else st.session_state['history'][1:]
                    )
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model = 'gpt-4-vision-preview',
                        temperature = temperature,
                        max_tokens = max_tokens,
                        messages = history
                    )
                    st.session_state['history'].append(
                        {'role': 'assistant', 'content': response.choices[0].message.content}
                    )
                    st.session_state['cost'] += response.usage.prompt_tokens * 0.01 / 1000
                    st.session_state['cost'] += response.usage.completion_tokens * 0.03 / 1000
                    st.rerun()
                else:
                    st.warning('You can\'t just send nothing!')
            else:
                st.warning('API Key required')

    # clear chat history
    with cols[8]:
        if st.button('Clear'):
            st.session_state['history'] = [st.session_state['history'][0]]
            st.rerun()
