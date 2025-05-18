import streamlit as st
import pandas as pd
import openai
from io import StringIO
from docx import Document
import pdfplumber
import os 

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide")
st.title("FindMyComponent Chatbot 🤖")

st.markdown(
    """
    **Features:**  
    - Chatbot for general questions  
    - Chat about content in uploaded files (txt, Word, Excel, PDF)
    - Search Components used in board and systems (IC, Passive, Thermal, Connectors..)  
    - Find alternatives by Form, Fit, Function (FFF)
    """
)

# ---- FILE UPLOAD SECTION ----
st.header("Chat With Your File")
uploaded_file = st.file_uploader(
    "Upload a file to chat with (txt, docx, xlsx, pdf):",
    type=["txt", "docx", "xlsx", "pdf"],
    key="file_uploader1"
)

def extract_text_from_file(uploaded_file):
    filetype = uploaded_file.name.split('.')[-1].lower()
    if filetype == "txt":
        return StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    elif filetype == "docx":
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif filetype == "pdf":
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    elif filetype == "xlsx":
        df = pd.read_excel(uploaded_file)
        return df.head(20).to_string()
    else:
        return "Unsupported file type."

file_text = ""
if uploaded_file is not None:
    file_text = extract_text_from_file(uploaded_file)
    st.info("File content loaded and ready for chat.")

st.header("Chat with IC Part Finder (or Your File)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Display chat history using st.chat_message ----
for sender, message in st.session_state.chat_history:
    if sender == "You":
        with st.chat_message("user"):
            st.markdown(message)
    else:
        with st.chat_message("assistant"):
            st.markdown(message)

# ---- User input at the bottom ----
user_input = st.chat_input("Type your message...")
if user_input:
    st.session_state.chat_history.append(("You", user_input))

    # Build messages for OpenAI
    messages = []
    if file_text:
        context = f"The following is the content of the uploaded file:\n{file_text}\n\n"
        messages.append({"role": "system", "content": context})
    for sender, msg in st.session_state.chat_history[-10:]:
        messages.append({"role": "user" if sender == "You" else "assistant", "content": msg})

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            max_tokens=1024,
        )
        bot_message = response.choices[0].message.content
    except Exception as e:
        bot_message = f"OpenAI API Error: {e}"
    st.session_state.chat_history.append(("Bot", bot_message))
    st.rerun()

st.divider()
