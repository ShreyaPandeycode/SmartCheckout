# 🛒 AI Smart Checkout System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Object%20Detection-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-yellow)

A fully automated, cashier-less retail checkout system powered by Computer Vision. This project uses **YOLOv8** for real-time object detection and **Streamlit** for the Point of Sale (POS) interface. It mimics systems like Amazon Go, allowing users to scan items via webcam, generate bills automatically, and manage inventory.

---

## 🌟 Key Features

This project implements **Several Advanced Features** to simulate a real-world retail environment:

1.  **✅ Multi-Object Tracking:** Uses ByteTrack to ensure items are counted only once, even if they stay in the frame.
2.  **🗣️ Voice Feedback:** Audio confirmation ("Maggi added - ₹14") using `pyttsx3`.
3.  **🧾 Auto-Invoice Generation:** Generates a professional PDF receipt instantly upon checkout.
4.  **💳 UPI QR Payment:** Dynamically generates a UPI QR code for contactless payment.
5.  **📊 Admin Dashboard:** A secured tab for store owners to view sales analytics and manage stock.
6.  **🎥 Multi-Angle Simulation:** Simulates a top-down camera view using image processing techniques.
7. **👤 User Profile & History:** Login system with persistent purchase history and wallet balance.

---

## 📂 Project Structure

```text
SmartCheckout/
│
├── database/
│   └── shop.db           # SQLite database (Users, Inventory, Sales)
├── raw_images/           # Source images for training
├── datasets/             # Processed YOLO format dataset
├── app.py                # Main Streamlit Application
├── train_yolo.py         # Script to train the model
├── data_parsing.py       # Script to convert CSV annotations to YOLO format
├── best.pt               # Trained YOLOv8 Model Weights
├── requirements.txt      # Python dependencies
├── data.yaml             # YOLO configuration file
└── README.md             # Project Documentation
```

---

## 📊 Model Performance

The YOLOv8 Nano model was trained on a custom dataset for **30 epochs**. Below are the key performance metrics:

| Metric    | Value | Description                               |
|------------|--------|-------------------------------------------|
| **mAP50**  | 0.89   | Mean Average Precision at 0.5 IoU        |
| **Precision** | 0.92 | Accuracy of positive predictions         |
| **Recall**    | 0.82 | Ability to find all positive samples     |

### Training Graphs

*Results* 

<img width="2400" height="1200" alt="results" src="https://github.com/user-attachments/assets/ff790723-2491-42f4-b81c-eb47ae74121a" />

--- 
*Confusion Matrix*

<img width="3000" height="2250" alt="confusion_matrix" src="https://github.com/user-attachments/assets/7a48e754-57f1-454c-a356-e2297aba45f2" />

---
*F1-Curve*

<img width="2250" height="1500" alt="BoxF1_curve" src="https://github.com/user-attachments/assets/fa8b30e1-9596-484d-a164-8eb19ab5590c" />

---

***

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash

git clone https://github.com/your-username/SmartCheckout.git

cd SmartCheckout

```

### 2. Create a Virtual Environment

```bash
# Windows

python -m venv venv

venv\Scripts\activate

# Mac/Linux

python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

***

## 🏃‍♂️ How to Run

### Option A: Run the App (Pre-trained)

If `best.pt` is already present in the folder:
```bash
streamlit run app.py
```

### Option B: Train from Scratch

1. **Prepare Data:**  
   Place images in `raw_images/` and the CSV file in the root directory.
   ```bash
   python data_parsing.py
   ```

2. **Train Model:**
   ```bash
   python train_yolo.py
   ```

3. **Run App:**
   ```bash
   streamlit run app.py
   ```

***

## 🛒 User Guide

### Login Credentials

| Role   | Username | Password |
|--------|-----------|-----------|
| User   | user      | 1234      |
| Admin  | admin     | admin     |

### Scanning
1. Navigate to **“🛒 Live Checkout”**.  
2. Toggle **“Start Scanning System”**.  
3. Show items (e.g., *Maggi, Jim Jam, etc.*) to the webcam.

### Checkout
1. Review the **Live Invoice** on the right panel.  
2. Click **✅ Finalize & Print**.  
3. Scan the QR code or download the **PDF receipt**.

***

## 🛠️ Technologies Used

| Technology | Purpose |
|-------------|----------|
| **Python 3.9** | Core programming language |
| **Ultralytics YOLOv8** | Object detection & tracking |
| **Streamlit** | Web interface |
| **OpenCV** | Image processing |
| **SQLite3** | Local database management |
| **ReportLab** | PDF generation |

***

## 🔮 Future Improvements

- Integration with **physical load cells (IoT)** for real weight verification.  
- Deployment on **NVIDIA Jetson Nano** for edge computing.  
- Integration with **Stripe/Razorpay API** for real payment processing.

***
