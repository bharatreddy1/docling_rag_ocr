from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage # Add this import

def create_documentation_agent(tools):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # In newer LangGraph versions, use the 'prompt' argument
    # instead of 'state_modifier'
    system_msg = (
        "You are an expert document assistant. "
        "Use the provided tools to search the library for answers. "
        "When you find information, mention the source filename. "
        "Answer accurately based ONLY on the retrieved context."
    )
    
    # Changed state_modifier -> prompt
    return create_react_agent(
        llm, 
        tools, 
        prompt=system_msg 
    )