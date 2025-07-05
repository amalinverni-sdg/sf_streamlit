import streamlit as st

create_page = st.Page("pages/create_setup.py", title="Create entry", icon=":material/add_circle:")
update_page = st.Page("pages/update_setup.py", title="Update entry", icon=":material/delete:")

pg = st.navigation([create_page, update_page])
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()
