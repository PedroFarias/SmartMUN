#from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
import os
import psycopg2
import psycopg2.extras
import urlparse
#from flask_sqlalchemy import SQLAlchemy
from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
#db = SQLAlchemy(app)
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port)

db = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

"""Functions w/Database Alterations"""
def updateReqs():
    """ Updates statistics about committee"""
    
    db.execute("SELECT members FROM users WHERE id = %s;",(session["user_id"],))
    table = db.fetchall()
    # update values
    session["total"] = int(table[0]["members"])
    session["qualifiedMaj"] = int(session["total"] * 2/3)
    session["simpleMaj"] = int((session["total"] / 2) + 1) if \
        session["total"] != 0 else 0
    session["fifthComm"] = int(session["total"] / 5)
    
def updateDelInfo(column, value, table, delName, tableName):
    """ Updates one of the stats about a delegation's participation"""
    
    newVal = table[0][column] + value
    db.execute("UPDATE " + tableName + " SET %s = %s WHERE \
        delName = %s;", (column, newVal, delName))
    conn.commit()

"""Routes"""
@app.route("/", methods=["GET", "POST"])
@commLogin_required
def index():
    """Shows committee information"""
    
    # form submitted
    if request.method == "POST":
        # ensure speaker was input
        if not request.form.get("delName"):
            return render_template("error.html", 
                error="Please provide speaker's name.")
        
        # ensure delegation is in committee
        tableName = "comm{}".format(session["commCode"])
        db.execute("SELECT * FROM " + tableName + " WHERE delName = %s;",
            (request.form.get("delName"),))
        table = db.fetchall()

	if len(table) == 0:
            return render_template("error.html", 
                error="This delegation must first be added to the committee.")
        
        # update number of speeches
        updateDelInfo("speeches", 1, table, request.form.get("delName"),
            tableName)
    
    # prepare to render
    updateReqs()
    db.execute("SELECT * FROM users WHERE id = %s;",
        (session["commCode"],))
    table = db.fetchall()
    commName = table[0]["username"]
    tableName = "comm{}".format(session["commCode"])
    db.execute("SELECT * FROM " + tableName + " ORDER BY delName;")
    delegations = db.fetchall()
    conn.commit()

    return render_template("index.html", total=session["total"], 
        qualifiedMaj=session["qualifiedMaj"], simpleMaj=session["simpleMaj"],
        fifthComm=session["fifthComm"], delegations=delegations, 
        currentSpeaker=request.form.get("delName"))
        
@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs user in."""
    
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure fields are complete
        if not request.form.get("username"):
            return render_template("error.html", 
                error="Please provide the username.")
        elif not request.form.get("password"):
            return render_template("error.html", 
                error="Please provide the password.")
        
        checked = request.form.get("delCheck")
        if checked:
            # ensure committee name & code were submitted
            if not request.form.get("commName"):
                return render_template("error.html", 
                    error="Please provide the committee name.")
            elif not request.form.get("commCode"):
                return render_template("error.html", 
                    error="Please provide the committee code.")
                    
            # check if committee code and name match
            db.execute("SELECT username FROM users WHERE id = %s;",
                (request.form.get("commCode"),))
            rows = db.fetchall()
            # ensure committee was registered    
            if len(rows) != 1:
                return render_template("error.html", 
                    error="This committee was not registered.")
            elif rows[0]["username"] != request.form.get("commName"):
                return render_template("error.html", 
                    error="Committee name and code don't match.")

            # query database for username
            tableName = "comm{}".format(request.form.get("commCode"))
            db.execute("SELECT * FROM " + tableName + " WHERE delName = %s;",
                (request.form.get("username").upper(),))
            rows = db.fetchall()
            # ensure username exists and password is correct
            if rows[0]["hash"] is None:
                return render_template("error.html", 
                    error="Delegation not yet registered.")
            
            if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), \
            rows[0]["hash"]):
                return render_template("error.html", 
                    error="Invalid username or password.")
                
            # remember which user has logged in
            session["commCode"] = request.form.get("commCode")
            session["user_id"] = -1 * rows[0]["delId"]
            
            # redirect user to crisis page
            conn.commit()
            return redirect(url_for("crisis"))
        
        # logging in as a committee manager
        else:
            db.execute("SELECT * FROM users WHERE username = %s",
                (request.form.get("username"),))
            rows = db.fetchall()
            # ensure username exists and password is correct
            if len(rows) != 1 or not pwd_context.verify(request.form.get("password"),
                rows[0]["hash"]):
                return render_template("error.html", 
                    error="Invalid username or password.")

            # remember which user has logged in
            session["user_id"] = rows[0]["id"]
            session["commCode"] = session["user_id"]

            # redirect user to home page
            conn.commit()
            return redirect(url_for("manager"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        
@app.route("/logout")
def logout():
    """Log user out."""
    
    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
    
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure all fields complete
        if not request.form.get("username"):
            return render_template("error.html", 
                error="Delegation name cannot be blank.")
        elif not request.form.get("password"):
            return render_template("error.html", 
                error="Password cannot be blank.")
        elif not request.form.get("confPass"):
            return render_template("error.html", 
                error="Please confirm your password.")
        # check passwords match    
        elif request.form.get("password") != request.form.get("confPass"):
            return render_template("error.html", 
                error="The passwords do not match.")
        
        # see if we are logging in as a delegate
        checked = request.form.get("delCheck")
        if checked:
            if not request.form.get("commName"):
                return render_template("error.html", 
                    error="Committee name cannot be blank.")
            elif not request.form.get("commCode"):
                return render_template("error.html", 
                    error="Committee code cannot be blank.")
                
            # check if committee code and name match
            db.execute("SELECT username FROM users WHERE id = :id;",
               (request.form.get("commCode"),))
            rows = db.fetchall()
            if len(rows) != 1:
                return render_template("error.html", 
                    error="Committee not found.")
                
            if rows[0]["username"] != request.form.get("commName"):
                return render_template("error.html", 
                    error="Committee name and code don't match.")

            # query database for username
            tableName = "comm{}".format(request.form.get("commCode"))
            db.execute("SELECT * FROM " + tableName + " WHERE delName = %s;",
                (request.form.get("username").upper(),))
            rows = db.fetchall()
            # check if username has already been taken
            if not rows[0]["hash"] is None:
                return render_template("error.html", 
                    error="This delegation has already been registered.")
    
            # register user w/hashed password
            db.execute("UPDATE " + tableName + " SET hash = %s WHERE delName = %s;", 
                (pwd_context.encrypt(request.form["password"]),
		request.form.get("username").upper()))
                
        # logging in as a committee manager
        else:
            # query database for username
            db.execute("SELECT * FROM users WHERE username = %s;", (request.form.get("username"),))
            rows = db.fetchall()

            # check if username has already been taken
            if len(rows) != 0:
                return render_template("error.html", 
                    error="This username has already been taken, please choose another.")
    
            # register user w/hashed password
            db.execute("INSERT INTO users (username, hash) VALUES (%s, %s);", 
                (request.form["username"], pwd_context.encrypt(request.form["password"])))
            
            # create committee table
            db.execute("SELECT id FROM users WHERE username = %s;",
                (request.form["username"],))
            rows = db.fetchall()
            tableName = "comm{}".format(rows[0]["id"])
            db.execute("CREATE TABLE " + tableName + " (delId serial PRIMARY KEY \
                NOT NULL, delName text NOT NULL, speeches \
                INTEGER DEFAULT 0, resos INTEGER DEFAULT 0, amendments \
                INTEGER DEFAULT 0, sessions INTEGER DEFAULT 0, hash \
                TEXT)")
            
    # redirect user to login page
    conn.commit()
    return redirect(url_for("login"))

    # else if user reached route via GET (by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/resetpass", methods=["GET", "POST"])
@login_required
def resetpass():
    """Reset user's password."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure all fields complete
        if not request.form.get("oldPass"):
            return render_template("error.html", 
                error="Please provide your old password.")
        elif not request.form.get("newPass"):
            return render_template("error.html", 
                error="Please provide your new password.")
        elif not request.form.get("confNewPass"):
            return render_template("error.html", 
                error="Please confirm your new password.")
        
        # delegate logged in
        if session["user_id"] < 0:
            tableName = "comm{}".format(commCode)
            db.execute("SELECT hash FROM " + tableName + " WHERE delId = %s;",
                (-1*session["user_id"],))
            currentPass = db.fetchall()
        # committee logged in
        else:
            db.execute("SELECT hash FROM users WHERE id = %s;",
                (session["user_id"],))
            currentPass = db.fetchall()

        # ensure password is correct
        if not pwd_context.verify(request.form.get("oldPass"), 
            currentPass[0]["hash"]):
            return render_template("error.html", 
                error="The old password is incorrect.")
        # check new passwords match    
        elif request.form.get("newPass") != request.form.get("confNewPass"):
            return render_template("error.html", 
                error="New passwords do not match.")
        # ensure passwords are different
        elif request.form.get("oldPass") == request.form.get("newPass"):
            return render_template("error.html", 
                error="Passwords must be different.")

        # delegate logged in
        if session["user_id"] < 0:
            tableName = "comm{}".format(commCode)
            db.execute("UPDATE " + tableName + " SET hash = %s WHERE delId = %s;",
                (pwd_context.encrypt(request.form["newPass"]), 
                -1*session["user_id"]))
        # update password: committee logged in
        else:
            db.execute("UPDATE users SET hash = %s WHERE id = %s;",
                (pwd_context.encrypt(request.form["newPass"]), 
                session["user_id"]))
        
        success = "Password modified successfully!"
        conn.commit()
        return render_template("resetpass.html", success=success)
    else:
        return render_template("resetpass.html")
        
@app.route("/manager", methods=["GET", "POST"])
@commLogin_required
def manager():
    """Manages committee information."""
    
    # update info
    tableName = "comm{}".format(session["commCode"])
    db.execute("SELECT * FROM " + tableName + ";")
    delegations = db.fetchall()

    if request.method == "POST":
        # check if already in committee
        if not request.form.get("delName"):
            return render_template("error.html", 
                error="Please inform the delegation(s) to be modified.")
        
        # prepare parse string with commas
        delete = request.form.get("delete")
        names = request.form.get("delName").upper()
        
        # add each delegation to this array
        dels = commaStringParse(names)
        
        #  check operation for each country
        for delName in dels:
            db.execute("SELECT * FROM " + tableName + " WHERE delName = %s;",
                (delName,))
            table = db.fetchall()
    
            # attempted to add the delegation already in committee
            if len(table) != 0 and (not request.form.get("resos")) and \
                (not request.form.get("amendments")) and \
                (not request.form.get("speeches")) and \
                (not request.form.get("sessions")) and\
                (not delete):
                return render_template("error.html", 
                    error="This delegation is already in the committee.")
            # ensure delegation is in committee
            elif len(table) == 0 and (not (request.form.get("resos") is None)) and\
                (not (request.form.get("amendments") is not None)) and \
                (not (request.form.get("sessions") is not None)) and \
                (not (request.form.get("speeches") is not None)):
                return render_template("error.html", 
                    error="This delegation must first be added to the committee.")
            
            # add member if necessary
            if len(table) == 0:
                db.execute("INSERT INTO " + tableName + " (delName) VALUES (%s);", 
                    (delName,))
                table = db.execute("SELECT * FROM " + tableName + ";")
                newMem = len(table)
                db.execute("UPDATE users SET members = %s WHERE id = %s;",
                    (newMem, session["user_id"]))
    
            # delete member if necessary     
            if delete:
                db.execute("DELETE FROM " + tableName + " WHERE delName = %s;",
                    (delName,))
                table = db.execute("SELECT * FROM " + tableName + ";")
                newMem = len(table)
                db.execute("UPDATE users SET members = %s WHERE id = %s;",
                    (newMem, session["user_id"]))
                    
            # update resolution information if necessary
            if isInt(request.form.get("resos")):
                updateDelInfo("resos", int(request.form.get("resos")), 
                    table, delName, tableName)
            elif len(request.form.get("resos")) != 0:
                return render_template("error.html", 
                    error="The input for resolutions must be an integer.")
            # update amendments information if necessary
            if isInt(request.form.get("amendments")):
                updateDelInfo("amendments", int(request.form.get("amendments")), 
                    table, delName, tableName)
            elif len(request.form.get("amendments")) != 0:
                return render_template("error.html", 
                    error="The input for amendments must be an integer.")
            # update speech information if necessary
            if isInt(request.form.get("speeches")):
                updateDelInfo("speeches", int(request.form.get("speeches")), 
                    table, delName, tableName)
            elif len(request.form.get("speeches")) != 0:
                return render_template("error.html", 
                    error="The input for speeches must be an integer.")
            # update session information if necessary
            if isInt(request.form.get("sessions")):
                updateDelInfo("sessions", int(request.form.get("sessions")), 
                    table, delName, tableName)
            elif len(request.form.get("sessions")) != 0:
                return render_template("error.html", 
                    error="The input for sessions must be an integer.")
    
    # prepare to render template
    db.execute("SELECT * FROM " + tableName + " ORDER BY delName ASC;", 
        (tableName,))
    delegations = db.fetchall()
    db.execute("SELECT * FROM users WHERE id = %s;",
        (session["user_id"],))
    table = db.fetchall()
    commName = table[0]["username"]
    updateReqs()
    conn.commit()
    return render_template("manager.html", total=session["total"], 
        qualifiedMaj=session["qualifiedMaj"], simpleMaj=session["simpleMaj"],
        fifthComm=session["fifthComm"], delegations=delegations, 
        commCode=session["user_id"], commName=commName)

@app.route("/crisis")
@login_required
def crisis():
    """Will allow delegates to communicate with each other & manager"""
    
    # prepate to render template
    tableName = "comm{}".format(session["commCode"])
    db.execute("SELECT * FROM " + tableName + " ORDER BY delName ASC;")
    delegations = db.fetchall()
    conn.commit()
    return render_template("crisis.html", delegations=delegations)
    
@app.route("/quickup", methods=["GET", "POST"])
@commLogin_required
def quickup():
    """Enables quick update by clicking on numbers on manager.html."""
    
    # collect information from URL args
    delName = request.args.get("name").upper()
    info = request.args.get("info")
    curVal = request.args.get("curVal")
    up = int(request.args.get("up"))
    tableName = "comm{}".format(session["commCode"])
    db.execute("SELECT * FROM " + tableName + " WHERE delName = %s;", (delName,))
    table = db.fetchall()

    # update sessions
    if info == "sessions":
        updateDelInfo("sessions", up, table, delName, tableName)
    # update amendments
    elif info == "amendments":
        updateDelInfo("amendments", up, table, delName, tableName)
    # update resolutions
    elif info == "resos":
        updateDelInfo("resos", up, table, delName, tableName)
     # update speeches
    elif info == "speeches":
        updateDelInfo("speeches", up, table, delName, tableName)

    # prepare to render template
    db.execute("SELECT * FROM %s ORDER BY delName ASC;",
        (tableName,))
    delegations = db.fetchall()
    db.execute("SELECT * FROM users WHERE id = %s",
        (session["user_id"],))
    table = db.fetchall()
    commName = table[0]["username"]
    updateReqs()  
    conn.commit()

    # render template
    return render_template("manager.html", total=session["total"], 
        qualifiedMaj=session["qualifiedMaj"], simpleMaj=session["simpleMaj"],
        fifthComm=session["fifthComm"], delegations=delegations, 
        commCode=session["user_id"], commName=commName)
