from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

DB_CONFIG = {
    "host": "localhost",
    "user": "moya_user", 
    "password": "moya123",
    "database": "recetas_db",
    "client_encoding": "UTF8"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

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

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
           
            cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
            existe = cur.fetchone()
            if existe:
                return render_template('login.html', mensaje_malo='Este correo ya está registrado')

            
            cur.execute(
                "INSERT INTO usuarios (usuario, correo, password) VALUES (%s, %s, %s) RETURNING id", 
                (usuario, correo, password)
            )
            conn.commit()
            
            return render_template('login.html', mensaje='Cuenta creada exitosamente')
            
    except Exception as e:
        print(f"❌ Error creando cuenta: {e}")
        return render_template('login.html', mensaje_malo='Error al crear la cuenta')
    finally:
        conn.close()

@app.route('/acceso_login', methods=['POST'])
def acceso_login():
    correo = request.form['txt_correo']
    password = request.form['txt_password']

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, usuario, password FROM usuarios WHERE correo = %s", (correo,))
            user = cur.fetchone()

        if user and check_password_hash(user[2], password):
            session['usuario'] = user[1]
            return redirect('/')
        else:
            return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return render_template('login.html', mensaje_malo='Error en el servidor')
    finally:
        conn.close()

@app.route('/buscar')
def buscar_recetas():
    return "Funcionalidad de búsqueda en desarrollo"

if __name__ == '__main__':
    app.run(debug=True, port=5005)