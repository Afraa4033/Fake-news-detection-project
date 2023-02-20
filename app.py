from flask import Flask, request, redirect, render_template, url_for, flash,session
from flask_mysqldb import MySQL
import datetime
import pickle

vector = pickle.load(open("vectorizer.pkl", 'rb'))
model = pickle.load(open("finalized_model.pkl", 'rb'))



app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'news'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template("home_page.html")

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":
        news_headline = str(request.form['news'])
        prediction = model.predict(vector.transform([news_headline]))[0]

        # Insert news into database
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H:%M:%S")
        text = request.form['news']
        result = prediction

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO newsin ( date, time, text, result) VALUES ( %s, %s, %s, %s)", ( date, time,  text, result))
        mysql.connection.commit()
        news_id = cur.lastrowid

        # Insert user into the users table
        cur.execute("INSERT INTO user VALUES ()")
        mysql.connection.commit()
        user_id = cur.lastrowid

        # Link user to news in the user_news table
        query = "INSERT INTO user_news (user_id, news_id) VALUES (%s, %s)"
        cur.execute(query, (user_id, news_id))
        mysql.connection.commit()
        
        return render_template("home_page.html", prediction_text="News headline is -> {}".format(prediction), text=text)

    else:
        return render_template("home_page.html")



@app.route('/Admin login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        passw = request.form['pass']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE email='" + user + "' AND password='" + passw + "'")
        rows = cur.fetchall()
        if rows and len(rows) == 1:
            session['user'] = user
            return redirect('/Admin Home')
        else:
            return render_template('Admin login.html', error=True)
    return render_template('Admin login.html')


@app.route('/admin_page')
def admin_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admin")
    data = cur.fetchall()
    cur.close()

    return render_template('admin_page.html', admin=data)

@app.route('/insert', methods = ['POST'])
def insert():
    if request.method == "POST":
        flash("Data Inserted Successfully")
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        return redirect(url_for('admin_page'))

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM admin WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('admin_page'))


@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email']
        passw = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE admin
               SET name=%s, email=%s, password=%s
               WHERE id=%s
            """, (name, email, passw, id_data))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('admin_page'))


@app.route("/Admin Home")
def admin_home():
    if 'user' not in session:
        return redirect('/Admin login')
    if 'logout' in request.args:
        session.pop('user', None)
        return redirect('/Admin login')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM newsin")
    rows = cur.fetchall()
    return render_template('Admin Home.html', rows=rows, user=session['user'])


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
