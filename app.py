from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL

# Importar las funciones desde otros archivos
from rutas_simples import (
    mostrar_presentacion as func_presentacion,
    mostrar_bebidas as func_bebidas,
    mostrar_bebidas_alcoholicas as func_bebidas_alcoholicas,
    mostrar_postres as func_postres,
    mostrar_comidas as func_comidas,
    mostrar_alta_cocina as func_alta_cocina,
    mostrar_login as func_login
)
from rutas_auth import (
    logout as func_logout,
    crear_cuenta as func_crear_cuenta,
    acceso_login as func_acceso_login
)
from rutas_recetas import buscar_recetas_api as func_buscar_recetas_api
from rutas_recetas import buscar_recetas_palabra_api as func_buscar_recetas_palabra_api
from rutas_recetas import buscar_por_ingredientes_api


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'recetas'

mysql = MySQL(app)

# Configurar las rutas manteniendo los nombres originales
@app.route('/')
def mostrar_presentacion():
    return func_presentacion()

@app.route('/bebidas')
def mostrar_bebidas():
    return func_bebidas()

@app.route('/bebidas_alcoholicas')
def mostrar_bebidas_alcoholicas():
    return func_bebidas_alcoholicas()

@app.route('/postres')
def mostrar_postres():
    return func_postres()

@app.route('/comidas')
def mostrar_comidas():
    return func_comidas()

@app.route('/alta_cocina')
def mostrar_alta_cocina():
    return func_alta_cocina()

@app.route('/login')
def mostrar_login():
    return func_login()

@app.route('/logout')
def logout():
    return func_logout()

@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    return func_crear_cuenta(mysql)

@app.route('/acceso_login', methods=['POST'])
def acceso_login():
    return func_acceso_login(mysql)

@app.route('/buscar_recetas')
def buscar_recetas_api():
    return func_buscar_recetas_api(mysql)



# ... después de las otras rutas ...

@app.route('/buscar_recetas_palabra')
def buscar_recetas_palabra_api():
    return func_buscar_recetas_palabra_api(mysql)


# ... (código existente) ...

@app.route('/buscar_por_ingredientes')
def buscar_por_ingredientes():
    return buscar_por_ingredientes_api(mysql)

if __name__ == '__main__':
    app.run(debug=True)