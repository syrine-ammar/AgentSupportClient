"""
llm_client.py
-----------------
 LLM wrapper. Change MODEL and API key in .env to switch provider.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel(os.getenv("LLM_MODEL", "gemini-1.5-flash"))#creates the model we will use to call the LLM for every request. You can change the model in the .env file 

def call_LLM(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    #This function sends a prompt to Gemini and returns plain text.
    response = _model.generate_content(
        f"{system_prompt}\n\n{user_message}",
        generation_config=genai.GenerationConfig(temperature=temperature),
    )
    return response.text


def call_LLM_json(system_prompt: str, user_message: str) -> dict:
    raw = call_LLM(system_prompt, user_message, temperature=0.0)
    cleaned = raw.strip().strip("```").removeprefix("json").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw_response": raw}


# Quick test
if __name__ == "__main__":
    print(call_LLM("Tu es un assistant.", "bonjour, explain in 3 lines what is langchain"))