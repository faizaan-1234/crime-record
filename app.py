# app.py
import os
import mysql.connector
import datetime # Needed for date/time formatting
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Load Secret Key - **IMPORTANT: Replace placeholder in .env file**
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_very_insecure_default_key_change_me')

# --- Database Configuration ---
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'CrimeRecords')
}

# --- Database Helper Functions ---
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        flash(f"Database Connection Error: {err}", "danger")
        print(f"Database Connection Error: {err}")
        return None

def fetch_all(query, params=None):
    """Fetches all results from the database as dictionaries."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    results = []
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Database Query Error: {err}", "danger")
        print(f"Database Query Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return results

def fetch_one(query, params=None):
    """Fetches a single result from the database as a dictionary."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
    except mysql.connector.Error as err:
        flash(f"Database Query Error: {err}", "danger")
        print(f"Database Query Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return result

def execute_query(query, params=None):
    """Executes an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    if not conn: return False, None
    cursor = conn.cursor()
    last_row_id = None
    success = False
    try:
        cursor.execute(query, params)
        conn.commit() # Commit the transaction
        last_row_id = cursor.lastrowid # Get ID for INSERT queries
        success = True
        # Note: Generic success flash message removed, handled in routes now
    except mysql.connector.Error as err:
        conn.rollback() # Rollback on error
        flash(f"Database Execution Error: {err}", "danger")
        print(f"Database Execution Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return success, last_row_id

# --- Helper to get dropdown data ---
def get_dropdown_data():
    """Fetches data needed for dropdowns in forms."""
    data = {
        'victims': fetch_all("SELECT VictimID, CONCAT(FirstName, ' ', LastName) as Name FROM Victims ORDER BY FirstName, LastName"),
        'suspects': fetch_all("SELECT SuspectID, CONCAT(FirstName, ' ', LastName) as Name FROM Suspects ORDER BY FirstName, LastName"),
        'officers': fetch_all("SELECT OfficerID, CONCAT(FirstName, ' ', LastName, ' (', BadgeNumber, ')') as Name FROM Officers ORDER BY FirstName, LastName"),
        'reported_by': fetch_all("SELECT ReportedByID, CONCAT(FirstName, ' ', LastName) as Name FROM ReportedBy ORDER BY FirstName, LastName"),
        'evidence': fetch_all("SELECT EvidenceID, CONCAT('ID: ', EvidenceID, ' - ', IFNULL(EvidenceType,'Unknown Type')) as Name FROM Evidence ORDER BY EvidenceID"),
        'crimes': fetch_all("SELECT CrimeID, CONCAT(CrimeType, ' (', DATE_FORMAT(DateOfCrime, '%Y-%m-%d'), ')') as Name FROM Crimes ORDER BY DateOfCrime DESC, CrimeID DESC")
    }
    for key in ['victims', 'suspects', 'officers', 'reported_by', 'evidence', 'crimes']:
        if key in data:
            id_key_name = key[:-1].capitalize() + 'ID'
            if key == 'reported_by': id_key_name = 'ReportedByID'
            if key == 'evidence': id_key_name = 'EvidenceID'
            if key == 'crimes': id_key_name = 'CrimeID'

            none_option = {id_key_name: None, 'Name': '--- Select ---'}
            if not data[key]:
                 none_option['Name'] = '--- No Records Found ---'
                 data[key] = [none_option]
            else:
                data[key].insert(0, none_option)
    return data

# --- Utility for date/time formatting for HTML input fields ---
def format_date_for_input(date_obj):
    """Formats date obj/None to YYYY-MM-DD string or empty string."""
    if isinstance(date_obj, datetime.date):
        return date_obj.strftime('%Y-%m-%d')
    return ''

def format_time_for_input(time_obj):
    """Formats time obj/timedelta/None to HH:MM string or empty string."""
    if isinstance(time_obj, datetime.timedelta):
         total_seconds = int(time_obj.total_seconds())
         hours = (total_seconds // 3600) % 24
         minutes = (total_seconds % 3600) // 60
         return f"{hours:02}:{minutes:02}"
    elif isinstance(time_obj, datetime.time):
         return time_obj.strftime('%H:%M')
    return ''

# --- Routes ---
@app.route('/')
def index():
    """Homepage."""
    current_year = datetime.datetime.now().year
    return render_template('index.html', current_year=current_year)

# --- Crimes ---
@app.route('/crimes')
def list_crimes(): # READ (List)
    query = """
        SELECT c.*,
               CONCAT(v.FirstName, ' ', v.LastName) as VictimName,
               CONCAT(s.FirstName, ' ', s.LastName) as SuspectName,
               CONCAT(o.FirstName, ' ', o.LastName) as OfficerName,
               CONCAT(rb.FirstName, ' ', rb.LastName) as ReportedByName,
               e.EvidenceType as EvidenceLinkedType
        FROM Crimes c
        LEFT JOIN Victims v ON c.VictimID = v.VictimID
        LEFT JOIN Suspects s ON c.SuspectID = s.SuspectID
        LEFT JOIN Officers o ON c.OfficerID = o.OfficerID
        LEFT JOIN ReportedBy rb ON c.ReportedByID = rb.ReportedByID
        LEFT JOIN Evidence e ON c.EvidenceID = e.EvidenceID
        ORDER BY c.DateOfCrime DESC, c.TimeOfCrime DESC, c.CrimeID DESC
    """
    crimes = fetch_all(query)

    # Format date/time for display before sending to template
    for crime in crimes:
        crime['DisplayTime'] = format_time_for_input(crime.get('TimeOfCrime'))
        # Optional date formatting if needed
        # crime['DisplayDate'] = format_date_for_input(crime.get('DateOfCrime'))

    return render_template('crimes.html', crimes=crimes)

@app.route('/crimes/add', methods=['GET', 'POST'])
def add_crime(): # CREATE
    dropdown_data = get_dropdown_data()
    if request.method == 'POST':
        crime_type = request.form.get('crime_type')
        description = request.form.get('description')
        date_of_crime = request.form.get('date_of_crime')
        time_of_crime = request.form.get('time_of_crime') or None
        location = request.form.get('location')
        status = request.form.get('status')
        victim_id = request.form.get('victim_id')
        suspect_id = request.form.get('suspect_id')
        officer_id = request.form.get('officer_id')
        reported_by_id = request.form.get('reported_by_id')
        evidence_id = request.form.get('evidence_id')

        if not all([crime_type, date_of_crime]):
             flash("Crime Type and Date are required.", "warning")
             return render_template('add_crime.html', **dropdown_data, form_data=request.form)

        query = """
            INSERT INTO Crimes (CrimeType, Description, DateOfCrime, TimeOfCrime, Location, Status, VictimID, SuspectID, OfficerID, ReportedByID, EvidenceID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (crime_type, description, date_of_crime, time_of_crime, location, status,
                  None if victim_id == 'None' else victim_id,
                  None if suspect_id == 'None' else suspect_id,
                  None if officer_id == 'None' else officer_id,
                  None if reported_by_id == 'None' else reported_by_id,
                  None if evidence_id == 'None' else evidence_id)

        success, new_id = execute_query(query, params)
        if success:
            flash(f"Crime (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_crimes'))
        else:
             # Error already flashed by execute_query
             return render_template('add_crime.html', **dropdown_data, form_data=request.form)
    # GET request
    return render_template('add_crime.html', **dropdown_data)

@app.route('/crimes/edit/<int:crime_id>', methods=['GET', 'POST'])
def edit_crime(crime_id): # UPDATE
    dropdown_data = get_dropdown_data()
    crime = fetch_one("SELECT * FROM Crimes WHERE CrimeID = %s", (crime_id,))
    if not crime:
        flash(f"Crime with ID {crime_id} not found.", "warning")
        return redirect(url_for('list_crimes'))

    if request.method == 'POST':
        crime_type = request.form.get('crime_type')
        description = request.form.get('description')
        date_of_crime = request.form.get('date_of_crime')
        time_of_crime = request.form.get('time_of_crime') or None
        location = request.form.get('location')
        status = request.form.get('status')
        victim_id = request.form.get('victim_id')
        suspect_id = request.form.get('suspect_id')
        officer_id = request.form.get('officer_id')
        reported_by_id = request.form.get('reported_by_id')
        evidence_id = request.form.get('evidence_id')

        if not all([crime_type, date_of_crime]):
             flash("Crime Type and Date are required.", "warning")
             form_data_on_error = {**crime, **request.form}
             # Re-format dates/times for form repopulation on error
             form_data_on_error['DateOfCrime'] = format_date_for_input(form_data_on_error.get('DateOfCrime'))
             form_data_on_error['TimeOfCrime'] = format_time_for_input(form_data_on_error.get('TimeOfCrime'))
             return render_template('edit_crime.html', crime=crime, **dropdown_data, form_data=form_data_on_error)

        query = """
            UPDATE Crimes SET
            CrimeType = %s, Description = %s, DateOfCrime = %s, TimeOfCrime = %s,
            Location = %s, Status = %s, VictimID = %s, SuspectID = %s,
            OfficerID = %s, ReportedByID = %s, EvidenceID = %s
            WHERE CrimeID = %s
        """
        params = (crime_type, description, date_of_crime, time_of_crime, location, status,
                  None if victim_id == 'None' else victim_id,
                  None if suspect_id == 'None' else suspect_id,
                  None if officer_id == 'None' else officer_id,
                  None if reported_by_id == 'None' else reported_by_id,
                  None if evidence_id == 'None' else evidence_id,
                  crime_id)

        success, _ = execute_query(query, params)
        if success:
            flash(f"Crime {crime_id} updated successfully!", "success")
            return redirect(url_for('list_crimes'))
        else:
             # Error already flashed, repopulate form with submitted data
             form_data_on_error = {**crime, **request.form}
             form_data_on_error['DateOfCrime'] = format_date_for_input(form_data_on_error.get('DateOfCrime'))
             form_data_on_error['TimeOfCrime'] = format_time_for_input(form_data_on_error.get('TimeOfCrime'))
             return render_template('edit_crime.html', crime=crime, **dropdown_data, form_data=form_data_on_error)

    # GET request: Format data from DB for form pre-population
    form_data = crime.copy()
    form_data['DateOfCrime'] = format_date_for_input(crime.get('DateOfCrime'))
    form_data['TimeOfCrime'] = format_time_for_input(crime.get('TimeOfCrime'))
    return render_template('edit_crime.html', crime=crime, **dropdown_data, form_data=form_data)

@app.route('/crimes/delete/<int:crime_id>', methods=['POST'])
def delete_crime(crime_id): # DELETE
    crime = fetch_one("SELECT CrimeID FROM Crimes WHERE CrimeID = %s", (crime_id,))
    if not crime:
         flash(f"Cannot delete: Crime with ID {crime_id} not found.", "warning")
         return redirect(url_for('list_crimes'))

    # Related records handled by ON DELETE constraints in DB schema
    query = "DELETE FROM Crimes WHERE CrimeID = %s"
    success, _ = execute_query(query, (crime_id,))
    if success:
        flash(f"Crime {crime_id} deleted successfully.", "success")
    # else: failure message handled by execute_query

    return redirect(url_for('list_crimes'))

# --- Victims ---
@app.route('/victims')
def list_victims(): # READ List
    victims = fetch_all("SELECT * FROM Victims ORDER BY LastName, FirstName")
    return render_template('victims.html', victims=victims)

@app.route('/victims/add', methods=['GET', 'POST'])
def add_victim(): # CREATE
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             return render_template('add_victim.html', form_data=request.form)

        query = "INSERT INTO Victims (FirstName, LastName, DateOfBirth, Address, PhoneNumber, Email) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (first_name, last_name, dob, address, phone, email)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Victim (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_victims'))
        else:
            return render_template('add_victim.html', form_data=request.form)
    # GET request
    return render_template('add_victim.html')

@app.route('/victims/edit/<int:victim_id>', methods=['GET', 'POST'])
def edit_victim(victim_id): # UPDATE
    victim = fetch_one("SELECT * FROM Victims WHERE VictimID = %s", (victim_id,))
    if not victim:
        flash(f"Victim with ID {victim_id} not found.", "warning")
        return redirect(url_for('list_victims'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             form_data_on_error = {**victim, **request.form}
             form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
             return render_template('edit_victim.html', victim=victim, form_data=form_data_on_error)

        query = """
            UPDATE Victims SET
            FirstName = %s, LastName = %s, DateOfBirth = %s, Address = %s,
            PhoneNumber = %s, Email = %s
            WHERE VictimID = %s
        """
        params = (first_name, last_name, dob, address, phone, email, victim_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Victim {victim_id} updated successfully!", "success")
            return redirect(url_for('list_victims'))
        else:
            form_data_on_error = {**victim, **request.form}
            form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
            return render_template('edit_victim.html', victim=victim, form_data=form_data_on_error)

    # GET request: Format data for form
    form_data = victim.copy()
    form_data['DateOfBirth'] = format_date_for_input(victim.get('DateOfBirth'))
    return render_template('edit_victim.html', victim=victim, form_data=form_data)

@app.route('/victims/delete/<int:victim_id>', methods=['POST'])
def delete_victim(victim_id): # DELETE
    victim = fetch_one("SELECT VictimID FROM Victims WHERE VictimID = %s", (victim_id,))
    if not victim:
         flash(f"Cannot delete: Victim with ID {victim_id} not found.", "warning")
         return redirect(url_for('list_victims'))

    # Check if linked - constraint is ON DELETE SET NULL
    linked_crimes = fetch_one("SELECT 1 FROM Crimes WHERE VictimID = %s LIMIT 1", (victim_id,))
    if linked_crimes:
        flash(f"Warning: Deleting Victim {victim_id}. Associated crime records will have VictimID set to NULL.", "info")

    query = "DELETE FROM Victims WHERE VictimID = %s"
    success, _ = execute_query(query, (victim_id,))
    if success:
        flash(f"Victim {victim_id} deleted successfully.", "success")
    # else: error flashed by execute_query

    return redirect(url_for('list_victims'))

# --- Suspects ---
@app.route('/suspects')
def list_suspects(): # READ List
    suspects = fetch_all("SELECT * FROM Suspects ORDER BY LastName, FirstName")
    return render_template('suspects.html', suspects=suspects)

@app.route('/suspects/add', methods=['GET', 'POST'])
def add_suspect(): # CREATE
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        criminal_record = request.form.get('criminal_record')
        known_aliases = request.form.get('known_aliases')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             return render_template('add_suspect.html', form_data=request.form)

        query = "INSERT INTO Suspects (FirstName, LastName, DateOfBirth, Address, PhoneNumber, CriminalRecord, KnownAliases) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        params = (first_name, last_name, dob, address, phone, criminal_record, known_aliases)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Suspect (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_suspects'))
        else:
            return render_template('add_suspect.html', form_data=request.form)
    # GET request
    return render_template('add_suspect.html')

@app.route('/suspects/edit/<int:suspect_id>', methods=['GET', 'POST'])
def edit_suspect(suspect_id): # UPDATE
    suspect = fetch_one("SELECT * FROM Suspects WHERE SuspectID = %s", (suspect_id,))
    if not suspect:
        flash(f"Suspect with ID {suspect_id} not found.", "warning")
        return redirect(url_for('list_suspects'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        criminal_record = request.form.get('criminal_record')
        known_aliases = request.form.get('known_aliases')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             form_data_on_error = {**suspect, **request.form}
             form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
             return render_template('edit_suspect.html', suspect=suspect, form_data=form_data_on_error)

        query = """
            UPDATE Suspects SET
            FirstName = %s, LastName = %s, DateOfBirth = %s, Address = %s, PhoneNumber = %s,
            CriminalRecord = %s, KnownAliases = %s
            WHERE SuspectID = %s
        """
        params = (first_name, last_name, dob, address, phone, criminal_record, known_aliases, suspect_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Suspect {suspect_id} updated successfully!", "success")
            return redirect(url_for('list_suspects'))
        else:
            form_data_on_error = {**suspect, **request.form}
            form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
            return render_template('edit_suspect.html', suspect=suspect, form_data=form_data_on_error)

    # GET request
    form_data = suspect.copy()
    form_data['DateOfBirth'] = format_date_for_input(suspect.get('DateOfBirth'))
    return render_template('edit_suspect.html', suspect=suspect, form_data=form_data)

@app.route('/suspects/delete/<int:suspect_id>', methods=['POST'])
def delete_suspect(suspect_id): # DELETE
    suspect = fetch_one("SELECT SuspectID FROM Suspects WHERE SuspectID = %s", (suspect_id,))
    if not suspect:
         flash(f"Cannot delete: Suspect with ID {suspect_id} not found.", "warning")
         return redirect(url_for('list_suspects'))

    # Check if linked - constraint is ON DELETE SET NULL
    linked_crimes = fetch_one("SELECT 1 FROM Crimes WHERE SuspectID = %s LIMIT 1", (suspect_id,))
    if linked_crimes:
        flash(f"Warning: Deleting Suspect {suspect_id}. Associated crime records will have SuspectID set to NULL.", "info")

    query = "DELETE FROM Suspects WHERE SuspectID = %s"
    success, _ = execute_query(query, (suspect_id,))
    if success:
        flash(f"Suspect {suspect_id} deleted successfully.", "success")
    return redirect(url_for('list_suspects'))

# --- Officers ---
@app.route('/officers')
def list_officers(): # READ List
    # Fetching Rank1 from DB but might display as 'Rank'
    officers = fetch_all("SELECT OfficerID, FirstName, LastName, BadgeNumber, Rank1, Department, ContactNumber, Email FROM Officers ORDER BY LastName, FirstName")
    return render_template('officers.html', officers=officers)

@app.route('/officers/add', methods=['GET', 'POST'])
def add_officer(): # CREATE
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        badge_number = request.form.get('badge_number')
        rank = request.form.get('rank') # Form uses 'rank'
        department = request.form.get('department')
        contact = request.form.get('contact')
        email = request.form.get('email')

        if not first_name or not last_name or not badge_number:
             flash("First Name, Last Name, and Badge Number are required.", "warning")
             return render_template('add_officer.html', form_data=request.form)

        # Check unique badge number before insert
        existing_officer = fetch_one("SELECT 1 FROM Officers WHERE BadgeNumber = %s", (badge_number,))
        if existing_officer:
            flash(f"Badge Number '{badge_number}' already exists.", "danger")
            return render_template('add_officer.html', form_data=request.form)

        # Insert using Rank1 column name
        query = "INSERT INTO Officers (FirstName, LastName, BadgeNumber, Rank1, Department, ContactNumber, Email) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        params = (first_name, last_name, badge_number, rank, department, contact, email)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Officer (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_officers'))
        else:
            # Error flashed by execute_query
            return render_template('add_officer.html', form_data=request.form)
    # GET request
    return render_template('add_officer.html')

@app.route('/officers/edit/<int:officer_id>', methods=['GET', 'POST'])
def edit_officer(officer_id): # UPDATE
    # Fetch including Rank1
    officer = fetch_one("SELECT * FROM Officers WHERE OfficerID = %s", (officer_id,))
    if not officer:
        flash(f"Officer with ID {officer_id} not found.", "warning")
        return redirect(url_for('list_officers'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        badge_number = request.form.get('badge_number')
        rank = request.form.get('rank') # Form uses 'rank'
        department = request.form.get('department')
        contact = request.form.get('contact')
        email = request.form.get('email')

        if not first_name or not last_name or not badge_number:
             flash("First Name, Last Name, and Badge Number are required.", "warning")
             form_data_on_error = {**officer, **request.form}
             # Ensure 'rank' field is populated for form refill
             form_data_on_error['rank'] = form_data_on_error.get('Rank1') if 'rank' not in form_data_on_error else form_data_on_error['rank']
             return render_template('edit_officer.html', officer=officer, form_data=form_data_on_error)

        # Check unique badge number only if it changed
        if badge_number != officer.get('BadgeNumber'):
            existing_officer = fetch_one("SELECT OfficerID FROM Officers WHERE BadgeNumber = %s AND OfficerID != %s", (badge_number, officer_id))
            if existing_officer:
                flash(f"Badge Number '{badge_number}' already exists for another officer.", "danger")
                form_data_on_error = {**officer, **request.form}
                form_data_on_error['rank'] = form_data_on_error.get('Rank1') if 'rank' not in form_data_on_error else form_data_on_error['rank']
                return render_template('edit_officer.html', officer=officer, form_data=form_data_on_error)

        # Update using Rank1 column name
        query = """
            UPDATE Officers SET
            FirstName = %s, LastName = %s, BadgeNumber = %s, Rank1 = %s, Department = %s,
            ContactNumber = %s, Email = %s
            WHERE OfficerID = %s
        """
        params = (first_name, last_name, badge_number, rank, department, contact, email, officer_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Officer {officer_id} updated successfully!", "success")
            return redirect(url_for('list_officers'))
        else:
            # Error flashed by execute_query
            form_data_on_error = {**officer, **request.form}
            form_data_on_error['rank'] = form_data_on_error.get('Rank1') if 'rank' not in form_data_on_error else form_data_on_error['rank']
            return render_template('edit_officer.html', officer=officer, form_data=form_data_on_error)

    # GET request: Prepare form data, mapping Rank1 to 'rank'
    form_data = officer.copy()
    form_data['rank'] = officer.get('Rank1') # Map DB Rank1 to form field 'rank'
    return render_template('edit_officer.html', officer=officer, form_data=form_data)

@app.route('/officers/delete/<int:officer_id>', methods=['POST'])
def delete_officer(officer_id): # DELETE
    officer = fetch_one("SELECT OfficerID FROM Officers WHERE OfficerID = %s", (officer_id,))
    if not officer:
         flash(f"Cannot delete: Officer with ID {officer_id} not found.", "warning")
         return redirect(url_for('list_officers'))

    # ON DELETE SET NULL constraints handle related records in DB
    query = "DELETE FROM Officers WHERE OfficerID = %s"
    success, _ = execute_query(query, (officer_id,))
    if success:
        flash(f"Officer {officer_id} deleted. Related record links set to NULL.", "success")
    # else: error flashed by execute_query

    return redirect(url_for('list_officers'))

# --- Witnesses ---
@app.route('/witnesses')
def list_witnesses(): # READ List
    query = """
        SELECT w.*, c.CrimeType, DATE_FORMAT(c.DateOfCrime, '%Y-%m-%d') as CrimeDate
        FROM Witnesses w
        LEFT JOIN Crimes c ON w.CrimeID = c.CrimeID
        ORDER BY w.LastName, w.FirstName
    """
    witnesses = fetch_all(query)
    return render_template('witnesses.html', witnesses=witnesses)

@app.route('/witnesses/add', methods=['GET', 'POST'])
def add_witness(): # CREATE
    dropdown_data = get_dropdown_data()
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        crime_id = request.form.get('crime_id')
        statement = request.form.get('statement')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             return render_template('add_witness.html', **dropdown_data, form_data=request.form)

        query = "INSERT INTO Witnesses (FirstName, LastName, DateOfBirth, Address, PhoneNumber, Email, CrimeID, Statement) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        params = (first_name, last_name, dob, address, phone, email,
                  None if crime_id == 'None' else crime_id, statement)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Witness (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_witnesses'))
        else:
            return render_template('add_witness.html', **dropdown_data, form_data=request.form)
    # GET request
    return render_template('add_witness.html', **dropdown_data)

@app.route('/witnesses/edit/<int:witness_id>', methods=['GET', 'POST'])
def edit_witness(witness_id): # UPDATE
    dropdown_data = get_dropdown_data()
    witness = fetch_one("SELECT * FROM Witnesses WHERE WitnessID = %s", (witness_id,))
    if not witness:
        flash(f"Witness with ID {witness_id} not found.", "warning")
        return redirect(url_for('list_witnesses'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        crime_id = request.form.get('crime_id')
        statement = request.form.get('statement')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             form_data_on_error = {**witness, **request.form}
             form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
             return render_template('edit_witness.html', witness=witness, **dropdown_data, form_data=form_data_on_error)

        query = """
            UPDATE Witnesses SET
            FirstName = %s, LastName = %s, DateOfBirth = %s, Address = %s, PhoneNumber = %s,
            Email = %s, CrimeID = %s, Statement = %s
            WHERE WitnessID = %s
        """
        params = (first_name, last_name, dob, address, phone, email,
                  None if crime_id == 'None' else crime_id, statement, witness_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Witness {witness_id} updated successfully!", "success")
            return redirect(url_for('list_witnesses'))
        else:
            form_data_on_error = {**witness, **request.form}
            form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
            return render_template('edit_witness.html', witness=witness, **dropdown_data, form_data=form_data_on_error)

    # GET request
    form_data = witness.copy()
    form_data['DateOfBirth'] = format_date_for_input(witness.get('DateOfBirth'))
    return render_template('edit_witness.html', witness=witness, **dropdown_data, form_data=form_data)

@app.route('/witnesses/delete/<int:witness_id>', methods=['POST'])
def delete_witness(witness_id): # DELETE
    witness = fetch_one("SELECT WitnessID FROM Witnesses WHERE WitnessID = %s", (witness_id,))
    if not witness:
         flash(f"Cannot delete: Witness with ID {witness_id} not found.", "warning")
         return redirect(url_for('list_witnesses'))

    # Simple delete - constraint handles CrimeID link
    query = "DELETE FROM Witnesses WHERE WitnessID = %s"
    success, _ = execute_query(query, (witness_id,))
    if success:
        flash(f"Witness {witness_id} deleted successfully.", "success")
    return redirect(url_for('list_witnesses'))

# --- Evidence ---
@app.route('/evidence')
def list_evidence(): # READ List
    query = """
        SELECT e.*, CONCAT(o.FirstName, ' ', o.LastName, ' (', o.BadgeNumber, ')') as CollectedByName
        FROM Evidence e
        LEFT JOIN Officers o ON e.CollectedByID = o.OfficerID
        ORDER BY e.DateCollected DESC, e.EvidenceID DESC
    """
    evidence_list = fetch_all(query)
    return render_template('evidence.html', evidence_list=evidence_list)

@app.route('/evidence/add', methods=['GET', 'POST'])
def add_evidence(): # CREATE
    dropdown_data = get_dropdown_data()
    if request.method == 'POST':
        evidence_type = request.form.get('evidence_type')
        description = request.form.get('description')
        date_collected = request.form.get('date_collected') or None
        location_collected = request.form.get('location_collected')
        collected_by_id = request.form.get('collected_by_id')

        query = "INSERT INTO Evidence (EvidenceType, Description, DateCollected, LocationCollected, CollectedByID) VALUES (%s, %s, %s, %s, %s)"
        params = (evidence_type, description, date_collected, location_collected,
                   None if collected_by_id == 'None' else collected_by_id)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Evidence (ID: {new_id}) added. Link it to a Crime if needed.", "success")
            return redirect(url_for('list_evidence'))
        else:
            return render_template('add_evidence.html', **dropdown_data, form_data=request.form)
    # GET request
    return render_template('add_evidence.html', **dropdown_data)

@app.route('/evidence/edit/<int:evidence_id>', methods=['GET', 'POST'])
def edit_evidence(evidence_id): # UPDATE
    dropdown_data = get_dropdown_data()
    evidence_item = fetch_one("SELECT * FROM Evidence WHERE EvidenceID = %s", (evidence_id,))
    if not evidence_item:
        flash(f"Evidence with ID {evidence_id} not found.", "warning")
        return redirect(url_for('list_evidence'))

    if request.method == 'POST':
        evidence_type = request.form.get('evidence_type')
        description = request.form.get('description')
        date_collected = request.form.get('date_collected') or None
        location_collected = request.form.get('location_collected')
        collected_by_id = request.form.get('collected_by_id')

        query = """
            UPDATE Evidence SET
            EvidenceType = %s, Description = %s, DateCollected = %s,
            LocationCollected = %s, CollectedByID = %s
            WHERE EvidenceID = %s
        """
        params = (evidence_type, description, date_collected, location_collected,
                  None if collected_by_id == 'None' else collected_by_id, evidence_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Evidence {evidence_id} updated successfully!", "success")
            return redirect(url_for('list_evidence'))
        else:
            form_data_on_error = {**evidence_item, **request.form}
            form_data_on_error['DateCollected'] = format_date_for_input(form_data_on_error.get('DateCollected'))
            return render_template('edit_evidence.html', evidence_item=evidence_item, **dropdown_data, form_data=form_data_on_error)

    # GET request
    form_data = evidence_item.copy()
    form_data['DateCollected'] = format_date_for_input(evidence_item.get('DateCollected'))
    return render_template('edit_evidence.html', evidence_item=evidence_item, **dropdown_data, form_data=form_data)

@app.route('/evidence/delete/<int:evidence_id>', methods=['POST'])
def delete_evidence(evidence_id): # DELETE
    evidence_item = fetch_one("SELECT EvidenceID FROM Evidence WHERE EvidenceID = %s", (evidence_id,))
    if not evidence_item:
         flash(f"Cannot delete: Evidence with ID {evidence_id} not found.", "warning")
         return redirect(url_for('list_evidence'))

    # Check if linked - constraint is ON DELETE SET NULL
    linked_crimes = fetch_one("SELECT 1 FROM Crimes WHERE EvidenceID = %s LIMIT 1", (evidence_id,))
    if linked_crimes:
        flash(f"Warning: Deleting Evidence {evidence_id}. Associated crime records will have EvidenceID set to NULL.", "info")

    query = "DELETE FROM Evidence WHERE EvidenceID = %s"
    success, _ = execute_query(query, (evidence_id,))
    if success:
        flash(f"Evidence {evidence_id} deleted successfully.", "success")
    return redirect(url_for('list_evidence'))

# --- Reports ---
@app.route('/reports')
def list_reports(): # READ List
    query = """
        SELECT r.*, c.CrimeType as RelatedCrimeType,
               CONCAT(o.FirstName, ' ', o.LastName) as OfficerName,
               DATE_FORMAT(r.ReportDate, '%Y-%m-%d') as FormattedReportDate,
               DATE_FORMAT(c.DateOfCrime, '%Y-%m-%d') as CrimeDate
        FROM Reports r
        LEFT JOIN Crimes c ON r.CrimeID = c.CrimeID
        LEFT JOIN Officers o ON r.OfficerID = o.OfficerID
        ORDER BY r.ReportDate DESC, r.ReportID DESC
    """
    reports = fetch_all(query)
    return render_template('reports.html', reports=reports)

@app.route('/reports/add', methods=['GET', 'POST'])
def add_report(): # CREATE
    dropdown_data = get_dropdown_data()
    if request.method == 'POST':
        report_date = request.form.get('report_date') or None
        report_type = request.form.get('report_type')
        description = request.form.get('description')
        crime_id = request.form.get('crime_id')
        officer_id = request.form.get('officer_id')

        query = "INSERT INTO Reports (ReportDate, ReportType, Description, CrimeID, OfficerID) VALUES (%s, %s, %s, %s, %s)"
        params = (report_date, report_type, description,
                  None if crime_id == 'None' else crime_id,
                  None if officer_id == 'None' else officer_id)
        success, new_id = execute_query(query, params)
        if success:
            flash(f"Report (ID: {new_id}) added successfully!", "success")
            return redirect(url_for('list_reports'))
        else:
             return render_template('add_report.html', **dropdown_data, form_data=request.form)
    # GET request
    return render_template('add_report.html', **dropdown_data)

@app.route('/reports/edit/<int:report_id>', methods=['GET', 'POST'])
def edit_report(report_id): # UPDATE
    dropdown_data = get_dropdown_data()
    report_item = fetch_one("SELECT * FROM Reports WHERE ReportID = %s", (report_id,))
    if not report_item:
        flash(f"Report with ID {report_id} not found.", "warning")
        return redirect(url_for('list_reports'))

    if request.method == 'POST':
        report_date = request.form.get('report_date') or None
        report_type = request.form.get('report_type')
        description = request.form.get('description')
        crime_id = request.form.get('crime_id')
        officer_id = request.form.get('officer_id')

        query = """
            UPDATE Reports SET
            ReportDate = %s, ReportType = %s, Description = %s, CrimeID = %s, OfficerID = %s
            WHERE ReportID = %s
        """
        params = (report_date, report_type, description,
                  None if crime_id == 'None' else crime_id,
                  None if officer_id == 'None' else officer_id, report_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Report {report_id} updated successfully!", "success")
            return redirect(url_for('list_reports'))
        else:
            form_data_on_error = {**report_item, **request.form}
            form_data_on_error['ReportDate'] = format_date_for_input(form_data_on_error.get('ReportDate'))
            return render_template('edit_report.html', report_item=report_item, **dropdown_data, form_data=form_data_on_error)

    # GET request
    form_data = report_item.copy()
    form_data['ReportDate'] = format_date_for_input(report_item.get('ReportDate'))
    return render_template('edit_report.html', report_item=report_item, **dropdown_data, form_data=form_data)

@app.route('/reports/delete/<int:report_id>', methods=['POST'])
def delete_report(report_id): # DELETE
    report_item = fetch_one("SELECT ReportID FROM Reports WHERE ReportID = %s", (report_id,))
    if not report_item:
         flash(f"Cannot delete: Report with ID {report_id} not found.", "warning")
         return redirect(url_for('list_reports'))

    # Simple delete - constraints handle links
    query = "DELETE FROM Reports WHERE ReportID = %s"
    success, _ = execute_query(query, (report_id,))
    if success:
        flash(f"Report {report_id} deleted successfully.", "success")
    return redirect(url_for('list_reports'))

# --- ReportedBy ---
@app.route('/reported_by')
def list_reported_by(): # READ List
    reporters = fetch_all("SELECT * FROM ReportedBy ORDER BY LastName, FirstName")
    return render_template('reported_by.html', reporters=reporters)

@app.route('/reported_by/add', methods=['GET', 'POST'])
def add_reported_by(): # CREATE
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             return render_template('add_reported_by.html', form_data=request.form)

        query = "INSERT INTO ReportedBy (FirstName, LastName, DateOfBirth, Address, PhoneNumber, Email) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (first_name, last_name, dob, address, phone, email)
        success, new_id = execute_query(query, params)
        if success:
             flash(f"Reporter (ID: {new_id}) added. Link them to a Crime if needed.", "success")
             return redirect(url_for('list_reported_by'))
        else:
            return render_template('add_reported_by.html', form_data=request.form)
    # GET request
    return render_template('add_reported_by.html')

@app.route('/reported_by/edit/<int:reporter_id>', methods=['GET', 'POST'])
def edit_reported_by(reporter_id): # UPDATE
    reporter = fetch_one("SELECT * FROM ReportedBy WHERE ReportedByID = %s", (reporter_id,))
    if not reporter:
        flash(f"Reporter with ID {reporter_id} not found.", "warning")
        return redirect(url_for('list_reported_by'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob') or None
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not first_name or not last_name:
             flash("First and Last Name are required.", "warning")
             form_data_on_error = {**reporter, **request.form}
             form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
             return render_template('edit_reported_by.html', reporter=reporter, form_data=form_data_on_error)

        query = """
            UPDATE ReportedBy SET
            FirstName = %s, LastName = %s, DateOfBirth = %s, Address = %s,
            PhoneNumber = %s, Email = %s
            WHERE ReportedByID = %s
        """
        params = (first_name, last_name, dob, address, phone, email, reporter_id)
        success, _ = execute_query(query, params)
        if success:
            flash(f"Reporter {reporter_id} updated successfully!", "success")
            return redirect(url_for('list_reported_by'))
        else:
            form_data_on_error = {**reporter, **request.form}
            form_data_on_error['DateOfBirth'] = format_date_for_input(form_data_on_error.get('DateOfBirth'))
            return render_template('edit_reported_by.html', reporter=reporter, form_data=form_data_on_error)

    # GET request
    form_data = reporter.copy()
    form_data['DateOfBirth'] = format_date_for_input(reporter.get('DateOfBirth'))
    return render_template('edit_reported_by.html', reporter=reporter, form_data=form_data)

@app.route('/reported_by/delete/<int:reporter_id>', methods=['POST'])
def delete_reported_by(reporter_id): # DELETE
    reporter = fetch_one("SELECT ReportedByID FROM ReportedBy WHERE ReportedByID = %s", (reporter_id,))
    if not reporter:
         flash(f"Cannot delete: Reporter with ID {reporter_id} not found.", "warning")
         return redirect(url_for('list_reported_by'))

    # Check if linked - constraint is ON DELETE SET NULL
    linked_crimes = fetch_one("SELECT 1 FROM Crimes WHERE ReportedByID = %s LIMIT 1", (reporter_id,))
    if linked_crimes:
        flash(f"Warning: Deleting Reporter {reporter_id}. Associated crime records will have ReportedByID set to NULL.", "info")

    query = "DELETE FROM ReportedBy WHERE ReportedByID = %s"
    success, _ = execute_query(query, (reporter_id,))
    if success:
        flash(f"Reporter {reporter_id} deleted successfully.", "success")
    return redirect(url_for('list_reported_by'))

# --- Main Execution ---
if __name__ == '__main__':
    # Debug mode should be turned OFF in production
    # Use host='0.0.0.0' to make accessible on network (use with caution)
    app.run(debug=True)