# streamlit run gui.py

from collections import defaultdict

import httpx
import streamlit as st

st.set_page_config(layout="wide")
if 'containers' not in st.session_state:
    st.session_state.containers = defaultdict(str)
if 'related_containers' not in st.session_state:
    st.session_state.related_containers = defaultdict(list)


def reset_state():
    st.session_state.containers = defaultdict(str)
    st.session_state.related_containers = defaultdict(list)


def call_scramble(collection_id: str):
    request_data = {"collection_id": collection_id, "method": 'left-right-shuffle'}
    response = httpx.post(f'{st.session_state.endpoint_host}/scramble_collection_tokens', json=request_data)
    return response.json()


def call_sample(collection_id: str, max_sample_size: int = 10):
    request_data = {"collection_id": collection_id, "max_sample_size": max_sample_size}
    response = httpx.post(f'{st.session_state.endpoint_host}/sample_collection_members', json=request_data)
    return response.json()


@st.cache_data
def call_fetch(collection_id: str):
    request_data = {"collection_id": collection_id}
    response = httpx.post(f'{st.session_state.endpoint_host}/fetch_top_collection_members', json=request_data)
    return response.json()


def show_sample(collection_id: str, max_sample_size: int = 10):
    suggestions = call_sample(collection_id, max_sample_size)
    st.session_state.containers[collection_id] = suggestions_to_markdown(suggestions)


def show_scramble(collection_id: str):
    suggestions = call_scramble(collection_id)
    st.session_state.containers[collection_id] = suggestions_to_markdown(suggestions)


def add_collection(parent_collection_id: str, collection_id: str):
    response = call_fetch(collection_id)
    st.session_state.related_containers[parent_collection_id].append(response)


@st.cache_data
def call_suggestions_by_category(label: str):
    request_data = {
        "label": label,
        "params": {
            "user_info": {
                "user_wallet_addr": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "user_ip_addr": "192.168.0.1",
                "session_id": "d6374908-94c3-420f-b2aa-6dd41989baef",
                "user_ip_country": "us"
            },
            "mode": "full",
            "metadata": True
        },
        "categories": {
            "related": {
                "enable_learning_to_rank": True,
                "max_names_per_related_collection": 10,
                "max_per_type": 2,
                "max_recursive_related_collections": 3,
                "max_related_collections": 6,
                "name_diversity_ratio": 0.5
            },
            "wordplay": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "alternates": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "emojify": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "community": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "expand": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "gowild": {
                "max_suggestions": 10,
                "min_suggestions": 2
            },
            "other": {
                "max_suggestions": 10,
                "min_suggestions": 6,
                "min_total_suggestions": 50
            }
        }
    }
    response = httpx.post(f'{st.session_state.endpoint_host}/suggestions_by_category', json=request_data)
    return response.json()


RED_DOT = '🔴'
GREEN_DOT = '🟢'


def suggestions_to_markdown(suggestions: list):
    markdowns = []
    for suggestion in suggestions:
        status = GREEN_DOT if suggestion['metadata']['cached_status'] == 'available' else RED_DOT
        markdowns.append(f'{status}&nbsp;{suggestion["name"]} ')
    return '\n'.join(markdowns)


endpoint_host = st.sidebar.text_input("Endpoint host:", value='http://54.89.196.85', key="endpoint_host")
input = st.sidebar.text_input("Input:", value='zeus', key="input", on_change=reset_state)

response = call_suggestions_by_category(input)
categories = response['categories']

new_categories = []
collection_ids = set()
for i, category in enumerate(categories):
    new_categories.append(category)
    if 'collection_id' not in category:
        continue
    for new_category in st.session_state.related_containers[category['collection_id']]:
        if new_category['collection_id'] not in collection_ids:
            new_categories.append(new_category)
            collection_ids.add(new_category['collection_id'])
categories = new_categories

markdowns = []
for i, category in enumerate(categories):
    markdowns.append(f'[{category["name"]}](#category{i}) ({len(category["suggestions"])})\n')

st.markdown(' | '.join(markdowns))

for i, category in enumerate(categories):
    st.write('---')
    st.subheader(f'{category["name"]}', anchor=f'category{i}')

    st.markdown(suggestions_to_markdown(category['suggestions']))

    if 'collection_id' in category:
        col1, col2 = st.columns(2)
        col1.button('Sample', key=f'sample-{category["name"]}', on_click=show_sample,
                    args=[category['collection_id'], 10], use_container_width=True)
        col2.button('Scramble', key=f'scramble-{category["name"]}', on_click=show_scramble,
                    args=[category['collection_id'], ], use_container_width=True)
        container = st.container()
        if st.session_state.containers[category['collection_id']]:
            container.markdown('**Sampled/scrambled:** ' + st.session_state.containers[category['collection_id']])

    if 'related_collections' in category:
        st.markdown('##### Related collections')
        for collection, column in zip(category['related_collections'],
                                      st.columns(len(category['related_collections']))):
            column.button(collection['collection_title'],
                          key=f'{category["name"]}{collection["collection_title"]}', on_click=add_collection,
                          args=[category['collection_id'], collection['collection_id']])
