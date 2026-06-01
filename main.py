import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Hafawa Ordering API")

# Allow the frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database Connection
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.post("/api/v1/orders")
async def process_order(payload: dict):
    # 1. Insert the parent order
    order_response = supabase.table("orders").insert({
        "table_number": payload["table_number"],
        "guest_count": payload["guest_count"],
        "allergens_note": payload["allergens_note"]
    }).execute()
    
    order_id = order_response.data[0]["id"]

    # 2. Insert the individual items
    formatted_items = [
        {
            "order_id": order_id,
            "menu_item_id": item.get("id"),
            "customer_note": item.get("note", ""),
            "status": "Placed"
        }
        for item in payload["items"]
    ]
    
    supabase.table("order_items").insert(formatted_items).execute()
    return {"status": "success", "order_id": order_id}
