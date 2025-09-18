import streamlit as st
import datetime
import pytz
import requests
import time
import pandas as pd
import threading
from typing import Dict, Any, Tuple, List
from config import config
from utils import format_indian_currency, get_state_coordinates
import plotly.express as px

GRAPHQL_ENDPOINT = config.GRAPHQL_ENDPOINT
HEADERS = config.HEADERS
TARGET_TAGS = config.TARGET_TAGS

# ─── Page & CSS ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="18 Hours Sale Dashboard", page_icon="📊", layout="wide")

# Initialize session state for caching
if 'main_data' not in st.session_state:
    st.session_state.main_data = None
if 'sku_data' not in st.session_state:
    st.session_state.sku_data = None
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = None
if 'state_data' not in st.session_state:
    st.session_state.state_data = None

# Last update timestamps
if 'last_main_update' not in st.session_state:
    st.session_state.last_main_update = None
if 'last_sku_update' not in st.session_state:
    st.session_state.last_sku_update = None
if 'last_map_update' not in st.session_state:
    st.session_state.last_map_update = None
if 'last_customer_update' not in st.session_state:
    st.session_state.last_customer_update = None
if 'last_state_update' not in st.session_state:
    st.session_state.last_state_update = None

# Loading states
if 'main_loading' not in st.session_state:
    st.session_state.main_loading = False
if 'sku_loading' not in st.session_state:
    st.session_state.sku_loading = False
if 'map_loading' not in st.session_state:
    st.session_state.map_loading = False
if 'customer_loading' not in st.session_state:
    st.session_state.customer_loading = False
if 'state_loading' not in st.session_state:
    st.session_state.state_loading = False
if 'category_data' not in st.session_state:
    st.session_state.category_data = None
if 'last_category_update' not in st.session_state:
    st.session_state.last_category_update = None
if 'category_loading' not in st.session_state:
    st.session_state.category_loading = False

st.sidebar.markdown("### Settings")
auto_refresh = st.sidebar.checkbox("Auto-refresh enabled", value=True)

# Refresh intervals
intervals = config.REFRESH_INTERVALS
main_refresh_interval = intervals["main"]
sku_refresh_interval = intervals["sku"]
map_refresh_interval = intervals["map"]
customer_refresh_interval = intervals["customer"]
state_refresh_interval = intervals["state"]
category_refresh_interval = 300  # 5 minutes

st.sidebar.markdown("### Refresh Intervals")
st.sidebar.info(f"""
**Main Metrics:** Every {main_refresh_interval} seconds
- Total Orders & Sales
- Tagged Orders & Sales  
- Recent Carts & Additional Metrics

**SKU Data:** Every {sku_refresh_interval//60} minutes
- Top 10 Best-Selling SKUs

**Customer Analysis:** Every {customer_refresh_interval//60} minutes
- New vs Returning Customers

**Geographic Data:** Every {map_refresh_interval//60} minutes
- India Map & State Performance

**State Performance:** Every {state_refresh_interval//60} minutes
- Top 10 Performing States
""")

st.sidebar.markdown("### About Metrics")
st.sidebar.info("""
**Primary Metrics:**
• Orders Placed: Paid orders with campaign tag since campaign start
• Sale Revenue: Line-item revenue from tagged paid orders
• Recent Carts: Abandoned carts (last 30 min)

**Additional Metrics:**
• Average Order Value
• Unique Customers
• Campaign Conversion Rate
• Orders per Customer

**Analysis Sections:**
• Customer Segmentation: New vs Returning
• Geographic Distribution: State-wise performance
• Product Performance: Top-selling SKUs
""")

# 1. UPDATE THE CSS STYLING (replace the existing CSS section)
st.markdown("""
<style>
  .main-header { 
    text-align: center; 
    font-size: 2.5rem; 
    color: #1f77b4; 
    margin-bottom: 2rem; 
    font-weight: 600;
    letter-spacing: -0.5px;
  }
  .counter-container {
    background: linear-gradient(135deg, #2E006B, #415BFF);
    padding: 1.5rem; 
    border-radius: 12px; 
    text-align: center; 
    margin: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  .counter-title { 
    font-size: 1.1rem; 
    color: #fff; 
    margin-bottom: 0.5rem; 
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .counter-value { 
    font-size: 2.2rem; 
    color: #FFD700; 
    font-weight: 700;
    margin: 0.5rem 0;
  }
  .counter-subtitle { 
    font-size: 0.85rem; 
    color: rgba(255,255,255,0.8); 
    font-weight: 400;
  }
  .section-header {
    font-size: 1.4rem;
    color: #ffffff;
    margin: 2rem 0 1rem 0;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .status-indicator {
    position: fixed; 
    top: 15px; 
    right: 60px;
    background: #28a745; 
    color: #fff; 
    padding: 8px 16px; 
    border-radius: 20px;
    z-index: 1000;
    font-size: 0.85rem;
    box-shadow: 0 3px 6px rgba(0,0,0,0.2);
    font-weight: 500;
  }
  .loading-indicator {
    position: fixed; 
    top: 15px; 
    right: 60px;
    background: #ff6b35; 
    color: #fff; 
    padding: 8px 16px; 
    border-radius: 20px;
    z-index: 1001;
    animation: pulse 1.5s infinite;
    font-size: 0.85rem;
    box-shadow: 0 3px 6px rgba(0,0,0,0.3);
    font-weight: 500;
  }
  @keyframes pulse {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.05); }
    100% { opacity: 1; transform: scale(1); }
  }
  .info-icon {
    position: fixed;
    top: 80px;
    right: 30px;
    background: #007bff;
    color: white;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex !important;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 9999;
    font-size: 1.1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    border: 3px solid white;
    font-weight: bold;
    transition: all 0.3s ease;
  }
  .info-icon:hover {
    background: #0056b3;
    transform: scale(1.1);
  }
  .info-tooltip {
    position: fixed;
    top: 120px;
    right: 30px;
    background: rgba(0,0,0,0.95);
    color: white;
    padding: 15px 18px;
    border-radius: 10px;
    font-size: 0.85rem;
    max-width: 280px;
    z-index: 9998;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    line-height: 1.5;
    border: 1px solid rgba(255,255,255,0.2);
  }
  .info-icon:hover + .info-tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateY(-5px);
  }
  .last-updated {
    text-align: center; 
    color: #666; 
    margin-top: 1rem; 
    font-style: italic;
  }
  .error-message {
    background: #f8d7da; 
    color: #721c24; 
    padding: 1rem; 
    border-radius: 5px;
  }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])  # Creates 3 equal columns
with col2:  # Use the middle column
    st.image("https://d3ve5430cjjm40.cloudfront.net/18Hour_Logo-01.png", width=300)

# Add spacing after image
st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Campaign Performance Dashboard</h1>', unsafe_allow_html=True)

# ─── Helper Functions ────────────────────────────────────────────────────────



def get_additional_metrics(start_iso: str, end_iso: str, total_orders: int, total_sales: float) -> Dict[str, float]:
    """Calculate additional metrics"""
    aov = total_sales / total_orders if total_orders else 0
    uniq = get_unique_customers_count(start_iso, end_iso)
    opc = total_orders / uniq if uniq else 0
    return {
        "avg_order_value": aov,
        "unique_customers": uniq,
        "orders_per_customer": opc
    }

def get_timeframe():
    """Get the configured timeframe for the sale"""
    return config.get_timeframe()

def fetch_orders_metrics(query_filter: str) -> Tuple[int, float]:
    """Fetch order count and revenue with improved error handling"""
    total_count = 0
    total_revenue = 0.0
    cursor = None
    retries = 3

    while True:
        for attempt in range(retries):
            try:
                graphql_query = f'''
                query ($cursor: String) {{
                  orders(
                    first: 250,
                    after: $cursor,
                    query: "{query_filter}",
                    sortKey: CREATED_AT
                  ) {{
                    pageInfo {{ hasNextPage endCursor }}
                    edges {{
                      node {{
                        currentTotalPriceSet {{ shopMoney {{ amount }} }}
                      }}
                    }}
                  }}
                }}
                '''
                payload = {"query": graphql_query, "variables": {"cursor": cursor}}
                resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                data = resp.json()["data"]["orders"]
                break
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(1 * (attempt + 1))

        for edge in data["edges"]:
            total_count += 1
            total_revenue += float(edge["node"]["currentTotalPriceSet"]["shopMoney"]["amount"])

        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]

    return total_count, total_revenue

def fetch_category_data(start_iso: str, end_iso: str, target_tags: List[str]) -> Dict[str, Any]:
    """Fetch category-wise sales data from tagged orders"""
    tag_query = " OR ".join(f"tag:{t}" for t in target_tags)
    date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
    paid_query = "financial_status:paid"
    query_filter = f"({tag_query}) AND {date_query} AND {paid_query}"
    
    category_data = {}
    all_skus_by_category = {}  # For dropdown functionality
    total_revenue = 0
    cursor = None
    
    while True:
        try:
            graphql_query = f'''
            query ($cursor: String) {{
              orders(
                first: 250,
                after: $cursor,
                query: "{query_filter}",
                sortKey: CREATED_AT
              ) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{
                  node {{
                    lineItems(first: 50) {{
                      edges {{
                        node {{
                          sku
                          title
                          quantity
                          originalTotalSet {{ shopMoney {{ amount }} }}
                          product {{
                            productType
                            vendor
                            tags
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            '''
            payload = {"query": graphql_query, "variables": {"cursor": cursor}}
            resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["orders"]

            for edge in data["edges"]:
                line_items = edge["node"]["lineItems"]["edges"]
                for item_edge in line_items:
                    item = item_edge["node"]
                    product = item.get("product", {})
                    
                    sku = item.get("sku") or "UNKNOWN"
                    title = item.get("title") or "Unknown Product"
                    quantity = int(item.get("quantity", 1))
                    revenue = float(item.get("originalTotalSet", {}).get("shopMoney", {}).get("amount", 0))
                    category = product.get("productType") or "Uncategorized"
                    
                    total_revenue += revenue
                    
                    # Aggregate by category
                    if category not in category_data:
                        category_data[category] = {"quantity": 0, "revenue": 0.0}
                        all_skus_by_category[category] = {}
                    
                    category_data[category]["quantity"] += quantity
                    category_data[category]["revenue"] += revenue
                    
                    # Store SKU-level data for dropdown functionality
                    if sku not in all_skus_by_category[category]:
                        all_skus_by_category[category][sku] = {"title": title, "quantity": 0, "revenue": 0.0}
                    
                    all_skus_by_category[category][sku]["quantity"] += quantity
                    all_skus_by_category[category][sku]["revenue"] += revenue

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
            
        except Exception as e:
            st.error(f"Error fetching category data: {str(e)}")
            break
    
    # Calculate category shares
    for category in category_data:
        category_data[category]["share_percentage"] = (category_data[category]["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "category_data": category_data,
        "all_skus_by_category": all_skus_by_category,
        "total_revenue": total_revenue
    }

def fetch_category_metrics() -> Dict[str, Any]:
    """Fetch category metrics separately"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        category_info = fetch_category_data(start_iso, end_iso, TARGET_TAGS)
        
        return {
            "category_info": category_info,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "category_info": {},
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

def get_recent_cart_activity(start_iso: str, end_iso: str) -> int:
    """Get recent cart activity with improved error handling"""
    try:
        url = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}/checkouts.json"
        params = {
            "created_at_min": start_iso,
            "created_at_max": end_iso,
            "limit": 250
        }
        headers = {"X-Shopify-Access-Token": ACCESS_TOKEN}
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        checkouts = r.json().get("checkouts", [])
        return len([c for c in checkouts if not c.get("completed_at")])
    except Exception:
        return 0

def get_unique_customers_count(start_iso: str, end_iso: str) -> int:
    """Get unique customer count with improved pagination"""
    date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
    paid_query = "financial_status:paid"
    query_filter = f"{date_query} AND {paid_query}"

    customers = set()
    cursor = None

    while True:
        try:
            graphql_query = f'''
            query ($cursor: String) {{
              orders(
                first: 250,
                after: $cursor,
                query: "{query_filter}",
                sortKey: CREATED_AT
              ) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{ node {{ customer {{ id }} }} }}
              }}
            }}
            '''
            payload = {"query": graphql_query, "variables": {"cursor": cursor}}
            resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["orders"]

            for edge in data["edges"]:
                cust = edge["node"].get("customer") or {}
                if cust.get("id"):
                    customers.add(cust["id"])

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
        except Exception:
            break

    return len(customers)

def get_top_skus_improved(start_iso: str, end_iso: str, target_tags: List[str]) -> List[Tuple[str, int, float]]:
    """Get top SKUs with quantity and revenue data, sorted by revenue"""
    sku_data = {}  # Changed to store both quantity and revenue
    tag_query = " OR ".join(f"tag:{t}" for t in target_tags)
    date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
    paid_query = "financial_status:paid"
    query_filter = f"({tag_query}) AND {date_query} AND {paid_query}"
    
    cursor = None
    
    while True:
        try:
            graphql_query = f'''
            query ($cursor: String) {{
              orders(
                first: 250,
                after: $cursor,
                query: "{query_filter}",
                sortKey: CREATED_AT
              ) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{
                  node {{
                    lineItems(first: 50) {{
                      edges {{
                        node {{
                          sku
                          quantity
                          originalTotalSet {{ shopMoney {{ amount }} }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            '''
            payload = {"query": graphql_query, "variables": {"cursor": cursor}}
            resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["orders"]

            for edge in data["edges"]:
                line_items = edge["node"]["lineItems"]["edges"]
                for item_edge in line_items:
                    item = item_edge["node"]
                    sku = item.get("sku") or "UNKNOWN"
                    qty = int(item.get("quantity", 1))
                    revenue = float(item.get("originalTotalSet", {}).get("shopMoney", {}).get("amount", 0))
                    
                    if sku not in sku_data:
                        sku_data[sku] = {"quantity": 0, "revenue": 0.0}
                    
                    sku_data[sku]["quantity"] += qty
                    sku_data[sku]["revenue"] += revenue

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
            
        except Exception as e:
            st.error(f"Error fetching SKU data: {str(e)}")
            break

    # Sort by revenue (descending) and return top 10
    top_10 = sorted(
        [(sku, data["quantity"], data["revenue"]) for sku, data in sku_data.items()],
        key=lambda x: x[2],  # Sort by revenue (index 2)
        reverse=True
    )[:10]
    
    return top_10

def fetch_geographic_data(start_iso: str, end_iso: str, target_tags: List[str]) -> Dict[str, Any]:
    """Fetch geographic data for mapping and state analysis"""
    tag_query = " OR ".join(f"tag:{t}" for t in target_tags)
    date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
    paid_query = "financial_status:paid"
    query_filter = f"({tag_query}) AND {date_query} AND {paid_query}"
    
    state_data = {}
    order_locations = []  # For actual map plotting
    total_revenue = 0
    total_quantity = 0
    cursor = None
    
    while True:
        try:
            graphql_query = f'''
            query ($cursor: String) {{
              orders(
                first: 250,
                after: $cursor,
                query: "{query_filter}",
                sortKey: CREATED_AT
              ) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{
                  node {{
                    id
                    name
                    shippingAddress {{
                      address1
                      address2
                      city
                      province
                      provinceCode
                      zip
                      country
                      countryCodeV2
                      latitude
                      longitude
                    }}
                    currentTotalPriceSet {{ shopMoney {{ amount }} }}
                    lineItems(first: 50) {{
                      edges {{
                        node {{
                          quantity
                          title
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            '''
            payload = {"query": graphql_query, "variables": {"cursor": cursor}}
            resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["orders"]

            for edge in data["edges"]:
                order = edge["node"]
                shipping_addr = order.get("shippingAddress")
                
                if shipping_addr:
                    state = shipping_addr.get("province")
                    city = shipping_addr.get("city")
                    latitude = shipping_addr.get("latitude")
                    longitude = shipping_addr.get("longitude")
                    revenue = float(order["currentTotalPriceSet"]["shopMoney"]["amount"])
                    
                    # Calculate total quantity for this order
                    order_quantity = sum(
                        int(item["node"]["quantity"]) 
                        for item in order["lineItems"]["edges"]
                    )
                    
                    # Store individual order location for mapping
                    if latitude and longitude:
                        try:
                            lat_float = float(latitude)
                            lon_float = float(longitude)
                            # Validate coordinates are within India bounds
                            if 6.0 <= lat_float <= 37.0 and 68.0 <= lon_float <= 97.0:
                                order_locations.append({
                                    "lat": lat_float,
                                    "lon": lon_float,
                                    "order_id": order["name"],
                                    "city": city or "Unknown",
                                    "state": state or "Unknown",
                                    "revenue": revenue,
                                    "quantity": order_quantity
                                })
                        except (ValueError, TypeError):
                            pass  # Skip invalid coordinates
                    
                    # Aggregate by state for state analysis
                    if state:
                        if state not in state_data:
                            state_data[state] = {"revenue": 0, "quantity": 0, "orders": 0}
                        
                        state_data[state]["revenue"] += revenue
                        state_data[state]["quantity"] += order_quantity
                        state_data[state]["orders"] += 1
                        
                        total_revenue += revenue
                        total_quantity += order_quantity

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
            
        except Exception as e:
            st.error(f"Error fetching geographic data: {str(e)}")
            break
    
    # Calculate percentages and prepare data
    for state in state_data:
        state_data[state]["revenue_percentage"] = (state_data[state]["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        state_data[state]["quantity_percentage"] = (state_data[state]["quantity"] / total_quantity * 100) if total_quantity > 0 else 0
    
    return {
        "state_data": state_data,
        "order_locations": order_locations,  # Actual order coordinates
        "total_revenue": total_revenue,
        "total_quantity": total_quantity
    }

def fetch_customer_segmentation(start_iso: str, end_iso: str) -> Dict[str, Any]:
    """Fetch new vs returning customer data"""
    date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
    paid_query = "financial_status:paid"
    query_filter = f"{date_query} AND {paid_query}"
    
    customer_data = {}
    cursor = None
    
    while True:
        try:
            graphql_query = f'''
            query ($cursor: String) {{
              orders(
                first: 250,
                after: $cursor,
                query: "{query_filter}",
                sortKey: CREATED_AT
              ) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{
                  node {{
                    customer {{
                      id
                      createdAt
                    }}
                    createdAt
                  }}
                }}
              }}
            }}
            '''
            payload = {"query": graphql_query, "variables": {"cursor": cursor}}
            resp = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()["data"]["orders"]

            for edge in data["edges"]:
                order = edge["node"]
                customer = order.get("customer")
                
                if customer and customer.get("id"):
                    customer_id = customer["id"]
                    customer_created = customer.get("createdAt")
                    order_created = order.get("createdAt")
                    
                    # If customer was created very close to order time, consider as new
                    if customer_created and order_created:
                        customer_dt = datetime.datetime.fromisoformat(customer_created.replace('Z', '+00:00'))
                        order_dt = datetime.datetime.fromisoformat(order_created.replace('Z', '+00:00'))
                        
                        # If customer created within 1 hour of order, consider new
                        time_diff = (order_dt - customer_dt).total_seconds() / 3600
                        
                        if customer_id not in customer_data:
                            customer_data[customer_id] = {
                                "is_new": time_diff <= 1,
                                "orders": 0
                            }
                        
                        customer_data[customer_id]["orders"] += 1

            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
            
        except Exception as e:
            st.error(f"Error fetching customer data: {str(e)}")
            break
    
    # Calculate totals
    new_customers = sum(1 for data in customer_data.values() if data["is_new"])
    returning_customers = len(customer_data) - new_customers
    new_customer_orders = sum(data["orders"] for data in customer_data.values() if data["is_new"])
    returning_customer_orders = sum(data["orders"] for data in customer_data.values() if not data["is_new"])
    
    return {
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "new_customer_orders": new_customer_orders,
        "returning_customer_orders": returning_customer_orders,
        "total_customers": len(customer_data)
    }

def fetch_main_metrics() -> Dict[str, Any]:
    """Fetch main dashboard metrics (orders, sales, etc.)"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        
        date_query = f"created_at:>'{start_iso}' AND created_at:<='{end_iso}'"
        paid_query = "financial_status:paid"
        overall_filt = f"{date_query} AND {paid_query}"
        tag_query = " OR ".join(f"tag:{t}" for t in TARGET_TAGS)
        tagged_filt = f"({tag_query}) AND {date_query} AND {paid_query}"

        total_orders, total_sales = fetch_orders_metrics(overall_filt)
        tag_orders, tag_sales = fetch_orders_metrics(tagged_filt)
        
        now_utc = datetime.datetime.now(pytz.UTC)
        recent_carts = get_recent_cart_activity(
            (now_utc - datetime.timedelta(minutes=30)).isoformat(),
            now_utc.isoformat()
        )

        additional_metrics = get_additional_metrics(start_iso, end_iso, total_orders, total_sales)
        conversion_rate = (tag_orders / total_orders * 100) if total_orders else 0

        return {
            "total_orders": total_orders,
            "total_sales": total_sales,
            "tag_orders": tag_orders,
            "tag_sales": tag_sales,
            "recent_carts": recent_carts,
            "additional_metrics": additional_metrics,
            "conversion_rate": conversion_rate,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

def fetch_sku_metrics() -> Dict[str, Any]:
    """Fetch SKU data with revenue information"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        top_skus = get_top_skus_improved(start_iso, end_iso, TARGET_TAGS)
        
        return {
            "top_skus": top_skus,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "top_skus": [],
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

def fetch_map_metrics() -> Dict[str, Any]:
    """Fetch geographic data for map visualization"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        geo_data = fetch_geographic_data(start_iso, end_iso, TARGET_TAGS)
        
        return {
            "geographic_data": geo_data,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "geographic_data": {},
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

def fetch_customer_metrics() -> Dict[str, Any]:
    """Fetch customer segmentation data"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        customer_seg = fetch_customer_segmentation(start_iso, end_iso)
        
        return {
            "customer_segmentation": customer_seg,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "customer_segmentation": {},
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

def fetch_state_metrics() -> Dict[str, Any]:
    """Fetch state performance data"""
    try:
        start_iso, end_iso, now_ist = get_timeframe()
        geo_data = fetch_geographic_data(start_iso, end_iso, TARGET_TAGS)
        
        return {
            "state_performance": geo_data,
            "now_ist": now_ist,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "state_performance": {},
            "now_ist": datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        }

# ─── Refresh Logic Functions ──────────────────────────────────────────────────

def should_refresh_main_data() -> bool:
    if st.session_state.last_main_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_main_update).total_seconds()
    return time_since_update >= main_refresh_interval

def should_refresh_sku_data() -> bool:
    if st.session_state.last_sku_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_sku_update).total_seconds()
    return time_since_update >= sku_refresh_interval

def should_refresh_map_data() -> bool:
    if st.session_state.last_map_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_map_update).total_seconds()
    return time_since_update >= map_refresh_interval

def should_refresh_customer_data() -> bool:
    if st.session_state.last_customer_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_customer_update).total_seconds()
    return time_since_update >= customer_refresh_interval

def should_refresh_state_data() -> bool:
    if st.session_state.last_state_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_state_update).total_seconds()
    return time_since_update >= state_refresh_interval

def should_refresh_category_data() -> bool:
    if st.session_state.last_category_update is None:
        return True
    time_since_update = (datetime.datetime.now() - st.session_state.last_category_update).total_seconds()
    return time_since_update >= category_refresh_interval

# ─── Main Application ─────────────────────────────────────────────────────────

def main():
    # Initialize data on first load only
    if st.session_state.main_data is None and not st.session_state.main_loading:
        st.session_state.main_loading = True
        st.session_state.main_data = fetch_main_metrics()
        st.session_state.last_main_update = datetime.datetime.now()
        st.session_state.main_loading = False

    if st.session_state.sku_data is None and not st.session_state.sku_loading:
        st.session_state.sku_loading = True
        st.session_state.sku_data = fetch_sku_metrics()
        st.session_state.last_sku_update = datetime.datetime.now()
        st.session_state.sku_loading = False

    if st.session_state.map_data is None and not st.session_state.map_loading:
        st.session_state.map_loading = True
        st.session_state.map_data = fetch_map_metrics()
        st.session_state.last_map_update = datetime.datetime.now()
        st.session_state.map_loading = False

    if st.session_state.customer_data is None and not st.session_state.customer_loading:
        st.session_state.customer_loading = True
        st.session_state.customer_data = fetch_customer_metrics()
        st.session_state.last_customer_update = datetime.datetime.now()
        st.session_state.customer_loading = False

    if st.session_state.state_data is None and not st.session_state.state_loading:
        st.session_state.state_loading = True
        st.session_state.state_data = fetch_state_metrics()
        st.session_state.last_state_update = datetime.datetime.now()
        st.session_state.state_loading = False

    if st.session_state.category_data is None and not st.session_state.category_loading:
        st.session_state.category_loading = True
        st.session_state.category_data = fetch_category_metrics()
        st.session_state.last_category_update = datetime.datetime.now()
        st.session_state.category_loading = False


    # Show loading indicators
    loading_status = []
    if st.session_state.main_loading:
        loading_status.append("📊 Main")
    if st.session_state.sku_loading:
        loading_status.append("🏆 SKUs")
    if st.session_state.map_loading:
        loading_status.append("🗺️ Map")
    if st.session_state.customer_loading:
        loading_status.append("👥 Customers")
    if st.session_state.state_loading:
        loading_status.append("🏛️ States")
    if st.session_state.category_loading:
        loading_status.append("🏷️ Categories")
    
    if loading_status:
        st.markdown(f'<div class="loading-indicator">🔄 {", ".join(loading_status)}</div>', unsafe_allow_html=True)
    elif auto_refresh:
        st.markdown('<div class="status-indicator">✅ Live</div>', unsafe_allow_html=True)

    # Info tooltip - ALWAYS DISPLAY
    tooltip_lines = []
    
    if st.session_state.last_main_update:
        main_seconds_ago = int((datetime.datetime.now() - st.session_state.last_main_update).total_seconds())
        main_next_refresh = max(0, main_refresh_interval - main_seconds_ago)
        tooltip_lines.append(f"📊 Main: {main_seconds_ago}s ago | Next: {main_next_refresh}s")
    
    if st.session_state.last_sku_update:
        sku_seconds_ago = int((datetime.datetime.now() - st.session_state.last_sku_update).total_seconds())
        sku_next_refresh = max(0, sku_refresh_interval - sku_seconds_ago)
        sku_next_min = sku_next_refresh // 60
        sku_next_sec = sku_next_refresh % 60
        tooltip_lines.append(f"🏆 SKUs: {sku_seconds_ago}s ago | Next: {sku_next_min}m {sku_next_sec}s")
    
    if st.session_state.last_customer_update:
        cust_seconds_ago = int((datetime.datetime.now() - st.session_state.last_customer_update).total_seconds())
        cust_next_refresh = max(0, customer_refresh_interval - cust_seconds_ago)
        cust_next_min = cust_next_refresh // 60
        cust_next_sec = cust_next_refresh % 60
        tooltip_lines.append(f"👥 Customers: {cust_seconds_ago}s ago | Next: {cust_next_min}m {cust_next_sec}s")
    
    if st.session_state.last_map_update:
        map_seconds_ago = int((datetime.datetime.now() - st.session_state.last_map_update).total_seconds())
        map_next_refresh = max(0, map_refresh_interval - map_seconds_ago)
        map_next_min = map_next_refresh // 60
        tooltip_lines.append(f"🗺️ Map: {map_seconds_ago}s ago | Next: {map_next_min}m")
    
    if st.session_state.last_state_update:
        state_seconds_ago = int((datetime.datetime.now() - st.session_state.last_state_update).total_seconds())
        state_next_refresh = max(0, state_refresh_interval - state_seconds_ago)
        state_next_min = state_next_refresh // 60
        tooltip_lines.append(f"🏛️ States: {state_seconds_ago}s ago | Next: {state_next_min}m")

    if st.session_state.last_category_update:
        cat_seconds_ago = int((datetime.datetime.now() - st.session_state.last_category_update).total_seconds())
        cat_next_refresh = max(0, category_refresh_interval - cat_seconds_ago)
        cat_next_min = cat_next_refresh // 60
        cat_next_sec = cat_next_refresh % 60
        tooltip_lines.append(f"🏷️ Categories: {cat_seconds_ago}s ago | Next: {cat_next_min}m {cat_next_sec}s")
    
    # Always show the info icon
    tooltip_text = "<br>".join(tooltip_lines) if tooltip_lines else "Dashboard Status Information"
    if auto_refresh:
        tooltip_text += "<br>🔄 Auto-refresh: ON"
    else:
        tooltip_text += "<br>⏸️ Auto-refresh: OFF"
        
    st.markdown(f'''
        <div class="info-icon">ℹ️</div>
        <div class="info-tooltip">{tooltip_text}</div>
    ''', unsafe_allow_html=True)

    # Use cached data
    main_data = st.session_state.main_data
    sku_data = st.session_state.sku_data
    map_data = st.session_state.map_data
    customer_data = st.session_state.customer_data
    state_data = st.session_state.state_data
    
    if not main_data or not main_data.get("success"):
        error_msg = main_data.get("error", "Unknown error") if main_data else "No main data available"
        st.markdown(f'<div class="error-message">⚠️ Main Data Error: {error_msg}</div>', unsafe_allow_html=True)
        
        if st.button("🔄 Retry Main Data", key="retry_main_button"):
            st.session_state.main_data = None
            st.session_state.last_main_update = None
            st.rerun()
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Orders Placed</div>
            <div class="counter-value">{main_data['tag_orders']:,}</div>
            <div class="counter-subtitle">Campaign orders since start</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Sale Revenue</div>
            <div class="counter-value">{format_indian_currency(main_data['tag_sales'])}</div>
            <div class="counter-subtitle">Total campaign revenue</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Recent Carts</div>
            <div class="counter-value">{main_data['recent_carts']}</div>
            <div class="counter-subtitle">Abandoned carts (30 min)</div>
            </div>
        """, unsafe_allow_html=True)

    # Additional metrics
    st.markdown("---")
    st.markdown('<div class="section-header">Performance Analytics</div>', unsafe_allow_html=True)
    am1, am2, am3, am4 = st.columns(4)
    
    with am1:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Avg Order Value</div>
            <div class="counter-value">{format_indian_currency(main_data['additional_metrics']['avg_order_value'])}</div>
            <div class="counter-subtitle">Revenue per order</div>
            </div>
        """, unsafe_allow_html=True)

    with am2:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Unique Customers</div>
            <div class="counter-value">{main_data['additional_metrics']['unique_customers']:,}</div>
            <div class="counter-subtitle">Distinct buyers</div>
            </div>
        """, unsafe_allow_html=True)

    with am3:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Campaign Conversion</div>
            <div class="counter-value">{main_data['conversion_rate']:.1f}%</div>
            <div class="counter-subtitle">Tagged order rate</div>
            </div>
        """, unsafe_allow_html=True)

    with am4:
        st.markdown(f"""
            <div class="counter-container">
            <div class="counter-title">Orders per Customer</div>
            <div class="counter-value">{main_data['additional_metrics']['orders_per_customer']:.2f}</div>
            <div class="counter-subtitle">Average orders</div>
            </div>
        """, unsafe_allow_html=True)

    # Customer Segmentation Section
    st.markdown("---")
    st.markdown('<div class="section-header">Customer Analysis</div>', unsafe_allow_html=True)
    
    if customer_data and customer_data.get("success"):
        cust_seg = customer_data["customer_segmentation"]
        
        cust_col1, cust_col2, cust_col3 = st.columns(3)
        
        with cust_col1:
            st.markdown(f"""
                <div class="counter-container">
                  <div class="counter-title">New Customers</div>
                  <div class="counter-value">{cust_seg.get('new_customers', 0):,}</div>
                  <div class="counter-subtitle">{cust_seg.get('new_customer_orders', 0):,} orders</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cust_col2:
            st.markdown(f"""
                <div class="counter-container">
                  <div class="counter-title">Returning Customers</div>
                  <div class="counter-value">{cust_seg.get('returning_customers', 0):,}</div>
                  <div class="counter-subtitle">{cust_seg.get('returning_customer_orders', 0):,} orders</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cust_col3:
            total_customers = cust_seg.get('total_customers', 0)
            new_customers = cust_seg.get('new_customers', 0)
            new_customer_percentage = (new_customers / total_customers * 100) if total_customers > 0 else 0
            
            st.markdown(f"""
                <div class="counter-container">
                  <div class="counter-title">New Customer %</div>
                  <div class="counter-value">{new_customer_percentage:.1f}%</div>
                  <div class="counter-subtitle">New vs Total</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Customer segmentation data loading...")

    # Top SKUs section
    st.markdown("---")
    st.markdown('<div class="section-header">Product Performance</div>', unsafe_allow_html=True)

    if sku_data and sku_data.get("success") and sku_data['top_skus']:
        # Create DataFrame with SKU, Quantity, and Revenue
        sku_df = pd.DataFrame(sku_data['top_skus'], columns=["SKU", "Quantity", "Revenue"])
        
        # Format revenue for display
        sku_df_display = sku_df.copy()
        sku_df_display["Revenue"] = sku_df_display["Revenue"].apply(format_indian_currency)
        sku_df_display.index = range(1, len(sku_df_display) + 1)
        
        # Display table
        st.markdown("### Top 10 SKUs by Revenue")
        st.dataframe(sku_df_display, use_container_width=True)
        
        # Summary statistics
        total_quantity = sku_df['Quantity'].sum()
        total_revenue = sku_df['Revenue'].sum()
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Total Quantity (Top 10): {total_quantity:,} units")
        with col2:
            st.info(f"Total Revenue (Top 10): {format_indian_currency(total_revenue)}")
        
        # 4. ADD VISUALIZATION CHART
        st.markdown("### SKU Performance Analysis")
        
        # Prepare data for charts
        chart_data = sku_df.head(10).copy()  # Top 10 for better readability
        
        # Create two columns for different chart views
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Revenue by SKU")
            # Bar chart for revenue
            revenue_chart = chart_data.set_index("SKU")["Revenue"]
            st.bar_chart(revenue_chart, height=400)
        
        with chart_col2:
            st.markdown("#### Quantity vs Revenue")
            # Scatter plot to show relationship
            import plotly.express as px
            
            fig = px.scatter(
                chart_data, 
                x="Quantity", 
                y="Revenue",
                hover_data=["SKU"],
                title="SKU Performance: Quantity vs Revenue",
                labels={"Quantity": "Units Sold", "Revenue": "Revenue (₹)"}
            )
            
            # Customize the chart
            fig.update_traces(
                marker=dict(size=10, color='rgba(102, 126, 234, 0.8)', line=dict(width=2, color='white'))
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Alternative simpler chart if plotly doesn't work
        # st.markdown("#### Quantity Distribution")
        # quantity_chart = chart_data.set_index("SKU")["Quantity"]
        # st.bar_chart(quantity_chart, height=300)
        
    elif sku_data and not sku_data.get("success"):
        st.error(f"SKU Data Error: {sku_data.get('error', 'Unknown error')}")
        if st.button("Retry SKU Data", key="retry_sku_button"):
            st.session_state.sku_data = None
            st.session_state.last_sku_update = None
            st.rerun()
    else:
        st.warning("SKU data loading...")

    # Category Level Sales Section
    st.markdown("---")
    st.markdown('<div class="section-header">Category Level Sales</div>', unsafe_allow_html=True)

    if st.session_state.category_data and st.session_state.category_data.get("success"):
        category_info = st.session_state.category_data["category_info"]
        
        if category_info.get("category_data"):
            # Category Overview Cards
            st.markdown("### Category Performance Overview")
            
            # Prepare category data for display - FILTER OUT UNCATEGORIZED
            categories_list = []
            for category, data in category_info["category_data"].items():
                # SKIP "Uncategorized" from display but keep in calculations
                if category.lower() != "uncategorized":
                    categories_list.append({
                        "Category": category,
                        "Quantity": data["quantity"],
                        "Revenue": data["revenue"],
                        "Sale Share %": data["share_percentage"]  # This keeps original percentages
                    })
            
            # Sort by revenue descending
            categories_df = pd.DataFrame(categories_list)
            categories_df = categories_df.sort_values("Revenue", ascending=False)
            categories_df.index = range(1, len(categories_df) + 1)
            
            # Format for display
            categories_display = categories_df.copy()
            categories_display["Revenue"] = categories_display["Revenue"].apply(format_indian_currency)
            categories_display["Sale Share %"] = categories_display["Sale Share %"].apply(lambda x: f"{x:.1f}%")
            
            # Display category table (without Uncategorized)
            st.dataframe(categories_display, use_container_width=True)
            
            # Category summary stats (excluding Uncategorized)
            total_categories = len(categories_df)
            top_category = categories_df.iloc[0] if not categories_df.empty else None
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Categories", total_categories)
            with col2:
                if top_category is not None:
                    st.metric("Top Category", top_category["Category"])
            with col3:
                if top_category is not None:
                    st.metric("Top Category Share", f"{top_category['Sale Share %']:.1f}%")
            
            # Category Analysis Charts
            st.markdown("### Category Revenue Analysis")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("#### Revenue by Category")
                revenue_chart = categories_df.set_index("Category")["Revenue"]
                st.bar_chart(revenue_chart, height=400)
            
            with chart_col2:
                st.markdown("#### Category Share Distribution")
                import plotly.express as px
                
                # Pie chart WITH Uncategorized (for accurate data representation)
                all_categories_list = []
                for category, data in category_info["category_data"].items():
                    all_categories_list.append({
                        "Category": category,
                        "Sale Share %": data["share_percentage"]
                    })
                
                all_categories_pie = pd.DataFrame(all_categories_list)
                
                fig = px.pie(
                    all_categories_pie,
                    values="Sale Share %",
                    names="Category",
                    title="Category Revenue Share"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Category Performance Scatter Plot (reverted from line chart)
            st.markdown("### Category Performance Analysis")
            
            if len(categories_df) > 1:
                # Scatter plot showing Quantity vs Revenue for categories (excluding Uncategorized from visual)
                fig_scatter = px.scatter(
                    categories_df,
                    x="Quantity",
                    y="Revenue",
                    hover_data=["Category"],
                    title="Category Performance: Quantity vs Revenue",
                    labels={"Quantity": "Units Sold", "Revenue": "Revenue (₹)"}
                )
                
                # Customize the scatter plot
                fig_scatter.update_traces(
                    marker=dict(size=12, color='rgba(102, 126, 234, 0.8)', line=dict(width=2, color='white'))
                )
                fig_scatter.update_layout(
                    height=400,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Interactive Category Drill-down
            st.markdown("---")
            st.markdown("### Category Drill-Down Analysis")
            
            # Category selection dropdown - EXCLUDE UNCATEGORIZED
            available_categories = [cat for cat in category_info["all_skus_by_category"].keys() 
                                if cat.lower() != "uncategorized"]
            
            if available_categories:
                selected_category = st.selectbox(
                    "Select a category to view top SKUs:",
                    options=available_categories,
                    index=0
                )
                
                if selected_category and selected_category in category_info["all_skus_by_category"]:
                    category_skus = category_info["all_skus_by_category"][selected_category]
                    
                    # Prepare SKU data for selected category
                    sku_list = []
                    for sku, data in category_skus.items():
                        sku_list.append({
                            "SKU": sku,
                            "Quantity": data["quantity"],
                            "Revenue": data["revenue"]
                        })
                    
                    # Sort by revenue and take top 10
                    sku_df = pd.DataFrame(sku_list)
                    sku_df = sku_df.sort_values("Revenue", ascending=False).head(10)
                    sku_df.index = range(1, len(sku_df) + 1)
                    
                    # Display category-specific table
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"#### Top 10 SKUs in {selected_category}")
                        sku_display = sku_df.copy()
                        sku_display["Revenue"] = sku_display["Revenue"].apply(format_indian_currency)
                        st.dataframe(sku_display, use_container_width=True)
                    
                    with col2:
                        # Category stats
                        category_stats = category_info["category_data"][selected_category]
                        st.markdown(f"#### {selected_category} Statistics")
                        st.metric("Total Quantity", f"{category_stats['quantity']:,}")
                        st.metric("Total Revenue", format_indian_currency(category_stats['revenue']))
                        st.metric("Sale Contribution Share", f"{category_stats['share_percentage']:.1f}%")
                    
                    # Category-specific performance chart
                    if len(sku_df) > 1:
                        st.markdown(f"#### {selected_category} - SKU Performance")
                        
                        # Scatter plot for SKUs in selected category (reverted from line chart)
                        fig_sku = px.scatter(
                            sku_df,
                            x="Quantity",
                            y="Revenue",
                            hover_data=["SKU"],
                            title=f"SKU Performance in {selected_category}",
                            labels={"Quantity": "Units Sold", "Revenue": "Revenue (₹)"}
                        )
                        
                        fig_sku.update_traces(
                            marker=dict(size=12, color='rgba(255, 99, 132, 0.8)', line=dict(width=2, color='white'))
                        )
                        
                        fig_sku.update_layout(
                            height=400,
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig_sku, use_container_width=True)
            else:
                st.warning("No categorized products found. All products are marked as 'Uncategorized'.")
        
        else:
            st.warning("No category data available yet.")

    elif st.session_state.category_data and not st.session_state.category_data.get("success"):
        st.error(f"Category Data Error: {st.session_state.category_data.get('error', 'Unknown error')}")
        if st.button("Retry Category Data", key="retry_category_button"):
            st.session_state.category_data = None
            st.session_state.last_category_update = None
            st.rerun()
    else:
        st.warning("Category data loading...")

    if not categories_df.empty:
        visible_revenue = categories_df['Revenue'].sum()
        total_all_revenue = category_info.get('total_revenue', 0)
        uncategorized_revenue = total_all_revenue - visible_revenue
        
        st.markdown("---")
        st.markdown("#### Revenue Distribution")
        
        dist_col1, dist_col2, dist_col3 = st.columns(3)
        with dist_col1:
            st.metric("Categorized Revenue", format_indian_currency(visible_revenue))
        with dist_col2:
            st.metric("Uncategorized Revenue", format_indian_currency(uncategorized_revenue))
        with dist_col3:
            categorized_percentage = (visible_revenue / total_all_revenue * 100) if total_all_revenue > 0 else 0
            st.metric("Categorized %", f"{categorized_percentage:.1f}%")


    # Geographic Analysis Section
    st.markdown("---")
    st.markdown('<div class="section-header">Geographic Analysis</div>', unsafe_allow_html=True)
    
    # Top 10 States Performance
    if state_data and state_data.get("success"):
        state_perf = state_data["state_performance"]
        
        if state_perf.get("state_data"):
            # Prepare data for top 10 states table
            states_list = []
            for state, data in state_perf["state_data"].items():
                states_list.append({
                    "State": state,
                    "Quantity Sold": data["quantity"],
                    "Revenue": data["revenue"],
                    "Revenue %": data["revenue_percentage"],
                    "Orders": data["orders"]
                })
            
            # Sort by revenue and take top 10
            states_df = pd.DataFrame(states_list)
            states_df = states_df.sort_values("Revenue", ascending=False).head(10)
            states_df.index = range(1, len(states_df) + 1)
            
            # Format revenue column for display
            states_df_display = states_df.copy()
            states_df_display["Revenue"] = states_df_display["Revenue"].apply(format_indian_currency)
            states_df_display["Revenue %"] = states_df_display["Revenue %"].apply(lambda x: f"{x:.1f}%")
            
            st.markdown("### Top 10 Performing States (Tagged Orders)")
            st.dataframe(states_df_display, use_container_width=True)
            
            # India Map Visualization with Real Order Locations
            st.markdown("### Order Distribution Map")
            
            order_locations = state_perf.get("order_locations", [])
            
            if order_locations:
                # Create DataFrame for map plotting
                map_df = pd.DataFrame(order_locations)
                
                # Display the map with actual order locations
                st.map(map_df[["lat", "lon"]], zoom=5, use_container_width=True)
                
                # Map statistics
                col_map1, col_map2, col_map3 = st.columns(3)
                
                with col_map1:
                    unique_cities = len(set(loc["city"] for loc in order_locations))
                    st.info(f"🏙️ **{unique_cities} cities** with tagged orders")
                
                with col_map2:
                    total_orders_on_map = len(order_locations)
                    st.info(f"📍 **{total_orders_on_map} orders** plotted on map")
                
                with col_map3:
                    total_map_revenue = sum(loc["revenue"] for loc in order_locations)
                    st.info(f"💰 **{format_indian_currency(total_map_revenue)}** from mapped orders")               
                
                
            else:
                st.warning("🗺️ No order locations with coordinates found. This could mean:")
                st.info("""
                - Orders don't have latitude/longitude data in Shopify
                - Coordinates are outside India bounds (filtered out)
                - No tagged orders have shipping addresses with coordinates
                
                **Note:** The state analysis table above still works using state names from shipping addresses.
                """)

            
            # Summary stats
            total_states = len(state_perf["state_data"])
            top_state = states_df.iloc[0] if not states_df.empty else None
            
            col_geo1, col_geo2, col_geo3 = st.columns(3)
            
            with col_geo1:
                st.metric("Total States with Orders", total_states)
            
            with col_geo2:
                if top_state is not None:
                    st.metric("Top State", top_state["State"])
            
            with col_geo3:
                if top_state is not None:
                    st.metric("Top State Revenue %", f"{top_state['Revenue %']:.1f}%")
            
            # Simple bar chart for top 5 states
            if len(states_df) >= 5:
                top_5_states = states_df.head(5)
                chart_data = top_5_states.set_index("State")["Revenue"]
                
                st.markdown("#### Top 5 States by Revenue")
                st.bar_chart(chart_data, height=400)
        else:
            st.warning("No geographic data available yet.")
    else:
        st.warning("State performance data loading...")    

    # Timestamp
    st.markdown(
        f'<div class="last-updated">Last updated: {main_data["now_ist"].strftime("%I:%M:%S %p IST")}</div>',
        unsafe_allow_html=True
    )
    
    # Background refresh logic
    if auto_refresh:
        # Main data refresh (30 seconds)
        if should_refresh_main_data() and not st.session_state.main_loading:
            def update_main_data():
                st.session_state.main_loading = True
                try:
                    new_main_data = fetch_main_metrics()
                    st.session_state.main_data = new_main_data
                    st.session_state.last_main_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.main_loading = False
            update_main_data()
        
        # SKU data refresh (10 minutes)
        if should_refresh_sku_data() and not st.session_state.sku_loading:
            def update_sku_data():
                st.session_state.sku_loading = True
                try:
                    new_sku_data = fetch_sku_metrics()
                    st.session_state.sku_data = new_sku_data
                    st.session_state.last_sku_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.sku_loading = False
            update_sku_data()
        
        # Map data refresh (30 minutes)
        if should_refresh_map_data() and not st.session_state.map_loading:
            def update_map_data():
                st.session_state.map_loading = True
                try:
                    new_map_data = fetch_map_metrics()
                    st.session_state.map_data = new_map_data
                    st.session_state.last_map_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.map_loading = False
            update_map_data()
        
        # Customer data refresh (5 minutes)
        if should_refresh_customer_data() and not st.session_state.customer_loading:
            def update_customer_data():
                st.session_state.customer_loading = True
                try:
                    new_customer_data = fetch_customer_metrics()
                    st.session_state.customer_data = new_customer_data
                    st.session_state.last_customer_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.customer_loading = False
            update_customer_data()
        
        # State data refresh (10 minutes)
        if should_refresh_state_data() and not st.session_state.state_loading:
            def update_state_data():
                st.session_state.state_loading = True
                try:
                    new_state_data = fetch_state_metrics()
                    st.session_state.state_data = new_state_data
                    st.session_state.last_state_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.state_loading = False
            update_state_data()
        
        if should_refresh_category_data() and not st.session_state.category_loading:
            def update_category_data():
                st.session_state.category_loading = True
                try:
                    new_category_data = fetch_category_metrics()
                    st.session_state.category_data = new_category_data
                    st.session_state.last_category_update = datetime.datetime.now()
                except Exception:
                    pass
                finally:
                    st.session_state.category_loading = False
            update_category_data()
    
    # Gentle rerun for updates
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()