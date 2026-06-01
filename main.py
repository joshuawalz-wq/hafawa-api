import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

app = FastAPI(title="Hafawa Ordering API")

# Updated CORS Middleware to prevent blocking requests from Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Initialize Database Connection
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.post("/api/v1/orders")
async def process_order(payload: dict):
    # 1. Safely extract data sent from the React app
    # We use .get() so it doesn't crash if a field is missing
    guest_count = payload.get("guest_count", 1)
    items = payload.get("items", [])
    
    # 2. Insert the parent order
    # Defaulting table_number to 'N/A' since frontend doesn't send it yet
    order_data = {
        "table_number": "N/A", 
        "guest_count": guest_count
    }
    
    order_response = supabase.table("orders").insert(order_data).execute()
    
    # Check if we got an order ID back
    if not order_response.data:
        return {"status": "error", "message": "Failed to create order"}
        
    order_id = order_response.data[0]["id"]

    # 3. Insert individual items
    if items:
        formatted_items = [
            {
                "order_id": order_id,
                "item_name": item.get("name", "Unknown Item"),
                "customer_note": item.get("note", ""),
                "status": "Placed"
            }
            for item in items
        ]
        
        supabase.table("order_items").insert(formatted_items).execute()
        
    return {"status": "success", "order_id": order_id}
