from flask import Flask, request, flash, session, url_for, redirect, render_template
import time
from w1thermsensor import W1ThermSensor
import time
import board
import adafruit_dht

import serial
import sys
import serial
from time import sleep

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.output(26, True)
GPIO.output(17, True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hidro.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class waktu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String)
    later = db.Column(db.String)
    total = db.Column(db.Float)
    daya = db.Column(db.Float)
    
class suhu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    humi = db.Column(db.Float)
    value = db.Column(db.Float)
    temp_c = db.Column(db.Float)
    nutrisi = db.Column(db.Float)
    
db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/edit')
def edit():
    return render_template('edit.html')

@app.route('/editProses', methods=['POST'])
def edit_proses():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    
    if not user:
        flash('Email belum terdaftar')
        return redirect(url_for('register')) 

    num_rows_updated = User.query.filter_by(email=email).update(dict(password=password))
    db.session.commit()

    return redirect(url_for('login'))
    
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registerProses', methods=['POST'])
def proses_register():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() 

    if user: 
        flash('Email Sudah ada')
        return redirect(url_for('register'))

    new_user = User(email=email, name=name, password=password)

    
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route('/loginProses', methods=['POST'])
def proses_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    
    if (user.password != password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) 
    
    session['username'] = user.name
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/cahaya")
def rc_time():
    count=0
    GPIO.setup(27, GPIO.OUT)
    GPIO.output(27, GPIO.LOW)
    time.sleep(1)
    GPIO.setup(27, GPIO.IN)
    while (GPIO.input(27) == GPIO.LOW):
        count += 1
    return count

@app.route("/index")
def index():
    sensor = W1ThermSensor()
    dhtDevice = adafruit_dht.DHT22(board.D21, use_pulseio=False)
    
    global waktu
    data = waktu.query.all()
    first = []
    later = []
    total = []
    daya = []

    for amounts in data:
        first.append(amounts.first)
        later.append(amounts.later)
        total.append(amounts.total)
        daya.append(amounts.daya)
        
    global suhu
    data1 = suhu.query.all()
    suhuww = []
    humiww = []
    valueww = []
    nutrisiww = []
    
    for amounts in data1:
        suhuww.append(amounts.temp_c)
        humiww.append(amounts.humi)
        valueww.append(amounts.value)
        nutrisiww.append(amounts.nutrisi)

    while True:
        try:
            value = rc_time()
            valuep = round((value/10000)*100, 1)
            print(value)
            if (value > 10000):
                cahaya = 0
                GPIO.output(22, False)
            if (value < 10000):
                cahaya = 1
                GPIO.output(22, True)
                
            temp = sensor.get_temperature()
            temp_c = dhtDevice.temperature
            print(temp_c)
            temp_f = temp_c * (9 / 5) + 32
            humi = dhtDevice.humidity
            
            from nutrisi import nutrisi
            nutrisi = nutrisi()
            print(nutrisi)
            
            new_suhu = suhu(humi=humi, value=value, temp_c=temp_c, nutrisi=nutrisi)
            db.session.add(new_suhu)
            db.session.commit()
            
        except RuntimeError as error:
            print(error.args[0])
            time.sleep(5)
            continue
        
        return render_template('sensor3.html', suhuww=suhuww, humiww=humiww, valueww=valueww, nutrisiww=nutrisiww, temp=temp,temp_c=temp_c,humi=humi, nutrisi=nutrisi, data=data, first=first, later=later, total=total, daya=daya, cahaya=cahaya, value=value, status=GPIO.input(17))
    
@app.route("/motoron")
def motoron():
    GPIO.output(17, False)
    first_time = datetime.now()
    session['first'] = first_time
    return redirect(url_for('index'))

@app.route("/motoroff")
def motoroff():
    GPIO.output(17, True)
    
    first_time = session['first']
    later_time = datetime.now()
    later_time = later_time.replace(microsecond=0)
    
    first = str(first_time)
    later = str(later_time)
        
    tawal = (later_time.hour*3600)+(later_time.minute*60)+(later_time.second)
    takhir = (first_time.hour*3600)+(first_time.minute*60)+(first_time.second)
    time_diff = ((tawal - takhir)/3600)
    total = round(time_diff, 6)
    daya = round(17*total, 6)
    
    new_user = waktu(total=total, first=first, later=later, daya=daya)
    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route("/convert")
def convert():
    import sqlite3
    import csv

    con = sqlite3.connect('hidro.sqlite3')
    outfile = open('hidroponik.csv', 'w')
    outcsv = csv.writer(outfile)

    cursor = con.execute('select humi, value, temp_c from suhu')

    # dump column titles (optional)
    outcsv.writerow(x[0] for x in cursor.description)
    # dump rows
    outcsv.writerows(cursor.fetchall())

    outfile.close()
    return redirect(url_for('prediksi'))

@app.route("/prediksi")
def prediksi():
    sensor = W1ThermSensor()
    dhtDevice = adafruit_dht.DHT22(board.D21, use_pulseio=False)
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.flush()
    
    global waktu
    data = waktu.query.all()
    first = []
    later = []
    total = []
    daya = []

    for amounts in data:
        first.append(amounts.first)
        later.append(amounts.later)
        total.append(amounts.total)
        daya.append(amounts.daya)
        

    while True:
        try:
            value = rc_time()
            valuep = round((value/10000)*100, 1)
            print(value)
            if (value > 10000):
                cahaya = 0
                GPIO.output(22, False)
            if (value < 10000):
                cahaya = 1
                GPIO.output(22, True)
                
            temp = sensor.get_temperature()
            temp_c = dhtDevice.temperature
            print(temp_c)
            temp_f = temp_c * (9 / 5) + 32
            humi = dhtDevice.humidity
            
            from nutrisi import nutrisi
            nutrisi = nutrisi()
            print(nutrisi)
            
            new_suhu = suhu(humi=humi, value=value, temp_c=temp_c, nutrisi=nutrisi)
            db.session.add(new_suhu)
            db.session.commit()
            
        except RuntimeError as error:
            print(error.args[0])
            time.sleep(5)
            continue
        
        #import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import os
        import io
        import base64

        dataset = pd.read_csv('hidroponik.csv')
    
        x = dataset.iloc[:,[0,1]].values
        y = dataset.loc[:, 'temp_c'].values
        y = y.astype('int')
    
        from sklearn.model_selection import train_test_split
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=0)
    
        from sklearn.preprocessing import StandardScaler
        sc= StandardScaler()
        x_train = sc.fit_transform(x_train)
        x_test = sc.fit_transform(x_test)
    
        from sklearn.naive_bayes import GaussianNB
        classifier = GaussianNB()
        classifier.fit(x_train, y_train)
    
        y_pred = classifier.predict(x_test)
        y = y_pred[-1]
        print(y)
        #plt.plot(y_pred)
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        from matplotlib.figure import Figure
        
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        axis.set_title("")
        axis.set_xlabel("")
        axis.set_ylabel("")
        axis.grid()
        axis.plot(y_pred)

        pngImage = io.BytesIO()
        FigureCanvas(fig).print_png(pngImage)
    
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

        '''i = 'plot1'
        plt.savefig('static/dist/{}'.format(i))
        plt.close()'''
        
        return render_template('prediksi.html', image=pngImageB64String, y=y, temp=temp,temp_c=temp_c,humi=humi, nutrisi=nutrisi, data=data, first=first, later=later, total=total, daya=daya, cahaya=cahaya, value=value, status=GPIO.input(17))



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
