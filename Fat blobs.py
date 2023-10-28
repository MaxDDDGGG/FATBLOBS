from flask import Flask, render_template, request, redirect, flash, abort
import pandas as pd
from io import BytesIO
import base64
import matplotlib
from matplotlib.dates import WeekdayLocator, DateFormatter
import matplotlib.pyplot as plt
import seaborn as sns
import json
import numpy as np
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
matplotlib.use("Agg")

df = pd.DataFrame(columns=["Name", "Date", "Weight (kg)", "Height (cm)"])
app.secret_key = 'FlitFlobs24!'

@app.route('/')
def home():
    return render_template('home.html')
correct_passcode_hash = pbkdf2_sha256.hash('I AM A FAT BLOB!')

@app.route('/enter_passcode', methods=['GET', 'POST'])
def enter_passcode():
    if request.method == 'POST':
        entered_passcode = request.form.get('passcode')
        if pbkdf2_sha256.verify(entered_passcode, correct_passcode_hash):
            session['passcode_entered'] = True
            return redirect('/enter_passcode')
        else:
            flash('Incorrect passcode. Please try again.', 'error')
    return render_template('enter_passcode.html')

@app.route('/logout')
def logout():
    session.pop('passcode_entered', None)
    return redirect('/')

height_data = {}

@app.route('/Weight_input', methods=['POST', 'GET'])
def Weight_input():
    global df

    if request.method == 'POST':
        Name = request.form["Name"].strip().title()
        Date = request.form["Date"]
        Weight = float(request.form["Weight"])
        Height = int(request.form["Height"])

        new_data = {"Name": Name, "Date": Date, "Weight (kg)": Weight, "Height (cm)": Height}

        height_data[Name] = Height

        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv("data/Weight_data.csv", index=False)

        flash(f'Weight data for {Name} saved successfully!', 'success')

    return render_template('Weight_input.html')

@app.route('/save_Weight', methods=['POST'])
def save_Weight():
    if request.method == 'POST':
        Name = request.form["Name"]
        flash(f'Weight data for {Name} saved successfully!', 'success')
    return redirect('/Weight_input')

@app.route('/Progress')
def get_chart():
    data = pd.read_csv('data/Weight_data.csv')
    data['Date'] = pd.to_datetime(data['Date'])
    plt.figure(figsize=(15, 8))
    for name, data in data.groupby('Name'):
        plt.scatter(data['Date'], data['Weight (kg)'], label=name)
        x = matplotlib.dates.date2num(data['Date'])
        y = data['Weight (kg)']
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        plt.plot(data['Date'], p(x), linestyle='-')
        plt.xlabel('Date')
        plt.title("Progress", fontdict={'fontsize': 24,'fontweight':'bold', 'color': 'purple'})
        plt.ylabel('Weight (kg)')
        plt.grid(color = 'green', linestyle = '-')
        plt.legend()
        plt.gca().set_facecolor('lightblue')
        week_locator = WeekdayLocator(byweekday=0, interval=1) 
        week_formatter = DateFormatter('%d-%m-%Y')
        plt.gca().xaxis.set_major_formatter(DateFormatter)
        plt.gca().xaxis.set_major_locator(week_locator)
        plt.gca().xaxis.set_major_formatter(week_formatter)
        plt.xticks(rotation=20)
        plt.ylim(40, 100)
        plt.yticks(np.arange(40, 100, 5))
    

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    chart_data = base64.b64encode(buffer.read()).decode()
    plt.close()

    return render_template('Progress.html', chart_data=chart_data)

@app.route('/Biometrics', methods=['GET'])
def Biometrics():
    data = pd.read_csv('data/Weight_data.csv')  
    data['Date'] = pd.to_datetime(data['Date'])

    most_recent_data=data[data.groupby('Name')['Date'].transform(max)==data['Date']]
    most_recent_data['BMI'] = round(most_recent_data['Weight (kg)'] / ((most_recent_data['Height (cm)'] / 100) ** 2), 0)
    most_recent_data['Target Weight']=round(21.7*((most_recent_data['Height (cm)']/100)**2),1)
    data_list = most_recent_data.to_dict(orient='records')
    return render_template('Biometrics.html', most_recent_data=data_list)

if __name__ == '__main__':
    app.run(debug=True)
