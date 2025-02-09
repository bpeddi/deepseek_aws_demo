import streamlit as st
from langchain_ollama  import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Set up Streamlit UI
st.set_page_config(page_title="Interactive Chatbot", layout="wide")

st.title("🤖 Interactive Chatbot using LangChain & Ollama")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Setup LangChain LLM with Ollama
llm = ChatOllama(
    model="deepseek-r1:latest",
    base_url="http://localhost:11434",
    temperature=0.3
)

# Create a prompt template
prompt = PromptTemplate(
    input_variables=["chat_history", "question"],
    template="""
    You are a helpful AI assistant.
    Here is the chat history so far: {chat_history}
    Now answer the following user query: {question}
    """
)

# Chat input
if user_input := st.chat_input("Ask me anything..."):
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate response
    chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    response = LLMChain(llm=llm, prompt=prompt).run(chat_history=chat_history, question=user_input)
    
    # Add AI response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display AI response
    with st.chat_message("assistant"):
        st.write(response)
