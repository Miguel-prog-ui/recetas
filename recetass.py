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

# Función para cargar recetas desde la tabla recetass
def cargar_recetas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT title, url, ingredients, steps, uuid FROM recetass")
    columnas = [desc[0] for desc in cur.description]
    recetas = [dict(zip(columnas, fila)) for fila in cur.fetchall()]
    cur.close()
    return recetas

# Página principal: login y registro
@app.route('/')
def inicio():
    return render_template('login.html')

# Registro de usuario
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

# Login de usuario
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
        return redirect('/recetas')
    else:
        return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')

# Página de recetas (protegida)
@app.route('/recetas', methods=['GET', 'POST'])
def mostrar_recetas():
    if 'usuario' not in session:
        return redirect('/')

    recetas = []
    ingredientes = ''
    if request.method == 'POST':
        ingredientes = request.form.get('ingredientes', '').lower()
        lista_ingredientes = [i.strip() for i in ingredientes.split(',') if i.strip()]
        todas = cargar_recetas()
        recetas = [
            r for r in todas
            if all(ing in r['ingredients'].lower() for ing in lista_ingredientes)
        ]
    return render_template('recetas.html', recetas=recetas, ingredientes=ingredientes, usuario=session['usuario'])

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
