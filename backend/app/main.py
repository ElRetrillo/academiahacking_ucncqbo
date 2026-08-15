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
        return {"users": {}, "admin_tokens": {}}
    with open(DB_FILE, "r") as f:
        try:
            data = json.load(f)
            if "admin_tokens" not in data:
                data["admin_tokens"] = {}
            return data
        except:
            return {"users": {}, "admin_tokens": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

@app.post("/api/ctf-academy")
async def academy(req: Request):
    body = await req.json()
    action = body.get("action", "")
    db = get_db()
    auth = req.headers.get("Authorization", "").replace("Bearer ", "")

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
            "description": "Hola! Soy un nuevo miembro de la academia.",
            "created_at": int(time.time() * 1000)
        }
        # First user is admin automatically for setup
        if len(db["users"]) == 1:
            db["users"][username]["role"] = "admin"
            
        save_db(db)
        user = db["users"][username]
        return {"ok": True, "token": username, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": username, "role": user["role"]}}}
    
    if action == "login":
        username = body.get("username", "")
        if username not in db["users"]:
            return JSONResponse(status_code=401, content={"ok": False, "message": "Invalid"})
        user = db["users"][username]
        return {"ok": True, "token": username, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": username, "role": user["role"]}}}

    if action == "state":
        if auth in db["users"]:
            user = db["users"][auth]
            return {"ok": True, "data": {"currentUser": user, "leaderboard": [], "participants": len(db["users"]), "session": {"username": auth, "role": user["role"]}}}
        return {"ok": True, "data": {"currentUser": None, "leaderboard": [], "participants": len(db["users"]), "session": None}}

    if action == "update_profile":
        if auth not in db["users"]:
            return JSONResponse(status_code=401, content={"ok": False, "message": "Unauthorized"})
        db["users"][auth]["description"] = body.get("description", "")
        save_db(db)
        return {"ok": True, "message": "Perfil actualizado", "data": {"currentUser": db["users"][auth]}}

    if action == "generate_admin_token":
        if auth not in db["users"] or db["users"][auth].get("role") != "admin":
            return JSONResponse(status_code=403, content={"ok": False, "message": "Forbidden"})
        token = str(uuid.uuid4())
        db["admin_tokens"][token] = {"used": False, "created_by": auth, "created_at": int(time.time() * 1000)}
        save_db(db)
        return {"ok": True, "message": "Token generado", "data": {"token": token}}

    if action == "redeem_admin_token":
        if auth not in db["users"]:
            return JSONResponse(status_code=401, content={"ok": False, "message": "Unauthorized"})
        token = body.get("token", "")
        if token not in db["admin_tokens"] or db["admin_tokens"][token]["used"]:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Token inválido o ya usado"})
        
        db["admin_tokens"][token]["used"] = True
        db["admin_tokens"][token]["used_by"] = auth
        db["users"][auth]["role"] = "admin"
        save_db(db)
        return {"ok": True, "message": "Ahora eres administrador", "data": {"currentUser": db["users"][auth]}}

    return JSONResponse(status_code=400, content={"ok": False, "message": "Action unknown"})

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}
