from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'recetas'

mysql = MySQL(app)

@app.route('/')
def mostrar_presentacion():
    return render_template('presentacion.html')

@app.route('/bebidas')
def mostrar_bebidas():
    return render_template('bebidas.html')

@app.route('/bebidas_alcoholicas')
def mostrar_bebidas_alcoholicas():
    return render_template('bebidas_alcoholicas.html')

@app.route('/postres')
def mostrar_postres():
    return render_template('postres.html')

@app.route('/comidas')
def mostrar_comidas():
    return render_template('comidas.html')

@app.route('/alta_cocina')
def mostrar_alta_cocina():
    return render_template('alta_cocina.html')

@app.route('/login')
def mostrar_login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')

@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    usuario = request.form['txt_usuario']
    correo = request.form['txt_correo']
    password = generate_password_hash(request.form['txt_password'])

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
    existe = cur.fetchone()
    if existe:
        return render_template('login.html', mensaje_malo='Este correo ya está registrado')

    cur.execute("INSERT INTO usuarios (usuario, correo, password) VALUES (%s, %s, %s)", (usuario, correo, password))
    mysql.connection.commit()
    cur.close()

    return render_template('login.html', mensaje='Cuenta creada exitosamente')

@app.route('/acceso_login', methods=['POST'])
def acceso_login():
    correo = request.form['txt_correo']
    password = request.form['txt_password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, password FROM usuarios WHERE correo = %s", (correo,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        session['usuario'] = user[1]
        return redirect('/')
    else:
        return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')

@app.route('/buscar')
def buscar_recetas():
    return "Funcionalidad de búsqueda en desarrollo"

if __name__ == '__main__':
    app.run(debug=True)