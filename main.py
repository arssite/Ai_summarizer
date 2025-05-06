# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Optional
# from dotenv import load_dotenv
# from supabase import create_client, Client
# import google.generativeai as genai
# import os

# # Load environment variables
# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # Initialize Supabase and Gemini
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel("gemini-1.5-flash")

# app = FastAPI()

# class PhoneRequest(BaseModel):
#     phone: str

# def fetch_assignments_by_phone(phone: str):
#     try:
#         response = supabase.table("assignments").select("*").eq("phone", phone).execute()
#         return response.data
#     except Exception as e:
#         print("❌ Error fetching assignments:", e)
#         return []

# def summarize_user_assignments(phone: str):
#     data = fetch_assignments_by_phone(phone)

#     if not data:
#         return {"status": "error", "message": f"No assignments found for phone: {phone}"}

#     try:
#         prompt = f"Summarize the following therapy assessments in under 1000 words:\n{data}"
#         response = model.generate_content(prompt)
#         summary = response.text.strip() if response and response.text else "Summary unavailable"
#         return {"status": "success", "phone": phone, "summary": summary}
#     except Exception as e:
#         print("❌ Error during summarization:", e)
#         return {"status": "error", "message": "Gemini summarization failed"}

# @app.post("/summarize")
# def summarize(request: PhoneRequest):
#     result = summarize_user_assignments(request.phone)
#     if result["status"] == "error":
#         raise HTTPException(status_code=404, detail=result["message"])
#     return result
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Supabase and Gemini
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

class PhoneRequest(BaseModel):
    phone: str

def fetch_assignments_by_phone(phone: str):
    try:
        response = supabase.table("assignments").select("*").eq("phone", phone).execute()
        return response.data
    except Exception as e:
        print("❌ Error fetching assignments:", e)
        return []

def update_summary_in_db(record_id: int, summary: str):
    try:
        supabase.table("assignments").update({"ai_insights_summary": summary}).eq("id", record_id).execute()
    except Exception as e:
        print(f"❌ Error updating summary for ID {record_id}:", e)

def summarize_user_assignments(phone: str):
    data = fetch_assignments_by_phone(phone)

    if not data:
        return {"status": "error", "message": f"No assignments found for phone: {phone}"}

    try:
        prompt = f"Summarize the following therapy assessments in under 1000 words:\n{data}"
        response = model.generate_content(prompt)
        summary = response.text.strip() if response and response.text else "Summary unavailable"

        # Update summary back into each corresponding row (optional: only latest if needed)
        for item in data:
            if item.get("id"):
                update_summary_in_db(item["id"], summary)

        return {"status": "success", "phone": phone, "summary": summary}
    except Exception as e:
        print("❌ Error during summarization:", e)
        return {"status": "error", "message": "Gemini summarization failed"}

@app.post("/summarize")
def summarize(request: PhoneRequest):
    result = summarize_user_assignments(request.phone)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result
