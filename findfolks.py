# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 22:22:51 2016

@author: Jessica
"""
#import flask library
import flask 
import pymysql.cursors

#initialize the app from flask
app = flask.Flask(__name__)

#configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='findfolks',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
                       
#define route to home function                    
@app.route('/')
def index():
    
    if ('error' in flask.session):
      error = flask.session['error']
      flask.session.pop('error')
    else:
      error = None
    #cursor used to send queries
    cursor = conn.cursor()
    query = 'SELECT title, description, start_time, end_time, location_name, zipcode FROM `an_event` WHERE start_time <= DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 3 DAY) AND start_time >= CURRENT_TIMESTAMP ORDER BY an_event.start_time ASC'
    cursor.execute(query)
    eventData = cursor.fetchall()

    interests = 'SELECT * FROM interest'
    cursor.execute(interests)
    interestData = cursor.fetchall()
    cursor.close()
    return flask.render_template('index.html', events = eventData, interests = interestData, error = error)

@app.route('/register')
def register():
    return flask.render_template('register.html')
    
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    firstName = flask.request.form['firstName']
    lastName = flask.request.form['lastName']
    email = flask.request.form['email']
    zipcode = flask.request.form['zipcode']
    username = flask.request.form['username']
    password = flask.request.form['password']

    cursor = conn.cursor()
    
    query = 'SELECT * FROM member WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    error = None
    if(data):
      error = "This user already exists"
      return flask.render_template('register.html', error = error)
    else:
      ins = 'INSERT INTO member VALUES(%s, md5(%s), %s, %s, %s, %s)'
      cursor.execute(ins, (username, password, firstName, lastName, email, zipcode))
      conn.commit()
      cursor.close()
      flask.session['username'] = username
      return flask.redirect(flask.url_for('home'))
@app.route('/login')
def login():
  return flask.render_template('login.html')

@app.route('/loginAuth', methods = ['GET', 'POST'])
def loginAuth():
  username = flask.request.form['username']
  password = flask.request.form['password']
  
  cursor = conn.cursor()
  
  query = 'SELECT * FROM member WHERE username = %s and password = md5(%s)'
  cursor.execute(query, (username, password))

  data = cursor.fetchone()

  cursor.close()
  error = None
  if(data):
    flask.session['username'] = username
    return flask.redirect(flask.url_for('home'))
  else:
    error = 'Invalid login or username'
    return flask.render_template('login.html', error = error)
@app.route('/interest', methods = ['GET', 'POST'])
def interest():
    interest = flask.request.form['interest']
    interest = interest.split(', ')
    category = interest[0]
    keyword = interest[1]
    cursor = conn.cursor()
    query = 'SELECT group_name, description FROM about NATURAL JOIN a_group WHERE category = %s AND keyword = %s'
    cursor.execute(query, (category, keyword))
    groups = cursor.fetchall()
    cursor.close()
    error = None
    if(groups):
      return flask.render_template('interest.html', groups = groups)
    else:
      error = "No groups with your interest, choose again!"
      flask.session['error']= error
      return flask.redirect(flask.url_for('index'))
@app.route('/home')
def home():
  username = flask.session['username']
  return flask.render_template('home.html', username = username)

@app.route('/logout')
def logout():
  flask.session.pop('username')
  return flask.redirect('/login')

@app.route('/upcomingEvents', methods = ['GET', 'POST'])
def upcomingEvents():
  username = flask.session['username']
  cursor = conn.cursor()
  threeDay = 'SELECT title, description, start_time, end_time, location_name, zipcode FROM sign_up NATURAL JOIN an_event WHERE username = %s AND start_time >= DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY) AND start_time <= DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY)  ORDER BY an_event.start_time ASC'
  cursor.execute(threeDay,(username))
  threeDayEvents = cursor.fetchall()
  currentDay = 'SELECT title, description, start_time, end_time, location_name, zipcode FROM sign_up NATURAL JOIN an_event WHERE username = %s AND DATE(start_time) = CURRENT_DATE() ORDER BY an_event.start_time ASC'
  cursor.execute(currentDay, (username))
  currentDayEvents = cursor.fetchall()
  cursor.close()
  return flask.render_template('upcomingEvents.html', threeDayEvents = threeDayEvents, currentDayEvents = currentDayEvents)

@app.route('/signup', methods = ['GET', 'POST'])
def signUp():
  username = flask.session['username']
  event = flask.request.form['event']
  cursor = conn.cursor()
  query = 'INSERT INTO sign_up (event_id, username) VALUES (%s, %s)'
  cursor.execute(query, (event, username))
  conn.commit()
  cursor.close()
  success = "You have signed up for this event!"
  flask.session['success'] = success
  return flask.redirect(flask.url_for('search', success = success))

@app.route('/search', methods = ['GET', 'POST'])
def search():
  if('success' in flask.session):
  	success = flask.session['success']
  	flask.session.pop('success')
  else:
  	success = None
  username = flask.session['username']
  cursor = conn.cursor()
  query = 'SELECT * FROM about NATURAL JOIN organize NATURAL JOIN an_event WHERE (category, keyword) IN (SELECT category, keyword FROM interested_in WHERE username = %s) AND event_id NOT IN (SELECT event_id FROM sign_up WHERE username = %s)'
  cursor.execute(query, (username, username))
  events = cursor.fetchall()
  cursor.close()
  return flask.render_template('search.html', events = events, success =success)

@app.route('/createEvent', methods = ['GET', 'POST'])
def createEvent():
  if('success' in flask.session):
    success = flask.session['success']
    flask.session.pop('success')
  else:
    success = None
  username = flask.session['username']
  cursor = conn.cursor()
  query = 'SELECT * FROM belongs_to NATURAL JOIN a_group WHERE username = %s AND authorized = 1'
  cursor.execute(query, (username))
  groups = cursor.fetchall()
  cursor.close()
  return flask.render_template('createEvent.html', groups = groups, success = success)
@app.route('/createEventForm', methods = ['GET', 'POST'])
def createEventForm():
  group_id = flask.request.form['group']
  flask.session['group'] = group_id
  return flask.render_template('createEventForm.html')
@app.route('/createEventAuth', methods = ['GET', 'POST'])
def createEventAuth():
  group_id = flask.session['group']
  username = flask.session['username']
  title = flask.request.form['title']
  description = flask.request.form['description']
  start_time = flask.request.form['start_time']
  end_time = flask.request.form['end_time']
  location_name = flask.request.form['location_name']
  zipcode = flask.request.form['zipcode']
  cursor = conn.cursor()
  query = 'INSERT INTO an_event (title, description, start_time, end_time, location_name, zipcode) VALUES (%s, %s, %s, %s, %s, %s)'
  cursor.execute(query, (title, description, start_time, end_time, location_name, zipcode))
  last_id = cursor.lastrowid
  insertOrganize = 'INSERT INTO organize (event_id, group_id) VALUES (%s, %s)'
  cursor.execute(insertOrganize, (last_id, group_id))
  insertSignUp = 'INSERT INTO sign_up (event_id, username) VALUES (%s, %s)'
  cursor.execute(insertSignUp, (last_id, username))
  conn.commit()
  cursor.close()
  flask.session.pop('group')
  flask.session['success'] = "Successfully created the event!"
  return flask.redirect(flask.url_for('createEvent'))

@app.route('/rateEvent', methods = ['GET', 'POST'])
def rateEvent():
  username = flask.session['username']
  cursor = conn.cursor()
  revents = 'SELECT * FROM an_event'
  cursor.execute(revents)
  rateEventsData = cursor.fetchall()
  cursor.close()
  error = None
  return flask.render_template('rateEvent.html', events = rateEventsData)

@app.route('/submitRating', methods = ['GET', 'POST'])
def submitRating():
  event = flask.request.form['event']
  event = event.split(" ")
  event_id = event[0]
  rating = flask.request.form.getlist('rating')
  username = flask.session.get('username')
  cursor = conn.cursor()
  eventID = 'SELECT * FROM an_event NATURAL JOIN sign_up WHERE username = %s AND event_id = %s AND start_time <= CURDATE()'
  cursor.execute(eventID,(username, event_id))
  eventsIDData = cursor.fetchall()
  error = None
  if (eventsIDData):
    ins = 'UPDATE `sign_up` SET `rating` =%s WHERE `event_id` = %s AND `username` = %s'
    cursor.execute(ins, (rating,event_id,username))
    conn.commit()
    cursor.close()
    return flask.render_template('submitRating.html')
  else:
    error = "Sorry, you can't rate this event because it either hasn't happened yet or you haven't signed up for it!"
    flask.session['error']= error
    return flask.render_template('rateError.html', error=error)

@app.route('/averageRatings', methods = ['GET', 'POST'])
def averageRatings(): 
  username = flask.session.get('username')
  cursor = conn.cursor()
  rate = 'SELECT title, group_id, AVG(rating) as rate FROM sign_up NATURAL JOIN an_event as e NATURAL JOIN organize WHERE group_id IN (SELECT group_id FROM belongs_to WHERE username = %s) AND start_time >= DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY) AND start_time < CURRENT_DATE GROUP BY e.event_id'
  cursor.execute(rate, (username))
  ratings = cursor.fetchall()
  cursor.close()
  error = None
  return flask.render_template('averageRatings.html', rates = ratings)

@app.route('/friendsEvent', methods = ['GET', 'POST'])
def friendsEvent():
  username = flask.session.get('username')
  cursor = conn.cursor()
  frEvents = 'SELECT event_id, title, username FROM sign_up NATURAL JOIN an_event WHERE username IN (SELECT friend_of FROM friend WHERE friend_to = %s)'
  cursor.execute(frEvents, username)
  friendEventsData = cursor.fetchall()
  cursor.close()
  error = None
  if (friendEventsData):
    return flask.render_template('friendsEvent.html', friend = friendEventsData)
  else:
    error = "Sorry, we couldn't find any of your friends who are signed up for events!"
    flask.session['error']= error
    return flask.render_template('friendsEvent.html', error = error)

@app.route('/postInEvent', methods = ['GET', 'POST'])
def postInEvent():
  username = flask.session.get('username')
  cursor = conn.cursor()
  pevent = 'SELECT * FROM an_event NATURAL JOIN sign_up WHERE username = %s'
  cursor.execute(pevent,username)
  eventData = cursor.fetchall()
  cursor.close()
  error = None
  return flask.render_template('postInEvent.html', events = eventData)

@app.route('/eventPosted', methods = ['GET', 'POST'])
def eventPosted():
  username = flask.session.get('username')
  post = flask.request.form['post']
  event = flask.request.form['event']
  event = event.split(" ")
  event_id = event[0]
  cursor = conn.cursor()
  posts = 'INSERT INTO post_in (event_id,username,post) VALUES (%s,%s,%s)'
  cursor.execute(posts,(event_id,username,post))
  conn.commit()
  cursor.close()
  error = None
  return flask.render_template('eventPosted.html')

@app.route('/makeFriends', methods = ['GET', 'POST'])
def makeFriends():
  cursor = conn.cursor()
  query = 'SELECT username from member where zipcode = (Select zipcode from member where username = %s) and username != %s and username not in (Select friend_to from friend where friend_of = %s)'
  username = flask.session['username']
  cursor.execute(query, (username, username, username))
  listOfmembers = cursor.fetchall()
  cursor.close()
  return flask.render_template('makeFriends.html', listOfmembers = listOfmembers)
@app.route('/makeFriendsAuth', methods = ['GET', 'POST'])
def makeFriendsAuth(): 
  friendName = flask.request.form['friend_name']
  username = flask.session["username"]
  cursor = conn.cursor()
  query = 'INSERT INTO friend (friend_of, friend_to) VALUES (%s, %s )'
  cursor.execute(query, (username, friendName))
  conn.commit()
  return flask.render_template('makeFriendsAuth.html')

@app.route('/joinGroup', methods = ['GET', 'POST'])
def joinGroup():
  cursor = conn.cursor() 
  queryListGroups = 'SELECT DISTINCT group_id, group_name, description, creator FROM belongs_to NATURAL JOIN a_group WHERE group_id NOT IN (SELECT group_id FROM belongs_to WHERE username = %s)'
  username = flask.session["username"]
  cursor.execute(queryListGroups, username)
  listOfGroups = cursor.fetchall()
  cursor.close()
  return flask.render_template('joinGroups.html', groups = listOfGroups)
 
@app.route('/populateBelongsTo', methods = ['GET', 'POST'])
def populateBelongsTo(): 
  group_id = flask.request.form['group_id']
  authorized = 0
  username = flask.session["username"]
  cursor = conn.cursor()
  belongsToQuery = 'INSERT INTO belongs_to (group_id, username, authorized) VALUES (%s, %s, %s)'
  cursor.execute(belongsToQuery, (group_id, username, authorized))
  conn.commit()
  cursor.close()
  return flask.render_template('populateBelongsTo.html', group_id = group_id)

@app.route('/createGroup', methods = ['GET', 'POST'])
def createGroup():
  return flask.render_template('createGroup.html')

@app.route('/createGroupAuth', methods = ['GET', 'POST'])
def createGroupAuth(): 
  group_name = flask.request.form['group_name']
  desc = flask.request.form['description']
  username = flask.session['username']
  cursor = conn.cursor() 
  insertGroupQuery = 'INSERT INTO a_group (group_name, description, creator) VALUES (%s, %s, %s) '
  cursor.execute(insertGroupQuery, (group_name, desc, username))  
  changeAuthorization = 'INSERT INTO belongs_to (group_id, username, authorized) VALUES (last_insert_id(), %s, %s)'
  cursor.execute(changeAuthorization, (username, 1))
  conn.commit()
  cursor.close()
  return flask.render_template('createGroupSuccess.html')

@app.route('/grantAccess', methods = ['GET', 'POST'])
def grantAccess():
  username = flask.session['username']
  listGroupsQuery = 'SELECT distinct group_id, group_name FROM a_group NATURAL JOIN belongs_to where username = %s and authorized = %s'
  cursor = conn.cursor()
  cursor.execute(listGroupsQuery, (username, 1))
  listOfGroups = cursor.fetchall()
  return flask.render_template('grantAccess.html', groups = listOfGroups)

@app.route('/grantAccessAuth', methods = ['GET', 'POST'])
def grantAccessAuth(): 
  group_id = flask.request.form['group_id']
  flask.session['group_id'] = group_id
  showMemberQuery = 'SELECT firstname, lastname, username FROM member NATURAL JOIN belongs_to where belongs_to.group_id = %s and authorized != %s'
  cursor= conn.cursor()
  cursor.execute(showMemberQuery, (group_id, 1))
  listOfmembers = cursor.fetchall()
  cursor.close()
  return flask.render_template('grantAccessMembers.html', members = listOfmembers)

@app.route('/changeAccess', methods = ['GET', 'POST'])
def changeAccess(): 
  memberInfo = flask.request.form['memberInfo']
  group_id = flask.session['group_id']
  changeAuth = 'UPDATE belongs_to SET authorized = %s WHERE  belongs_to.username = %s and belongs_to.group_id = %s'
  cursor = conn.cursor()
  cursor.execute(changeAuth, (1, memberInfo, group_id))
  conn.commit()
  return flask.render_template('grantAccessSuccess.html')


app.secret_key = 'SECRETOFTHESECRETKEY'
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)

