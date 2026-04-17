from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date
from .. import models, schemas
from ..database import get_db
from ..ai.gemini_client import get_gemini_client, TOOL_DEFINITIONS
from ..ai.vector_db import get_vector_db
from ..config import settings
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/", response_model=schemas.Message)
async def chat(chat_req: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1. Get conversation history and bound project
    db_conversation = db.query(models.Conversation).filter(models.Conversation.id == chat_req.conversation_id).first()
    bound_project_id = db_conversation.project_id if db_conversation else None
    
    db_messages = db.query(models.Message).filter(models.Message.conversation_id == chat_req.conversation_id).order_by(models.Message.created_at.asc()).all()
    
    # 2. Add new user message
    user_msg = models.Message(
        conversation_id=chat_req.conversation_id,
        role="user",
        content=chat_req.message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. RAG: Search knowledge base (Apply filter if project is bound)
    vector_db = get_vector_db()
    # If bound to a project, we can weight search or filter (ChromaDB supports 'where')
    search_where = {"project_id": bound_project_id} if bound_project_id else None
    search_results = vector_db.query(chat_req.workspace_id, chat_req.message, n_results=settings.rag_top_k, where=search_where)
    
    context_chunks = []
    if search_results and "documents" in search_results and search_results["documents"]:
        context_chunks = search_results["documents"][0]
    
    context_str = "\n\n".join(context_chunks)
    
    project_hint = ""
    if bound_project_id:
        project = db.query(models.Project).filter(models.Project.id == bound_project_id).first()
        if project:
            project_hint = f"This conversation is specifically about project '{project.name}' (ID: {project.id}). Please prioritize this project for all actions."

    system_prompt = f"""You are a personal AI assistant. Use the following context to help answer the user's request.
Context:
{context_str}

{project_hint}

If the user asks to perform an action (like creating a log or listing projects), use the available tools.
Today's date is {date.today().isoformat()}.
"""

    # 4. Prepare contents for Gemini
    contents = []
    for m in db_messages:
        parts = []
        if m.content:
            parts.append({"text": m.content})
        if m.tool_calls:
            for tc in m.tool_calls:
                parts.append({"functionCall": tc})
        
        contents.append({"role": "user" if m.role == "user" else "model", "parts": parts})
    
    # Add current message
    contents.append({"role": "user", "parts": [{"text": chat_req.message}]})

    client = get_gemini_client()
    
    # 5. Call Gemini and handle tool use loop
    max_iterations = 10
    current_iteration = 0
    
    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"DEBUG: Gemini iteration {current_iteration}")
        try:
            response = await client.generate_content(
                contents=contents,
                system_instruction=system_prompt,
                tools=TOOL_DEFINITIONS
            )
            
            candidate = response.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            # Save model response to contents for next turn
            if content:
                contents.append(content)
            
            assistant_text = ""
            tool_calls = []
            for part in parts:
                if "text" in part:
                    assistant_text += part["text"]
                if "functionCall" in part:
                    tool_calls.append(part["functionCall"])

            # 如果有文字且沒有工具呼叫，或者雖然有工具呼叫但我們想先回傳部分文字
            if not tool_calls and assistant_text:
                print(f"DEBUG: Final response reached at iteration {current_iteration}")
                db_assistant_msg = models.Message(
                    conversation_id=chat_req.conversation_id,
                    role="assistant",
                    content=assistant_text
                )
                db.add(db_assistant_msg)
                # ... 略 (更新時間)
                db.commit()
                db.refresh(db_assistant_msg)
                return db_assistant_msg
            
            if not tool_calls and not assistant_text:
                # 有時候 AI 會回傳空的，代表它可能卡住了
                print("DEBUG: Gemini returned empty content, retrying...")
                continue

            # Execute tool calls
            print(f"DEBUG: Executing tools: {[tc['name'] for tc in tool_calls]}")
            function_responses = []
            for tc in tool_calls:
                name = tc["name"]
                args = tc["args"]
                
                result = await execute_tool(name, args, db, chat_req.workspace_id)
                print(f"DEBUG: Tool {name} result: {str(result)[:100]}...")

                function_responses.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": name,
                            "response": {"result": result}
                        }
                    }]
                })
            
            contents.extend(function_responses)
            
        except Exception as e:
            print(f"DEBUG: Error in chat loop: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Too many tool use iterations")

async def execute_tool(name: str, args: Dict[str, Any], db: Session, workspace_id: str):
    logger.info(f"Executing tool: {name} with args: {args}")
    
    if name == "create_work_log":
        log = models.WorkLog(
            project_id=args["project_id"],
            workspace_id=workspace_id,
            log_date=date.fromisoformat(args["log_date"]),
            iso_week=date.fromisoformat(args["log_date"]).strftime("%Y-W%V"),
            content=args["content"],
            related_kpi_id=args.get("kpi_id"),
            source="ai_tool"
        )
        db.add(log)
        db.commit()
        return f"Successfully created work log for project {args['project_id']}"
    
    elif name == "list_projects":
        query = db.query(models.Project).filter(models.Project.workspace_id == workspace_id)
        if "status" in args:
            query = query.filter(models.Project.status == args["status"])
        projects = query.all()
        return json.dumps([{"id": p.id, "name": p.name, "status": p.status} for p in projects], ensure_ascii=False)

    elif name == "search_knowledge":
        vector_db = get_vector_db()
        results = vector_db.query(workspace_id, args["query"], n_results=args.get("top_k", 5))
        return json.dumps(results.get("documents", []), ensure_ascii=False)
    
    elif name == "update_project_status":
        project = db.query(models.Project).filter(models.Project.id == args["project_id"]).first()
        if project:
            project.status = args["status"]
            db.commit()
            return f"Updated project {project.name} status to {args['status']}"
        return "Project not found"
    
    elif name == "set_project_due_date":
        project = db.query(models.Project).filter(models.Project.id == args["project_id"]).first()
        if project:
            project.due_date = date.fromisoformat(args["due_date"])
            db.commit()
            return f"Set due date for {project.name} to {args['due_date']}"
        return "Project not found"
    
    elif name == "generate_weekly_report":
        workspace_id = args["workspace_id"]
        iso_week = args["iso_week"]
        logs = db.query(models.WorkLog).filter(
            models.WorkLog.workspace_id == workspace_id,
            models.WorkLog.iso_week == iso_week
        ).all()
        
        if not logs:
            return f"No work logs found for week {iso_week}."
        
        report_data = []
        for log in logs:
            project = db.query(models.Project).filter(models.Project.id == log.project_id).first()
            project_name = project.name if project else "Unknown"
            report_data.append(f"[{log.log_date}] ({project_name}): {log.content}")
        
        return "The following are the work logs for this week. Please summarize them into a formal weekly report with Key Achievements and Next Steps:\n" + "\n".join(report_data)
    
    elif name == "scan_git_commits":
        days = args.get("days", 1)
        import subprocess
        try:
            # 取得最近 N 天的 git commit 紀錄
            cmd = ["git", "log", f"--since={days} day ago", "--pretty=format:%h - %s (%ad)", "--date=short"]
            result = subprocess.check_output(cmd).decode("utf-8")
            if not result:
                return f"No git commits found in the last {days} days."
            return f"Found the following git commits:\n{result}\n\nPlease summarize these into one or more work logs for project {args['project_id']}."
        except Exception as e:
            return f"Error scanning git commits: {str(e)}"
    
    # Add more tools as needed
    return f"Tool {name} executed (placeholder)"
