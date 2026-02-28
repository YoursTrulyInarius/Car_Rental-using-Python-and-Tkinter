from models import Session, Vehicle, Customer, Rental, User
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import sqlalchemy.orm as orm

def provide_session(func):
    """Decorator to provide a database session and handle transactions/errors."""
    def wrapper(self, *args, **kwargs):
        session = Session()
        try:
            result = func(self, session, *args, **kwargs)
            session.commit()
            return result
        except IntegrityError as e:
            session.rollback()
            print(f"Integrity Error: {e}")
            raise ValueError("This record violates constraints (e.g. duplicate registration).")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database Error: {e}")
            raise Exception("A database error occurred. Please try again.")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    return wrapper

class CarRentalService:
    def __init__(self):
        pass

    # --- Vehicle Management ---
    @provide_session
    def add_vehicle(self, session, make, model, year, registration, daily_rate):
        # Check for duplicate registration
        existing = session.query(Vehicle).filter_by(registration=registration).first()
        if existing:
            raise ValueError(f"A vehicle with registration '{registration}' already exists.")
        vehicle = Vehicle(make=make, model=model, year=year, registration=registration, daily_rate=daily_rate)
        session.add(vehicle)
        return vehicle

    @provide_session
    def add_vehicle_batch(self, session, make, model, year, base_registration, daily_rate, quantity):
        created_vehicles = []
        for i in range(1, quantity + 1):
            # Auto-generate unique registration if batch > 1
            reg = f"{base_registration}-{i}" if quantity > 1 else base_registration

            # Check for duplicate registration before adding
            existing = session.query(Vehicle).filter_by(registration=reg).first()
            if existing:
                raise ValueError(f"A vehicle with registration '{reg}' already exists. Please use a different plate number prefix.")

            vehicle = Vehicle(make=make, model=model, year=year, registration=reg, daily_rate=daily_rate)
            session.add(vehicle)
            created_vehicles.append(vehicle)
        return created_vehicles

    @provide_session
    def get_all_vehicles(self, session):
        return session.query(Vehicle).all()

    @provide_session
    def get_vehicle(self, session, vehicle_id):
        return session.get(Vehicle, vehicle_id)

    @provide_session
    def get_available_vehicles(self, session):
        return session.query(Vehicle).filter_by(status='Available').all()

    @provide_session
    def get_vehicle_count_by_model(self, session, make, model, year):
        return session.query(Vehicle).filter_by(make=make, model=model, year=year).count()

    @provide_session
    def update_vehicle_batch(self, session, old_make, old_model, old_year, new_make, new_model, new_year, new_rate):
        """Update all vehicles in the same group (same make/model/year) to new values."""
        vehicles = session.query(Vehicle).filter_by(make=old_make, model=old_model, year=old_year).all()
        if not vehicles:
            raise ValueError("No vehicles found for that group.")
        for v in vehicles:
            v.make = new_make
            v.model = new_model
            v.year = new_year
            v.daily_rate = new_rate
        return len(vehicles)

    @provide_session
    def adjust_vehicle_stock(self, session, make, model, year, current_reg, daily_rate, target_qty):
        # 1. Get current vehicles of this type
        existing_vehicles = session.query(Vehicle).filter_by(make=make, model=model, year=year).all()
        current_qty = len(existing_vehicles)

        if target_qty == current_qty:
            return True, "No change in stock."

        if target_qty > current_qty:
            # ADD STOCK
            needed = target_qty - current_qty

            # Determine base registration prefix:
            # Strip any trailing numeric suffix first to get a clean base
            parts = current_reg.split('-')
            if len(parts) > 1 and parts[-1].isdigit():
                base_reg = '-'.join(parts[:-1])
            else:
                base_reg = current_reg

            # Find highest existing suffix across all vehicles in this group
            max_suffix = 0
            for v in existing_vehicles:
                v_parts = v.registration.split('-')
                if len(v_parts) > 1 and v_parts[-1].isdigit():
                    s = int(v_parts[-1])
                    if s > max_suffix:
                        max_suffix = s

            # Also check globally all registrations that start with base_reg
            all_regs = session.query(Vehicle.registration).filter(
                Vehicle.registration.like(f"{base_reg}-%")
            ).all()
            for (reg,) in all_regs:
                reg_parts = reg.split('-')
                if reg_parts[-1].isdigit():
                    s = int(reg_parts[-1])
                    if s > max_suffix:
                        max_suffix = s

            created_count = 0
            for i in range(needed):
                new_suffix = max_suffix + 1 + i
                new_reg = f"{base_reg}-{new_suffix}"

                # Double check it doesn't exist
                attempt = 0
                while session.query(Vehicle).filter_by(registration=new_reg).first():
                    attempt += 1
                    new_reg = f"{base_reg}-{new_suffix}-{attempt}"

                vehicle = Vehicle(make=make, model=model, year=year, registration=new_reg, daily_rate=daily_rate)
                session.add(vehicle)
                created_count += 1

            return True, f"Added {created_count} new vehicles to fleet."

        else:
            # REMOVE STOCK
            to_remove = current_qty - target_qty
            # Find available vehicles
            available = [v for v in existing_vehicles if v.status == 'Available']

            if len(available) < to_remove:
                return False, f"Cannot reduce stock to {target_qty}. Only {len(available)} available for removal (others are Rented/Maintenance)."

            # Remove the last added ones first (highest ID)
            available.sort(key=lambda x: x.id, reverse=True)
            for i in range(to_remove):
                session.delete(available[i])

            return True, f"Removed {to_remove} vehicles from fleet."

    @provide_session
    def update_vehicle(self, session, vehicle_id, **kwargs):
        vehicle = session.get(Vehicle, vehicle_id)
        if vehicle:
            # Check for duplicate registration if registration is being changed
            if 'registration' in kwargs and kwargs['registration'] != vehicle.registration:
                existing = session.query(Vehicle).filter_by(registration=kwargs['registration']).first()
                if existing:
                    raise ValueError(f"Registration '{kwargs['registration']}' is already used by another vehicle.")
            for key, value in kwargs.items():
                setattr(vehicle, key, value)
        return vehicle

    @provide_session
    def delete_vehicle(self, session, vehicle_id):
        # Check if vehicle has active rentals
        active_rental = session.query(Rental).filter_by(vehicle_id=vehicle_id, status='Active').first()
        if active_rental:
            raise ValueError("Cannot delete vehicle with an active rental.")

        vehicle = session.get(Vehicle, vehicle_id)
        if vehicle:
            session.delete(vehicle)
            return True
        return False

    @provide_session
    def delete_vehicle_group(self, session, make, model, year):
        """Delete all Available vehicles in a group. Raises if any are Rented/Maintenance."""
        vehicles = session.query(Vehicle).filter_by(make=make, model=model, year=year).all()
        rented = [v for v in vehicles if v.status != 'Available']
        if rented:
            raise ValueError(f"Cannot delete group: {len(rented)} vehicle(s) are currently Rented or in Maintenance.")
        for v in vehicles:
            active_rental = session.query(Rental).filter_by(vehicle_id=v.id, status='Active').first()
            if active_rental:
                raise ValueError(f"Cannot delete vehicle ID {v.id}: it has an active rental.")
            session.delete(v)
        return len(vehicles)

    # --- Customer Management ---
    @provide_session
    def add_customer(self, session, name, contact, license_details):
        if not name or not contact:
            raise ValueError("Name and Contact are required.")
        # Check for duplicate customer (same name AND contact)
        existing = session.query(Customer).filter_by(name=name, contact=contact).first()
        if existing:
            raise ValueError(f"A customer named '{name}' with that contact number already exists.")
        customer = Customer(name=name, contact=contact, license_details=license_details)
        session.add(customer)
        return customer

    @provide_session
    def get_all_customers(self, session):
        return session.query(Customer).all()

    @provide_session
    def delete_customer(self, session, customer_id):
        # Check if customer has active rentals
        active_rental = session.query(Rental).filter_by(customer_id=customer_id, status='Active').first()
        if active_rental:
            raise ValueError("Cannot delete customer with an active rental.")

        customer = session.get(Customer, customer_id)
        if customer:
            session.delete(customer)
            return True
        return False

    # --- Rental Processing ---
    @provide_session
    def create_rental(self, session, customer_id, vehicle_id, return_date_str, rental_date_str=None):
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            return None, "Vehicle not found."
        if vehicle.status != 'Available':
            return None, f"Vehicle is currently {vehicle.status}."

        try:
            if rental_date_str:
                rental_date = datetime.datetime.strptime(rental_date_str, "%Y-%m-%d").date()
            else:
                rental_date = datetime.date.today()

            return_date = datetime.datetime.strptime(return_date_str, "%Y-%m-%d").date()
        except ValueError:
            return None, "Invalid date format. Use YYYY-MM-DD."

        duration = (return_date - rental_date).days
        if duration <= 0:
            return None, "Return date must be after the start date."

        total_cost = duration * vehicle.daily_rate

        rental = Rental(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            rental_date=rental_date,
            return_date=return_date,
            total_cost=total_cost,
            status='Active'
        )
        vehicle.status = 'Rented'
        session.add(rental)
        return rental, "Success"

    @provide_session
    def complete_rental(self, session, rental_id):
        rental = session.get(Rental, rental_id)
        if rental and rental.status == 'Active':
            rental.status = 'Completed'
            rental.vehicle.status = 'Available'
            return True
        return False

    @provide_session
    def get_all_rentals(self, session):
        return session.query(Rental).options(orm.joinedload(Rental.customer), orm.joinedload(Rental.vehicle)).all()

    @provide_session
    def authenticate(self, session, username, password):
        user = session.query(User).filter_by(username=username, password=password).first()
        return user is not None
