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
    mostrar_login as func_login,
    mostrar_comunidad as func_comunidad
)
from rutas_auth import (
    logout as func_logout,
    crear_cuenta as func_crear_cuenta,
    acceso_login as func_acceso_login
)
from rutas_recetas import (
    buscar_recetas_api as func_buscar_recetas_api,
    buscar_recetas_palabra_api as func_buscar_recetas_palabra_api,
    buscar_por_ingredientes_api as func_buscar_por_ingredientes_api
)
from rutas_michelin import (
    buscar_recetas_michelin as func_buscar_recetas_michelin,
    buscar_michelin_ingredientes as func_buscar_michelin_ingredientes,
    obtener_estadisticas as func_obtener_estadisticas
)

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

@app.route('/comunidad')
def mostrar_comunidad():
    return func_comunidad()

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

# NUEVA RUTA: Panel de administración
@app.route('/admin')
def mostrar_admin():
    # Verificar si el usuario es administrador
    if 'tipo_usuario' not in session or session['tipo_usuario'] != 'admin':
        return redirect('/login')
    return render_template('admin.html')

# RUTAS PARA RECETAS NORMALES
@app.route('/buscar_recetas')
def buscar_recetas_api():
    return func_buscar_recetas_api(mysql)

@app.route('/buscar_recetas_palabra')
def buscar_recetas_palabra_api():
    return func_buscar_recetas_palabra_api(mysql)

@app.route('/buscar_por_ingredientes')
def buscar_por_ingredientes():
    return func_buscar_por_ingredientes_api(mysql)

# RUTAS ESPECÍFICAS PARA MICHELIN
@app.route('/buscar_recetas_michelin')
def buscar_recetas_michelin():
    return func_buscar_recetas_michelin(mysql)

@app.route('/buscar_michelin_ingredientes')
def buscar_michelin_ingredientes():
    return func_buscar_michelin_ingredientes(mysql)

@app.route('/estadisticas')
def obtener_estadisticas():
    return func_obtener_estadisticas(mysql)

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template('500.html'), 500

# Middleware para verificar sesión en rutas protegidas
@app.before_request
def antes_de_peticion():
    rutas_protegidas = ['/comunidad', '/favoritos']
    if request.path in rutas_protegidas and 'usuario' not in session:
        return redirect('/login')
    
    # Proteger ruta de admin
    if request.path == '/admin' and ('tipo_usuario' not in session or session['tipo_usuario'] != 'admin'):
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)