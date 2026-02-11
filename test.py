import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1p72hvVlFG9nTA3-2XWutxlH9bxd5AA4aSvD1ksfasyk/edit?gid=120210836#gid=120210836t", ttl=0)

st.dataframe(df)