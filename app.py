import json
import os
import time
import requests
from urllib.parse import quote
from dotenv import load_dotenv
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards
import pyperclip

load_dotenv()

CIVITAI_TOKEN = os.getenv('CIVITAI_TOKEN')
PAGE_TITLE = "Civitai Model Extractor"
PAGE_ICON = "🚀"
API_URL = 'https://civitai.com/api/v1/'

VERSION = 'v0.1.0'

def get_models_infos(model_name: str) -> dict:
    '''get models infos from civitai'''
    model = quote(model_name)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CIVITAI_TOKEN}"
    }
    response = requests.get(f"{API_URL}models?query={model}", headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

def get_images(version_id: int, model_id: int) -> list:
    '''get images from version id model'''
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CIVITAI_TOKEN}"
    }
    response = requests.get(f"{API_URL}images?limit=200&modelVersionId={version_id}&modelId={model_id}", headers=headers)
    # response = requests.get(f"https://civitai.com/api/v1/images?modelVersionId={version_id}", headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

st.set_page_config(
    page_title=PAGE_TITLE, 
    page_icon=PAGE_ICON, 
    layout="wide"
)

def popover_image_metadata(image: dict, version_id: int) -> None:
    '''popup image metadata'''
    model, prompt, negative_prompt, seed, steps, cfg_scale, sampler, clip_skip = None, None, None, None, None, None, None, None
    if meta:= image.get('meta'):
        model = meta.get('Model', 'Not provided')
        prompt = meta.get('prompt', 'Not provided')
        negative_prompt = meta.get('negativePrompt', 'Not provided')
        seed = meta.get('seed', 'Not provided')
        steps = meta.get('steps', 'Not provided')
        cfg_scale = meta.get('cfgScale', 'Not provided')
        sampler = meta.get('sampler', 'Not provided')
        clip_skip = meta.get('Clip skip', 'Not provided')

    msg = \
"""<p>ID: {id}<br>  
Author: {author}<br>
Size: {size}<br>  
Model: {model}</p>"""

    msg_prompt = f"<p><b>Prompt:</b><br>{prompt}</p>"
    msg_negative = f"<p><b>Negative Prompt:</b><br>{negative_prompt}</p>"

    msg_extra = \
"""<p>
    <b>Seed:</b> {seed}<br>
    <b>Steps:</b> {steps}<br>
    <b>Sampler:</b> {sampler}<br>
    <b>CFG Scale:</b> {cfg_scale}<br>
    <b>Clip Skip:</b> {clip_skip}<br>
</p>"""
    
    msg = msg.format(
        id=image['id'],
        author=image['username'], 
        size=f"{image['width']}x{image['height']} px", 
        model=model, 
    )
    st.markdown(msg, unsafe_allow_html=True)
    
    st.markdown(msg_prompt, unsafe_allow_html=True)
    if st.button("Copy Prompt", key=f"copy_prompt_{image['id']}_{version_id}", type="primary"):
        pyperclip.copy(prompt)
        success_prompt = st.success("copied!")
        time.sleep(2)
        success_prompt.empty()

    st.markdown(msg_negative, unsafe_allow_html=True)
    if st.button("Copy Negative Prompt", key=f"copy_negative_{image['id']}_{version_id}", type="primary"):
        pyperclip.copy(negative_prompt)
        success_neg = st.success("copied!")
        time.sleep(2)
        success_neg.empty()

    msg_extra = msg_extra.format(
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        sampler=sampler,
        clip_skip=clip_skip
    )
    st.markdown(msg_extra, unsafe_allow_html=True)


################
# INIT SESSION #
################
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = None
if 'models' not in st.session_state:
    st.session_state['models'] = {}
if 'popup_wf' not in st.session_state:
    st.session_state['popup_wf'] = False

#########
# STYLE #
#########
st.markdown("""
<style>
div.nx-tumbnail {
    display: inline-block; 
    width: 32px; 
    height: 32px; 
    border-radius: 50%;
    background-repeat: no-repeat; 
    background-position: center; 
    background-size: cover;
    vertical-align: middle;
    margin-right: 15px;
}
            
div.stHeadingContainer  a {
    text-decoration: none;
    color: inherit;
}

label[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"] div {
    color: #31333F;
} 

div[data-testid="stPopoverBody"] {
    min-width: 65%;
}
            
</style>
""", 
    unsafe_allow_html=True
)

with st.sidebar:
    st.header(f"{PAGE_TITLE} {PAGE_ICON}")
    st.subheader(f"Version: {VERSION}")
    model_name = st.text_input("Model Name", st.session_state['model_name'])

if model_name:
    st.session_state['model_name'] = model_name
    st.write(f"Query: ***{st.session_state['model_name']}***")

    if st.session_state['models'].get(st.session_state['model_name']) is None:
        models = get_models_infos(st.session_state['model_name'])
        st.session_state['models'][st.session_state['model_name']] = models

    models = st.session_state['models'][st.session_state['model_name']]

    if len(models['items']) == 0:
        st.error(f"{st.session_state['model_name']} seem to not exist on Civitai.")
    else:    
        
        nb_models = len(models['items'])
        st.success(f"Found {nb_models} model{'s' if nb_models > 1 else ''}")
        
        for model in models['items']:
            author = ''
            author_img = ''
            if 'creator' in model:
                author_img = f"<div class=\"nx-tumbnail\" style=\"background-image: url({model['creator']['image']});\"></div> " if model['creator']['image'] else ''
                author = f"[{model['creator']['username']}](https:/civitai.com/user/{model['creator']['username']})"
            author_title = f"{author_img}{author}"

            st.subheader(f"[{model['name']}](https:/civitai.com/models/{model['id']})", divider=True)
            st.markdown(f"##### {author_img}{author}", unsafe_allow_html=True)

            infos_str = \
"""
- ID: {id}
- Type: {type}
- NSFW: {nsfw}
- Tags: {tags}
"""     
            infos_str = infos_str.format(
                id=model['id'],
                type=model['type'],
                nsfw=model['nsfw'],
                tags=', '.join(f"[{tag}](https:/civitai.com/tag/{quote(tag)})" for tag in model['tags'])
            )
            st.markdown(infos_str, unsafe_allow_html=True)

            m_1, m_2, m_3, m_4 = st.columns(4)

            m_1.metric(label="📥 Download", value=model['stats'].get('downloadCount'))
            m_2.metric(label="👍 Likes", value=model['stats'].get('thumbsUpCount'))
            m_3.metric(label="👎 Unlikes", value=model['stats'].get('thumbsDownCount'))
            m_4.metric(label="💬 Comments", value=model['stats'].get('commentCount'))
            style_metric_cards(
                border_left_color="#FF4B4B",
            )
            
            st.write("##### Versions")
            for version in model['modelVersions']:
                if version['id'] not in model:
                    model[version['id']] = get_images(version_id=version['id'], model_id=model['id'])
                    st.session_state['models'][st.session_state['model_name']] = models
                with st.expander(f"{version['name']}", ):                
                    st.markdown(f"Download: [{version['id']}]({version['downloadUrl']})<br>Images: {len(model[version['id']]['items'])}", unsafe_allow_html=True)
                    col_1, col_2, col_3, col_4 = st.columns(4)
                    i = 1
                    for img in model[version['id']]['items']:
                        if i == 1:
                            col_1.image(img['url'])
                            c_1, c_2, c_3 = col_1.columns(3, gap='small')
                            with c_1.popover("ℹ️", use_container_width=True):
                                popover_image_metadata(image=img, version_id=version['id'])
                            data = ''
                            disabled = True
                            if meta:= img.get('meta'):
                                if comfy:= meta.get('comfy'):
                                    data_json = json.loads(comfy)
                                    data = json.dumps(data_json.get('workflow'), indent=4)
                                    disabled = False
                                    
                            c_2.download_button(
                                label="WF",
                                data = data,
                                mime="text/json",
                                key=f"nodes_{img['id']}_{version['id']}", 
                                file_name=f"wf_{img['id']}.json",
                                use_container_width=True,
                                disabled=disabled
                            )
                            c_3.link_button("📷", f"https://civitai.com/images/{img['id']}", use_container_width=True)
                        if i == 2:
                            col_2.image(img['url'])
                            c_1, c_2, c_3 = col_2.columns(3, gap='small')
                            with c_1.popover("ℹ️", use_container_width=True):
                                popover_image_metadata(image=img, version_id=version['id'])
                            data = ''
                            disabled = True
                            if meta:= img.get('meta'):
                                if comfy:= meta.get('comfy'):
                                    data_json = json.loads(comfy)
                                    data = json.dumps(data_json.get('workflow'), indent=4)
                                    disabled = False
                                    
                            c_2.download_button(
                                label="WF",
                                data = data,
                                mime="text/json",
                                key=f"nodes_{img['id']}_{version['id']}", 
                                file_name=f"wf_{img['id']}.json",
                                use_container_width=True,
                                disabled=disabled
                            )
                            c_3.link_button("📷", f"https://civitai.com/images/{img['id']}", use_container_width=True)
                        if i == 3:
                            col_3.image(img['url'])
                            c_1, c_2, c_3 = col_3.columns(3, gap='small')
                            with c_1.popover("ℹ️", use_container_width=True):
                                popover_image_metadata(image=img, version_id=version['id'])
                            data = ''
                            disabled = True
                            if meta:= img.get('meta'):
                                if comfy:= meta.get('comfy'):
                                    data_json = json.loads(comfy)
                                    data = json.dumps(data_json.get('workflow'), indent=4)
                                    disabled = False
                                    
                            c_2.download_button(
                                label="WF",
                                data = data,
                                mime="text/json",
                                key=f"nodes_{img['id']}_{version['id']}", 
                                file_name=f"wf_{img['id']}.json",
                                use_container_width=True,
                                disabled=disabled
                            )
                            c_3.link_button("📷", f"https://civitai.com/images/{img['id']}", use_container_width=True)
                        if i == 4:
                            col_4.image(img['url'])
                            c_1, c_2, c_3 = col_4.columns(3, gap='small')
                            with c_1.popover("ℹ️", use_container_width=True):
                                popover_image_metadata(image=img, version_id=version['id'])
                            data = ''
                            disabled = True
                            if meta:= img.get('meta'):
                                if comfy:= meta.get('comfy'):
                                    data_json = json.loads(comfy)
                                    data = json.dumps(data_json.get('workflow'), indent=4)
                                    disabled = False
                                    
                            c_2.download_button(
                                label="WF",
                                data = data,
                                mime="text/json",
                                key=f"nodes_{img['id']}_{version['id']}", 
                                file_name=f"wf_{img['id']}.json",
                                use_container_width=True,
                                disabled=disabled
                            )
                            c_3.link_button("📷", f"https://civitai.com/images/{img['id']}", use_container_width=True)
                        i += 1
                        if i > 4:
                            i = 1
            with st.expander("Description"):
                st.markdown(model['description'], unsafe_allow_html=True)


else:
    st.write("Indicate model name")

