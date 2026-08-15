from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json, os, uuid, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "/app/ctf_data.json"

def get_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"users": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

@app.post("/api/ctf-academy")
async def academy(req: Request):
    body = await req.json()
    action = body.get("action", "")
    db = get_db()

    if action == "register":
        username = body.get("username", "")
        if username in db["users"]:
            return JSONResponse(status_code=409, content={"ok": False, "message": "User exists"})
        db["users"][username] = {
            "id": str(uuid.uuid4()),
            "username": username,
            "score": 0,
            "role": "user",
            "nationality": "CL",
            "created_at": int(time.time() * 1000)
        }
        save_db(db)
        user = db["users"][username]
        return {"ok": True, "token": username, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": username, "role": "user"}}}
    
    if action == "login":
        username = body.get("username", "")
        if username not in db["users"]:
            return JSONResponse(status_code=401, content={"ok": False, "message": "Invalid"})
        user = db["users"][username]
        return {"ok": True, "token": username, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": username, "role": "user"}}}

    if action == "state":
        auth = req.headers.get("Authorization", "").replace("Bearer ", "")
        if auth in db["users"]:
            user = db["users"][auth]
            return {"ok": True, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": auth, "role": "user"}}}
        return {"ok": True, "data": {"currentUser": None, "leaderboard": [], "participants": len(db["users"]), "session": None}}

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}
