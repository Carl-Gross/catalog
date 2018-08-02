# general imports
import sys, os
sys.path.insert(0, '/var/www/html/catalog/')

from flask import Flask, render_template, request, redirect
from flask import url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from db_setup import Make, Model, Owner
import time

# imports for state token
from flask import session as login_session
import random
import string

# imports for callback authorization
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://catalog:fsbb231@localhost/catalog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_NATIVE_UNICODE'] = False
app.debug = True
app.secret_key = 'super_secret_key'

# get client ID from client_secrets file (dl from google)
CLIENT_ID = json.loads(
            open('/var/www/html/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# connect to database and start session
db = SQLAlchemy(app)

@app.route('/')
def showIndex():
    makes = Make.query.order_by(Make.name).all()
    recent_adds = Model.query.order_by(
                            Model.last_update.desc()).all()
    return render_template('main.html', makes = makes,
                            recent_adds = recent_adds, username = getuser())

@app.route('/showMake/<int:make_id>/')
def showMake(make_id):
    make = Make.query.filter_by(id = make_id).one()
    models = Model.query.filter_by(make_id = make_id).order_by(
            Model.name).all()
    return render_template('showmake.html', make = make,
                            models = models, username = getuser())

@app.route('/showModel/<int:model_id>/')
def showModel(model_id):
    model = Model.query.filter_by(id = model_id).one()
    make_name = Make.query.filter_by(id = model.make_id).one().name
    print('current ID is' + str(getCurrentUserID()) + ' and modelID is '
                            + str(model.owner_id))
    return render_template('showmodel.html', model = model,
                            username = getuser(), make_name = make_name,
                            userID = getCurrentUserID())

@app.route('/showModel/<int:model_id>/JSON/')
def showModelJSON(model_id):
    model = Model.query.filter_by(id = model_id).one()
    return jsonify(model.serialize)

@app.route('/<int:make_id>/addModel/',  methods=['GET', 'POST'])
def addModel(make_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST': #if user submitted the form
        # get the new id by finding the selected make name
        make_id_update = Make.query.filter_by(
                        name = request.form['make']).one()

        # build the new model object from the form inputs
        newModel = Model(name=request.form['name'],
                        description=request.form['description'],
                        make_id=make_id_update.id,
                        owner_id=login_session['user_id'],
                        last_update = str(time.time()))

        #commit to the db and redirect to the original page
        session.add(newModel)
        session.commit()
        flash("New Model Created")
        return redirect(url_for('showMake', make_id = make_id,
                        username = getuser()))
    current_make = Make.query.filter_by(id = make_id).one()
    makes = Make.query.order_by(Make.name).all()
    return render_template('newModel.html', make_id = make_id,
                            makes = makes, current_make = current_make.name,
                            username = getuser())

@app.route('/<int:make_id>/editModel/<int:model_id>', methods=['GET', 'POST'])
def editModel(make_id, model_id):
    model = Model.query.filter_by(id = model_id).one()
    if 'username' not in login_session or getCurrentUserID() != model.owner_id:
        flash("Unauthorized User")
        return redirect('/login')

    if request.method == 'POST':
        make_id_update = Make.query.filter_by(
                            name = request.form['make']).one()

        model.name = request.form['name']
        model.description = request.form['description']
        model.make_id = make_id_update.id

        session.add(model)
        session.commit()
        flash("Model Edited")
        return redirect(url_for('showMake', make_id = make_id,
                                username = getuser()))
    current_make = Make.query.filter_by(id = make_id).one()
    makes = Make.query.order_by(Make.name).all()

    return render_template('editModel.html', model = model,
                            makes = makes, current_make = current_make.name,
                            make_id = make_id, username = getuser())

@app.route('/deleteModel/<int:model_id>',  methods=['GET', 'POST'])
def deleteModel(model_id):
    deleteMe = Model.query.filter_by(id = model_id).one()
    if 'username' not in login_session or getCurrentUserID() != deleteMe.owner_id:
        flash("Unauthorized User")
        return redirect('/login')
    if request.method == 'POST':
        session.delete(deleteMe)
        session.commit()
        return redirect(url_for('showIndex', username = getuser()))
    return render_template('deleteModel.html', model = deleteMe,
                            username = getuser())

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token inside the credentials object is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return 'User ' + str(login_session['username'])

def createUser(login_session):
    newUser = Owner(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(Owner).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(Owner).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(Owner).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'POST')[0]
    print 'result is '
    print result
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'),
                                200)
        response.headers['Content-Type'] = 'application/json'
        print response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        print response
    return redirect(url_for('showIndex', username = getuser()))

def getuser():
    username = None
    if 'username' in login_session:
        username = login_session['username']
    return username

def getCurrentUserID():
    userID = None
    if 'gplus_id' in login_session:
        userID = login_session['user_id']
    return userID


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0')
