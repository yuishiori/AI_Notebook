import aiohttp
import json
from ..config import settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str = settings.gemini_api_key, model: str = settings.gemini_model, base_url: str = settings.gemini_api_base_url):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def generate_content(self, contents: List[Dict[str, Any]], system_instruction: Optional[str] = None, tools: Optional[List[Dict[str, Any]]] = None, stream: bool = False):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        endpoint = "streamGenerateContent?alt=sse" if stream else "generateContent"
        url = f"{self.base_url}/models/{self.model}:{endpoint}?key={self.api_key}"
        print(f"DEBUG: Gemini API URL: {url.split('?')[0]}?key=REDACTED")

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": settings.gemini_temperature,
                "maxOutputTokens": settings.gemini_max_output_tokens,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": settings.gemini_safety_threshold
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": settings.gemini_safety_threshold
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": settings.gemini_safety_threshold
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": settings.gemini_safety_threshold
                }
            ]
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if tools:
            payload["tools"] = [{"function_declarations": [t["function"] for t in tools]}]
            payload["tool_config"] = {"function_calling_config": {"mode": "AUTO"}}

        print(f"DEBUG: Sending request to Gemini...")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                print(f"DEBUG: Gemini Response Status: {response.status}")
                if response.status != 200:
                    text = await response.text()
                    print(f"DEBUG: Gemini API error: {response.status} - {text}")
                    logger.error(f"Gemini API error: {response.status} - {text}")
                    raise Exception(f"Gemini API error: {response.status} - {text}")

                if stream:
                    return response
                else:
                    res_json = await response.json()
                    print(f"DEBUG: Gemini Response JSON parsed")
                    return res_json

# Tool Definitions (Section 15)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "create_work_log",
            "description": "Create a new work log for a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "The ID of the project."},
                    "log_date": {"type": "string", "description": "The date of the log (YYYY-MM-DD)."},
                    "content": {"type": "string", "description": "The content of the work log."},
                    "kpi_id": {"type": "string", "description": "Optional KPI ID to link."}
                },
                "required": ["project_id", "log_date", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_project_status",
            "description": "Update the status and progress of a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "The ID of the project."},
                    "status": {"type": "string", "enum": ["active", "paused", "done"], "description": "The new status."},
                    "progress": {"type": "string", "description": "Progress description."}
                },
                "required": ["project_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search the knowledge base for a specific query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "workspace_id": {"type": "string", "description": "The workspace ID."},
                    "project_id": {"type": "string", "description": "Optional project ID to filter."},
                    "top_k": {"type": "integer", "default": 5, "description": "Number of results to return."}
                },
                "required": ["query", "workspace_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "List projects in a workspace with optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "The workspace ID."},
                    "status": {"type": "string", "enum": ["active", "paused", "done"], "description": "Optional status filter."},
                    "due_within_days": {"type": "integer", "description": "Filter projects due within N days."}
                },
                "required": ["workspace_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_report",
            "description": "Generate a weekly report for a workspace and week.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "The workspace ID."},
                    "iso_week": {"type": "string", "description": "The ISO week string (YYYY-Www)."}
                },
                "required": ["workspace_id", "iso_week"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_project_due_date",
            "description": "Set the due date for a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "The ID of the project."},
                    "due_date": {"type": "string", "description": "The due date (YYYY-MM-DD)."}
                },
                "required": ["project_id", "due_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_git_commits",
            "description": "Scan the local git repository for recent commits to generate work logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 1, "description": "Number of days to look back."},
                    "project_id": {"type": "string", "description": "The ID of the project to associate the logs with."}
                },
                "required": ["project_id"]
            }
        }
    }
]

# Global instance
gemini_client = None

def get_gemini_client():
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client
