from flask import redirect, render_template, request, session, url_for
from functools import wraps


def commLogin_required(f):
    """ Decorate routes to require login of a committee.
        Derived from: http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/ """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # checks is user login
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        # checks if user has a committee login (an int)
        elif session.get("user_id") < 0:
            return redirect(url_for("crisis", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """ Decorate routes to require any login.
        http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/ """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # checks is user login
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def isInt(s):
    """ Checks if a string is an integer. """
    try:
        int(s)
        return True
    except ValueError:
        return False
        
def commaStringParse(string):
    """ Parses a string with comma separated values """
    dels = []
    cur = ""
    length = len(string)
    for c in string:
        # skip spaces outside words
        if c ==  " " and cur == "":
            continue
        # new delegation found
        elif c == ",":
            dels.append(cur)
            cur = ""
        # last name in list
        elif string.index(c) == length - 1:
            cur += c
            dels.append(cur)
        else:
            cur += c
    return dels