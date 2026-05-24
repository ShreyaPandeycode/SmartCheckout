import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import sqlite3
import pandas as pd
from datetime import datetime
import pyttsx3
import threading
import queue
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image
import os
import time
import razorpay

# --- RAZORPAY INITIALIZATION ---
# Replace these with your actual test keys from the Razorpay Dashboard
RAZORPAY_KEY_ID = "rzp_test_StGnQlytLdXBrF" 
RAZORPAY_KEY_SECRET = "xlyOTx7VsaD5Xi8tVwXs7DRc"

try:
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    rzp_client = None
    print("Razorpay initialization failed:", e)
# -------------------------------

# config
st.set_page_config(page_title="Smart Retail System", layout="wide", page_icon="🛒")
MODEL_PATH = 'best.pt'
DB_PATH = 'database/shop.db'

# css
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .invoice-box {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #41444C;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    table { width: 100%; border-collapse: collapse; color: white; }
    th { text-align: left; border-bottom: 2px solid #FF4B4B; padding: 10px; }
    td { border-bottom: 1px solid #41444C; padding: 10px; }
    .total-row { font-size: 1.5em; font-weight: bold; color: #00FF00; text-align: right; padding-top: 20px; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# db and init
def init_db():
    if not os.path.exists('database'): os.makedirs('database')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (name TEXT PRIMARY KEY, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, wallet REAL, points INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, items TEXT, total REAL, date TEXT, user TEXT)''')
    
    c.execute("SELECT count(*) FROM inventory")
    if c.fetchone()[0] == 0:
        items = [('maggi', 14.0, 50), ('Jim_jam', 35.0, 50), ('dairy_milk', 20.0, 100), ('pears_soap', 48.0, 40), ('plain_bhujia', 10.0, 60)]
        c.executemany("INSERT OR IGNORE INTO inventory VALUES (?,?,?)", items)
        c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin', 0, 0)")
        c.execute("INSERT OR IGNORE INTO users VALUES ('user', '1234', 1000, 50)")
        conn.commit()
    conn.close()

init_db()

# voice thread
voice_q = queue.Queue()
def voice_worker():
    engine = pyttsx3.init()
    while True:
        text = voice_q.get()
        if text is None: break
        try: engine.say(text); engine.runAndWait()
        except: pass
        voice_q.task_done()
threading.Thread(target=voice_worker, daemon=True).start()
def speak(text): voice_q.put(text)

# pdf generator
def generate_pdf(cart, total, user):
    filename = f"invoice_{int(time.time())}.pdf"
    c = canvas.Canvas(filename)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, 800, "SMART RETAIL INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 750, f"Customer ID: {user}")
    c.line(50, 740, 550, 740)
    y = 720
    c.drawString(50, y, "Item")
    c.drawString(300, y, "Qty")
    c.drawString(400, y, "Price")
    c.drawString(500, y, "Total")
    y -= 20
    c.line(50, y+15, 550, y+15)
    for name, info in cart.items():
        c.drawString(50, y, name.capitalize())
        c.drawString(300, y, str(info['qty']))
        c.drawString(400, y, f"{info['price']}")
        c.drawString(500, y, f"{info['price'] * info['qty']}")
        y -= 20
    c.line(50, y+10, 550, y+10)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(350, y-20, f"GRAND TOTAL: Rs. {total}")
    c.save()
    return filename

# session state
if 'cart' not in st.session_state: st.session_state['cart'] = {}
if 'tracked_ids' not in st.session_state: st.session_state['tracked_ids'] = set()
if 'user' not in st.session_state: st.session_state['user'] = None

# login logic
if not st.session_state['user']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 POS System Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            sub = st.form_submit_button("Login")
            if sub:
                conn = sqlite3.connect(DB_PATH)
                res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                conn.close()
                if res: st.session_state['user'] = u; st.rerun()
                else: st.error("Invalid Credentials")
    st.stop()

# app layout
with st.sidebar:
    st.title(f"👨🏼‍💻 {st.session_state['user']}")
    menu = st.radio("Navigation", ["🛒 Live Checkout", "📊 Store Manager", "📜 History"])
    st.divider()
    if st.button("Logout", type="primary"):
        st.session_state['user'] = None
        st.session_state['cart'] = {}
        st.rerun()

# checkout page 1.
if menu == "🛒 Live Checkout":
    st.title("🛒 Smart Checkout Terminal")
    
    # Load Model & Prices
    try:
        model = YOLO(MODEL_PATH)
    except:
        st.error("Model not found. Please run training first.")
        st.stop()
        
    conn = sqlite3.connect(DB_PATH)
    prices = pd.read_sql("SELECT name, price FROM inventory", conn).set_index('name')['price'].to_dict()
    conn.close()

    col_input, col_inv = st.columns([1.5, 1])

    # input: upload n camera
    with col_input:
        # TABS for switching modes
        tab_cam, tab_upload = st.tabs(["📷 Live Camera", "📤 Upload Image"])
        
        # tab 1: webcam
        with tab_cam:
            st.subheader("Live Feed")
            
            # CONFIDENCE SLIDER (Fixes the Cup/JimJam issue)
            conf_threshold = st.slider("Detection Confidence", 0.0, 1.0, 0.65, help="Increase this if the model detects wrong items (like cups).")
            
            run_camera = st.toggle("Start Camera", value=False)
            cam_placeholder = st.empty()
            
            if run_camera:
                cap = cv2.VideoCapture(0)
                while run_camera:
                    ret, frame = cap.read()
                    if not ret: 
                        st.error("Camera not detected")
                        break
                    
                    # Tracking
                    results = model.track(frame, persist=True, verbose=False, conf=conf_threshold)
                    res = results[0]
                    frame_viz = res.plot()
                    
                    if res.boxes.id is not None:
                        ids = res.boxes.id.cpu().numpy().astype(int)
                        clss = res.boxes.cls.cpu().numpy().astype(int)
                        
                        for tid, cls in zip(ids, clss):
                            name = model.names[cls]
                            if name in prices:
                                if tid not in st.session_state['tracked_ids']:
                                    st.session_state['tracked_ids'].add(tid)
                                    if name in st.session_state['cart']:
                                        st.session_state['cart'][name]['qty'] += 1
                                    else:
                                        st.session_state['cart'][name] = {'qty': 1, 'price': prices[name]}
                                    speak(f"{name} added")

                    cam_placeholder.image(cv2.cvtColor(frame_viz, cv2.COLOR_BGR2RGB), use_container_width=True)
                cap.release() # Ensure camera turns off
        
        # tab2: upload
        with tab_upload:
            st.subheader("Static Image Analysis")
            uploaded_file = st.file_uploader("Upload an image to scan", type=['jpg', 'png', 'jpeg'])
            
            if uploaded_file:
                # Save temp
                with open("temp_upload.jpg", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Predict
                img = cv2.imread("temp_upload.jpg")
                results = model.predict(img, conf=0.5) # Standard confidence for upload
                res_plotted = results[0].plot()
                st.image(cv2.cvtColor(res_plotted, cv2.COLOR_BGR2RGB), caption="Detected Items", use_container_width=True)
                
                # Add to Cart Button
                if st.button("Add Detected Items to Cart"):
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0])
                        name = model.names[cls_id]
                        if name in prices:
                            if name in st.session_state['cart']:
                                st.session_state['cart'][name]['qty'] += 1
                            else:
                                st.session_state['cart'][name] = {'qty': 1, 'price': prices[name]}
                    st.success("Items added to invoice!")
                    time.sleep(1)
                    st.rerun()

    # invoice 
    with col_inv:
        st.subheader("🧾 Live Invoice")
        total_amount = 0
        cart_items = []
        
        if st.session_state['cart']:
            for item, details in st.session_state['cart'].items():
                line_total = details['qty'] * details['price']
                total_amount += line_total
                cart_items.append({
                    "Item": item.capitalize(),
                    "Qty": details['qty'],
                    "Price": f"₹{details['price']}",
                    "Total": f"₹{line_total}"
                })
            
            df = pd.DataFrame(cart_items)
            html_table = f"""
            <div class="invoice-box">
                <table>
                    <tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
            """
            for _, row in df.iterrows():
                html_table += f"<tr><td>{row['Item']}</td><td>{row['Qty']}</td><td>{row['Price']}</td><td>{row['Total']}</td></tr>"
            html_table += f"</table><div class='total-row'>GRAND TOTAL: ₹{total_amount}</div></div>"
            st.markdown(html_table, unsafe_allow_html=True)
            
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Clear"):
                    st.session_state['cart'] = {}
                    st.session_state['tracked_ids'] = set()
                    st.rerun()
            with c2:
                if st.button("✅ Pay & Print", type="primary"):
                    pdf_file = generate_pdf(st.session_state['cart'], total_amount, st.session_state['user'])
                    
                    # --- RAZORPAY INTEGRATION ---
                    if rzp_client:
                        try:
                            # Create Razorpay Payment Link (Amount must be in paise, so multiply by 100)
                            payment_data = {
                                "amount": int(total_amount * 100), 
                                "currency": "INR",
                                "description": f"Smart Retail Checkout - {st.session_state['user']}",
                                "customer": {
                                    "name": st.session_state['user'],
                                    "contact": "9876543210" # Realistic dummy number
                                },
                                "notify": {"sms": False, "email": False},
                                "reminder_enable": False
                            }
                            payment_link = rzp_client.payment_link.create(payment_data)
                            payment_url = payment_link['short_url']
                            
                            st.success("Invoice Generated! Scan QR to Pay.")
                            
                            # Generate QR Code for the Razorpay Link
                            qr_img = qrcode.make(payment_url).get_image()
                            st.image(qr_img, width=200, caption="Scan to Pay via Razorpay")
                            st.markdown(f"[Click here to pay manually if QR fails]({payment_url})")
                            
                        except Exception as e:
                            st.error(f"Razorpay Error: {e}")
                            # Fallback to standard UPI if API fails
                            upi_url = f"upi://pay?pa=shop@upi&pn=SmartShop&am={total_amount}"
                            st.image(qrcode.make(upi_url).get_image(), width=150, caption="Fallback UPI QR")
                    else:
                        # Fallback to standard UPI if Razorpay isn't configured
                        upi_url = f"upi://pay?pa=shop@upi&pn=SmartShop&am={total_amount}"
                        st.image(qrcode.make(upi_url).get_image(), width=150, caption="Standard UPI QR")
                    # ----------------------------

                    # Update Database
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    for item, info in st.session_state['cart'].items():
                        c.execute("UPDATE inventory SET stock = stock - ? WHERE name=?", (info['qty'], item))
                    c.execute("INSERT INTO sales (items, total, date, user) VALUES (?,?,?,?)", 
                              (str(st.session_state['cart']), total_amount, str(datetime.now()), st.session_state['user']))
                    conn.commit()
                    conn.close()
                    
                    with open(pdf_file, "rb") as f:
                        st.download_button("Download PDF", f, file_name="Invoice.pdf")
        else:
            st.info("Cart is empty.")

# Admin dashboard 2.
elif menu == "📊 Store Manager":
    if st.session_state['user'] != 'admin':
        st.error("Access Denied")
    else:
        st.title("Store Manager")
        conn = sqlite3.connect(DB_PATH)
        t1, t2 = st.tabs(["Inventory", "Sales"])
        with t1:
            df = pd.read_sql("SELECT * FROM inventory", conn)
            st.dataframe(df, use_container_width=True)
            with st.form("stock"):
                name = st.selectbox("Item", df['name'].tolist())
                qty = st.number_input("Add Stock", 1)
                if st.form_submit_button("Update"):
                    conn.execute("UPDATE inventory SET stock = stock + ? WHERE name=?", (qty, name))
                    conn.commit()
                    st.rerun()
        with t2:
            st.dataframe(pd.read_sql("SELECT * FROM sales ORDER BY id DESC", conn), use_container_width=True)
        conn.close()

# History 3.
elif menu == "📜 History":
    st.title("Transaction History")
    conn = sqlite3.connect(DB_PATH)
    st.dataframe(pd.read_sql(f"SELECT * FROM sales WHERE user='{st.session_state['user']}' ORDER BY id DESC", conn), use_container_width=True)
    conn.close()