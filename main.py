import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

app = FastAPI(title="Hafawa Ordering API")

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

if not url or not key:
    supabase = None
else:
    supabase = create_client(url, key)

@app.post("/api/v1/orders")
async def process_order(payload: dict):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        guest_count = payload.get("guest_count", 1)
        items = payload.get("items", [])
        
        # CHANGED: table_number is now 0 (integer) instead of "N/A" (text)
        order_data = {"table_number": 0, "guest_count": guest_count}
        
        order_response = supabase.table("orders").insert(order_data).execute()
        
        if not order_response.data:
            raise Exception("Failed to insert order")
            
        order_id = order_response.data[0]["id"]

        if items:
            formatted_items = [
                {
                    "order_id": order_id, 
                    "item_name": item.get("name", "Unknown"), 
                    "customer_note": item.get("note", ""), 
                    "status": "Placed"
                }
                for item in items
            ]
            supabase.table("order_items").insert(formatted_items).execute()
            
        return {"status": "success", "order_id": order_id}
        
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
