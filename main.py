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

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key) if url and key else None

@app.post("/api/v1/orders")
async def process_order(payload: dict):
    print(f"DEBUG: Received payload: {payload}")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        # Extract data (Now including table_number!)
        table_number = int(payload.get("table_number", 0))
        guest_count = payload.get("guest_count", 1)
        items = payload.get("items", [])
        
        # Prepare Order
        order_data = {"table_number": table_number, "guest_count": guest_count}
        print(f"DEBUG: Inserting order: {order_data}")
        
        order_response = supabase.table("orders").insert(order_data).execute()
        order_id = order_response.data[0]["id"]
        print(f"DEBUG: Order created with ID: {order_id}")

        # Prepare Items
        if items:
            formatted_items = [
                {
                    "order_id": order_id, 
                    "menu_item_id": item.get("id"),
                    "customer_note": item.get("note", ""), 
                    "status": "Placed"
                }
                for item in items
            ]
            print(f"DEBUG: Inserting items: {formatted_items}")
            supabase.table("order_items").insert(formatted_items).execute()
            
        return {"status": "success", "order_id": order_id}
        
    except Exception as e:
        print(f"DEBUG: CRITICAL ERROR - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/orders")
async def get_orders():
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    try:
        # Fetch all orders (newest first)
        orders_response = supabase.table("orders").select("*").order("created_at", desc=True).execute()
        orders = orders_response.data
        
        # Fetch all items
        items_response = supabase.table("order_items").select("*").execute()
        items = items_response.data
        
        # Combine items into their respective orders
        for order in orders:
            order["items"] = [item for item in items if item["order_id"] == order["id"]]
            
        return {"status": "success", "data": orders}
        
    except Exception as e:
        print(f"DEBUG: Fetch error - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
