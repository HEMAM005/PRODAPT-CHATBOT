from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import google.generativeai as genai
import re

# ==============================
# 🔑 Configure Gemini API Key
# ==============================
GEMINI_API_KEY = "AIzaSyBjykkcg2yJksGH_ZCQLzUt3AgW3T2_HVM"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
# 🧠 Store Chat History (memory)
# ==============================
chat_history = []   # list of {"role": "user"/"model", "parts": ["message"]}

# ==============================
# 📄 Serve Frontend
# ==============================
@app.get("/")
async def get_ui():
    return FileResponse("chat.html")

# ==============================
# ✨ Simplify and Format Text (➤ bullets only at start)
# ==============================
def simplify_text(text: str) -> str:
    if not text:
        return "🤖 Sorry, I couldn’t generate a reply."

    # Preserve code blocks separately
    code_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    placeholders = {}
    for i, block in enumerate(code_blocks):
        placeholder = f"[[CODE_BLOCK_{i}]]"
        placeholders[placeholder] = block
        text = text.replace(block, placeholder)

    # Remove bold / markdown symbols
    text = text.replace("**", "").replace("#", "").strip()

    # Replace list markers with ➤
    text = re.sub(r"^\s*\d+\.", "➤", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•*]\s+", "➤", text, flags=re.MULTILINE)

    # Ensure each non-empty line starts with ➤
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned = []
    for line in lines:
        if not any(ph in line for ph in placeholders):  # skip placeholders
            line = re.sub(r"^➤+", "➤", line)  # collapse multiple bullets
            if not line.startswith("➤"):
                line = f"➤ {line}"
        cleaned.append(line)

    final_text = "\n".join(cleaned).strip()

    # Restore code blocks (without ➤)
    for placeholder, block in placeholders.items():
        final_text = final_text.replace(placeholder, block)

    return final_text

# ==============================
# 💬 Chat Endpoint (with memory)
# ==============================
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")

        if not user_message:
            return JSONResponse({"reply": "⚠️ No message received"}, status_code=400)

        # Add user message to chat history
        chat_history.append({"role": "user", "parts": [user_message]})

        # Generate response with history
        response = model.generate_content(chat_history)

        reply = simplify_text(response.text)

        # Save model reply to chat history
        chat_history.append({"role": "model", "parts": [reply]})

        return {"reply": reply}

    except Exception as e:
        return JSONResponse({"reply": f"❌ Error: {str(e)}"}, status_code=500)
