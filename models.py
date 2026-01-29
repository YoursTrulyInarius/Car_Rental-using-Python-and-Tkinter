from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default='admin')

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    license_details = Column(String, nullable=False)
    rentals = relationship("Rental", back_populates="customer")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    registration = Column(String, unique=True, nullable=False)
    status = Column(String, default='Available') # Available, Rented, Maintenance
    daily_rate = Column(Float, nullable=False)
    rentals = relationship("Rental", back_populates="vehicle")

class Rental(Base):
    __tablename__ = 'rentals'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    rental_date = Column(Date, default=datetime.date.today)
    return_date = Column(Date, nullable=True)
    total_cost = Column(Float, nullable=False)
    status = Column(String, default='Active') # Active, Completed, Cancelled

    customer = relationship("Customer", back_populates="rentals")
    vehicle = relationship("Vehicle", back_populates="rentals")

# Database Setup
engine = create_engine('sqlite:///car_rental.db')
Session = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
    
    # Add a default admin user if not exists
    session = Session()
    if not session.query(User).filter_by(username='admin').first():
        admin = User(username='admin', password='password', role='admin')
        session.add(admin)
        session.commit()
    session.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
