import os
import traceback
from typing import List
from urllib.parse import quote_plus
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

# Langchain & Langgraph imports
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

# ---------------------------------------------------------
# 1. ENVIRONMENT & DATABASE SETUP
# ---------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")

if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create PostgreSQL Engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------------------------------------
# 2. DATABASE MODELS
# ---------------------------------------------------------
class InteractionLog(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), index=True)
    date = Column(String(50))
    topic = Column(String(255))
    summary = Column(Text)
    follow_up_date = Column(String(50), nullable=True)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 3. LANGGRAPH TOOLS
# ---------------------------------------------------------
@tool
def log_interaction(hcp_name: str, date: str, topic: str, summary: str, follow_up_date: str = None) -> str:
    """Saves a new HCP interaction to the database."""
    db = SessionLocal()
    new_log = InteractionLog(
        hcp_name=hcp_name, date=date, topic=topic, 
        summary=summary, follow_up_date=follow_up_date
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    db.close()
    return f"Successfully logged interaction #{new_log.id} with {hcp_name} on {date} regarding {topic}."

@tool
def edit_interaction(interaction_id: int, new_topic: str = None, new_summary: str = None, new_follow_up_date: str = None) -> str:
    """Modifies an existing logged interaction using its ID."""
    db = SessionLocal()
    log = db.query(InteractionLog).filter(InteractionLog.id == interaction_id).first()
    if not log:
        db.close()
        return f"Error: Interaction ID {interaction_id} not found."
    
    if new_topic: log.topic = new_topic
    if new_summary: log.summary = new_summary
    if new_follow_up_date: log.follow_up_date = new_follow_up_date
    
    db.commit()
    db.close()
    return f"Successfully updated interaction #{interaction_id}."

@tool
def get_recent_interactions(limit: int = 5) -> str:
    """Fetches the most recent interactions logged in the database."""
    db = SessionLocal()
    logs = db.query(InteractionLog).order_by(InteractionLog.id.desc()).limit(limit).all()
    db.close()
    if not logs:
        return "No interactions found in the database."
    result = "\n".join([f"ID: {l.id} | HCP: {l.hcp_name} | Date: {l.date} | Topic: {l.topic}" for l in logs])
    return f"Recent interactions:\n{result}"

@tool
def search_hcp_history(hcp_name: str) -> str:
    """Searches for all past interactions with a specific HCP."""
    db = SessionLocal()
    logs = db.query(InteractionLog).filter(InteractionLog.hcp_name.ilike(f"%{hcp_name}%")).all()
    db.close()
    if not logs:
        return f"No past interactions found for {hcp_name}."
    result = "\n".join([f"ID: {l.id} | Date: {l.date} | Topic: {l.topic} | Summary: {l.summary}" for l in logs])
    return f"History for {hcp_name}:\n{result}"

@tool
def delete_interaction(interaction_id: int) -> str:
    """Deletes an interaction log from the database."""
    db = SessionLocal()
    log = db.query(InteractionLog).filter(InteractionLog.id == interaction_id).first()
    if not log:
        db.close()
        return f"Error: Interaction ID {interaction_id} not found."
    db.delete(log)
    db.commit()
    db.close()
    return f"Successfully deleted interaction #{interaction_id}."

tools = [log_interaction, edit_interaction, get_recent_interactions, search_hcp_history, delete_interaction]

# ---------------------------------------------------------
# 4. LANGGRAPH AGENT SETUP
# ---------------------------------------------------------
llm = ChatGroq(model="openai/gpt-oss-20b", api_key=GROQ_API_KEY, temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot_node(state: MessagesState):
    system_msg = SystemMessage(
        content="You are an AI assistant for Medical Representatives. Help them log, edit, and search HCP interactions using the provided tools. "
                "Always be concise, professional, and confirm actions once completed."
    )
    messages = [system_msg] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def tools_condition(state: MessagesState):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state: {state}")
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
agent = graph_builder.compile()

# ---------------------------------------------------------
# 5. FASTAPI ROUTES
# ---------------------------------------------------------
app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ManualLogRequest(BaseModel):
    hcp_name: str
    date: str
    topic: str
    summary: str
    follow_up_date: str = None

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.message)]}
        final_state = agent.invoke(inputs)
        return {"reply": final_state["messages"][-1].content}
    except Exception as e:
        print("\n--- AI ERROR ---")
        traceback.print_exc()
        print("----------------\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interactions")
async def create_interaction_manual(data: ManualLogRequest, db: Session = Depends(get_db)):
    try:
        new_log = InteractionLog(**data.model_dump())
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {"status": "success", "data": new_log}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interactions")
async def fetch_all_interactions(db: Session = Depends(get_db)):
    logs = db.query(InteractionLog).order_by(InteractionLog.id.desc()).all()
    return {"data": logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)