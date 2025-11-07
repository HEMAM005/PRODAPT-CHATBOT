from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import google.generativeai as genai
import re

# ==============================
# 🔑 Configure Gemini API Key
# ==============================
GEMINI_API_KEY = "AIzaSyDQUsbaB1MC1BxT6vRlI1eSl9ASg3iq3ws"
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Use correct model from list_models()
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ==============================
# 🚀 FastAPI App Setup
# ==============================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# 🧠 Store Chat History
# ==============================
chat_history = []

# ==============================
# 📄 Serve chat.html
# ==============================
@app.get("/")
async def get_ui():
    return FileResponse("chat.html")

# ==============================
# ✨ Simplify & Beautify Text
# ==============================
def simplify_text(text: str) -> str:
    if not text:
        return "🤖 Sorry, I couldn’t generate a reply."

    # Extract code blocks
    code_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    placeholders = {}
    for i, block in enumerate(code_blocks):
        placeholder = f"[[CODE_BLOCK_{i}]]"
        placeholders[placeholder] = block
        text = text.replace(block, placeholder)

    # Remove markdown
    text = text.replace("**", "").replace("#", "").strip()
    text = re.sub(r"^\s*\d+\.", "➤", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•*]\s+", "➤", text, flags=re.MULTILINE)

    # Add bullets
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned = []
    for line in lines:
        if not any(ph in line for ph in placeholders):
            line = re.sub(r"^➤+", "➤", line)
            if not line.startswith("➤"):
                line = f"➤ {line}"
        cleaned.append(line)

    final_text = "\n".join(cleaned).strip()

    # Restore code blocks
    for placeholder, block in placeholders.items():
        final_text = final_text.replace(placeholder, block)

    return final_text


# ==============================
# 💬 Chat Endpoint (POST)
# ==============================
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")

        if not user_message:
            return JSONResponse({"reply": "⚠️ No message received"}, status_code=400)

        # Append user input to history
        chat_history.append({"role": "user", "parts": [user_message]})

        # Generate model response
        response = model.generate_content(chat_history)

        reply = simplify_text(response.text)

        # Add model reply to history
        chat_history.append({"role": "model", "parts": [reply]})

        return {"reply": reply}

    except Exception as e:
        return JSONResponse({"reply": f"❌ Error: {str(e)}"}, status_code=500)


# ==============================
# ▶️ Run server
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

