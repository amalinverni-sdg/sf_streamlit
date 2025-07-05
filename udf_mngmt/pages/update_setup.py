import os
import io
import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

# Update page content
st.title("Update Page")

# You can also check query parameters here if needed
query_params = st.query_params
if query_params.get("page") == ["update"]:
    st.write("You have navigated to the update page based on your input.")