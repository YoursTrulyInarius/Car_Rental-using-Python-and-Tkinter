# Car Rental Management System

A comprehensive desktop application designed to streamline car rental operations, managing vehicle fleets, customer records, and rental transactions with ease.

## 🚀 Features

### 🚗 Vehicle Fleet Management
- **Smart Inventory**: View vehicles by model groups ("Fleet Summary") or individual units.
- **Batch Creation**: Add multiple identical vehicles at once with auto-generated license plates (e.g., `ABC-123-1`, `ABC-123-2`).
- **Stock Management**: Easily adjust the total stock count for any model directly from the edit screen.
- **Status Tracking**: value-added visualization of Available vs. Rented units.

### 👤 Customer Management
- Maintain a database of customers with contact and license details.
- Prevent deletion of customers with active rentals for data integrity.

### 📅 Rental Processing
- **Responsive Booking Dialog**: Wide, user-friendly form with visual calendar pickers.
- **Flexible Dates**: Set custom Start and Return dates.
- **Live Cost Estimator**: Automatically calculates the Total Rental Fee based on the selected dates and vehicle rate.
- **Validation**: Prevents double-booking and ensures valid rental periods.

### 📊 Dashboard & Reporting
- **Quick Actions**: One-click access to common tasks.
- **Real-time Stock Levels**: Immediate view of available vs. total stock per model.
- **Recent Transactions**: History of the latest rentals.
- **CSV Export**: Export data for external analysis.

## 🛠️ Technology Stack
- **Language**: Python 3.12+
- **GUI Framework**: Tkinter with `ttkbootstrap` (Modern Flat UI)
- **Database**: SQLite
- **ORM**: SQLAlchemy

## 📦 Installation & Usage

1.  **Install Dependencies**:
    ```bash
    pip install ttkbootstrap sqlalchemy pandas
    ```

2.  **Run the Application**:
    ```bash
    python main.py
    ```

3.  **Default Admin**:
    - The system auto-initializes. No login setup required for the local version.

---

### 👨‍💻 Developed by
**Cabardo, Sonjeev C.**
BSIT 2 C
