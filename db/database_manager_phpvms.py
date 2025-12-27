import mysql.connector
from mysql.connector import Error
import requests
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASS")
# -----------------------------
# MySQL Configuration
# -----------------------------
DB_CONFIG = {
    'host': DB_HOST,
    'database': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,    
    'port': 3306
}
# -----------------------------
# Database connection
# -----------------------------
def connect_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print(f"✅ Conectado a MySQL: {DB_CONFIG['database']}")
            return conn
    except Error as e:
        print(f"❌ Error MySQL: {e}")
        return None
connect_database()
# -----------------------------
# LOGIN phpVMS (web scraping)
# -----------------------------
def login_phpvms(email, password):
    try:
        session = requests.Session()

        # Obtener CSRF
        r = session.get('http://127.0.0.1:8000/login')
        csrf = re.search(r'_token" value="([^"]+)"', r.text)
        if not csrf:
            return None

        # Login
        r = session.post(
            'http://127.0.0.1:8000/login',
            data={
                '_token': csrf.group(1),
                'email': email,
                'password': password
            },
            allow_redirects=False
        )

        if r.status_code != 302:
            return None

        # Obtener perfil
        r = session.get('http://127.0.0.1:8000/profile')

        uid_match = re.search(r'profile/(\d+)/edit', r.text)
        if not uid_match:
            return None

        return  int(uid_match.group(1))

    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


# -----------------------------
# OBTENER RESERVA (BID)
# -----------------------------
def get_reservation(user_id):
    conn = connect_database()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                b.flight_id,
                b.aircraft_id,
                f.flight_number,
                f.flight_type,
                f.dpt_airport_id,
                f.arr_airport_id,
                dpt.name AS dpt_name,
                arr.name AS arr_name,
                a.name AS aircraft_name,
                a.registration
            FROM bids b
            JOIN flights f ON b.flight_id = f.id
            JOIN airports dpt ON f.dpt_airport_id = dpt.id
            JOIN airports arr ON f.arr_airport_id = arr.id
            LEFT JOIN aircraft a ON b.aircraft_id = a.id
            WHERE b.user_id = %s
            LIMIT 1
        """

        cursor.execute(query, (user_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            'flight_id': row['flight_id'],
            'flight_number': row['flight_number'],
            'aircraft_id': row['aircraft_id'],
            "transport_type" : row["flight_type"],
            'departure': {
                'id': row['dpt_airport_id'],
                'name': row['dpt_name']
            },
            'arrival': {
                'id': row['arr_airport_id'],
                'name': row['arr_name']
            },
            'aircraft': {
                'id': row['aircraft_id'],
                'name': row['aircraft_name'],
                'registration': row['registration']
            } if row['aircraft_name'] else None
        }

    except Exception as e:
        print(f"❌ Error DB: {e}")
        return None

    finally:
        conn.close()


def initialize_pirep(user_id, airline_id, aircraft_id, flight_id, flight_number, flight_type, departure, arrival, zfw, block_fuel, route):
    """
    Inserta un nuevo PIREP en la tabla 'pireps'.
    """
    try:
        conn = connect_database()

        cursor = conn.cursor()

        # Genera un UUID para el PIREP
        pirep_id = str(uuid.uuid4())

        # Tiempos iniciales
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert SQL
        sql = """
        INSERT INTO pireps (
            id, user_id, airline_id, aircraft_id, flight_id, flight_number,
            flight_type, dpt_airport_id, arr_airport_id, zfw, block_fuel,
            route, state, status, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            pirep_id,
            user_id,
            airline_id,
            aircraft_id,
            flight_id,
            flight_number,
            flight_type,
            departure,
            arrival,
            zfw,
            block_fuel,
            route,
            1,      # state inicial
            'SCH',  # status inicial (Scheduled)
            now,    # created_at
            now     # updated_at
        )

        cursor.execute(sql, values)
        conn.commit()

        print(f"✅ PIREP inicializado con ID: {pirep_id}")
        return pirep_id

    except Error as e:
        print(f"❌ Error al insertar PIREP: {e}")
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def initialize_acars(pirep_id, init_lat, init_lon, block_fuel):
    try:
        conn = connect_database()
        cursor = conn.cursor()

        acars_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sql = """
        INSERT INTO acars (
            id, pirep_id, type, nav_type, `order`, name, status, log,
            lat, lon, distance, heading, altitude_agl, altitude_msl,
            vs, gs, ias, transponder, autopilot, fuel, fuel_flow, sim_time,
            created_at, updated_at, source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            acars_id,
            pirep_id,
            0,          # type normal
            0,          # nav_type DCT
            0,          # order
            '',         # name inicial
            'SCH',      # status
            '',         # log
            init_lat,
            init_lon,
            0,          # distance
            0,          # heading
            0.0,        # altitude_agl
            0.0,        # altitude_msl
            0.0,        # vs
            0,          # gs
            0,          # ias
            0,          # transponder
            '',         # autopilot
            block_fuel, # fuel inicial
            0.0,        # fuel_flow
            '0:00',     # sim_time
            now,
            now,
            'ACARS'
        )

        cursor.execute(sql, values)
        conn.commit()
        print(f"✅ ACARS inicializado con ID: {acars_id}")
        return acars_id

    except Error as e:
        print(f"❌ Error al inicializar ACARS: {e}")
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
