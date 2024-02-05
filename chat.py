#!/bin/env python
import time
from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from sqlalchemy import Column, String, Integer, BLOB

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
socketio = SocketIO()
db = SQLAlchemy(app)
socketio.init_app(app)

class MessagesModel(db.Model):
    id = Column(Integer, primary_key=True)
    msg = Column(String)

class TrackingModel(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    headers = Column(String)
    ip = Column(String)
    time = Column(Integer)

class LoginForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Chat')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        db.session.add(TrackingModel(name=session['name'], headers=str(request.headers), ip=request.remote_addr, time=time.time()))
        db.session.commit()
        return redirect(url_for('.chat'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
    return render_template('index.html', form=form)


@app.route('/chat')
def chat():
    messages = MessagesModel.query.limit(100).all()
    name = session.get('name', '')
    if name == '':
        return redirect(url_for('.index'))
    return render_template('chat.html', name=name, messages=messages)

@socketio.on('joined', namespace='/chat')
def joined(message):
    join_room("msgs")

@socketio.on('text', namespace='/chat')
def text(message):
    if not message["msg"]:
        return
    msg = session.get('name') + ': ' + message['msg']
    emit('message', {'msg': msg}, room="msgs")
    print(f"{session.get('name')}: {message['msg']}")
    db.session.add(MessagesModel(msg=msg))
    db.session.commit()

@socketio.on('left', namespace='/chat')
def left(message):
    leave_room("msgs")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app)
