from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'recetas'

mysql = MySQL(app)

# Ruta principal
@app.route('/')
def inicio():
    return render_template('login.html')

# Registro
@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    usuario = request.form['txt_usuario']
    correo = request.form['txt_correo']
    password = generate_password_hash(request.form['txt_password'])

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (usuario, correo, password) VALUES (%s, %s, %s)", (usuario, correo, password))
    mysql.connection.commit()
    cur.close()

    return render_template('login.html', mensaje='Cuenta creada exitosamente')

# Login
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
        return redirect('/bienvenido')
    else:
        return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')

# Página protegida
@app.route('/bienvenido')
def bienvenido():
    if 'usuario' in session:
        return f"Bienvenido, {session['usuario']}!"
    else:
        return redirect('/')
    
if __name__ == '__main__':
    app.run(debug=True)
