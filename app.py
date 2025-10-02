from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename

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

# Configuración para upload de imágenes
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

mysql = MySQL(app)

# Asegurar que la carpeta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configurar las rutas manteniendo los nombres originales
# En app.py, modifica la ruta principal
@app.route('/')
def mostrar_presentacion():
    # Redirigir al login si no hay sesión activa
    if 'usuario' not in session:
        return redirect('/login')
    return func_presentacion()

# Agregar una nueva ruta para acceso sin login
@app.route('/acceso_publico')
def acceso_publico():
    # Establecer una sesión temporal para usuario público
    session['usuario_publico'] = True
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

# NUEVAS RUTAS PARA EL PERFIL DE USUARIO
@app.route('/perfil')
def perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    # Obtener datos básicos del usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
    usuario = cur.fetchone()
    cur.close()
    
    if not usuario:
        session.pop('usuario', None)
        return redirect('/login')
    
    # FUTURO: Obtener estadísticas cuando existan las tablas relacionadas
    # cur.execute("SELECT COUNT(*) as total_recetas FROM recetas WHERE usuario_id = %s", (usuario[0],))
    # stats_result = cur.fetchone()
    # total_recetas = stats_result[0] if stats_result else 0
    
    # Por ahora, datos de ejemplo para el frontend
    total_recetas = 0  # FUTURO: Reemplazar con consulta real
    total_likes = 0    # FUTURO: Reemplazar con consulta real
    favoritos_count = 0 # FUTURO: Reemplazar con consulta real
    
    return render_template('perfil.html', 
                         usuario=usuario, 
                         total_recetas=total_recetas,
                         total_likes=total_likes,
                         favoritos_count=favoritos_count)

@app.route('/editar_perfil')
def editar_perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
    usuario = cur.fetchone()
    cur.close()
    
    if not usuario:
        session.pop('usuario', None)
        return redirect('/login')
    
    return render_template('editar_perfil.html', usuario=usuario)

@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    nombre = request.form['nombre']
    email = request.form['email']
    
    cur = mysql.connection.cursor()
    
    # Verificar si el nuevo nombre de usuario ya existe (excluyendo el usuario actual)
    cur.execute("SELECT id FROM usuarios WHERE usuario = %s AND usuario != %s", (nombre, session['usuario']))
    if cur.fetchone():
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
        usuario_actual = cur.fetchone()
        cur.close()
        return render_template('editar_perfil.html', 
                             usuario=usuario_actual,
                             error="El nombre de usuario ya está en uso")
    
    # Actualizar datos básicos
    cur.execute("""
        UPDATE usuarios 
        SET usuario = %s, correo = %s 
        WHERE usuario = %s
    """, (nombre, email, session['usuario']))
    
    mysql.connection.commit()
    cur.close()
    
    # Actualizar la sesión con el nuevo nombre
    session['usuario'] = nombre
    
    return redirect('/perfil')

@app.route('/recetas_favoritas')
def recetas_favoritas():
    if 'usuario' not in session:
        return redirect('/login')
    
    # FUTURO: Implementar cuando exista la tabla favoritos
    # cur = mysql.connection.cursor()
    # cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    # usuario_id = cur.fetchone()
    # 
    # if not usuario_id:
    #     session.pop('usuario', None)
    #     return redirect('/login')
    # 
    # usuario_id = usuario_id[0]
    # 
    # # Verificar si existe la tabla favoritos
    # cur.execute("SHOW TABLES LIKE 'favoritos'")
    # if not cur.fetchone():
    #     cur.close()
    #     return render_template('recetas_favoritas.html', recetas=[])
    # 
    # # Obtener recetas favoritas del usuario
    # cur.execute("""
    #     SELECT r.* FROM recetas r
    #     JOIN favoritos f ON r.id = f.receta_id
    #     WHERE f.usuario_id = %s
    # """, (usuario_id,))
    # recetas_favoritas = cur.fetchall()
    # cur.close()
    
    # Por ahora, lista vacía para el frontend
    recetas_favoritas = []
    
    return render_template('recetas_favoritas.html', recetas=recetas_favoritas)

@app.route('/mis_recetas')
def mis_recetas():
    if 'usuario' not in session:
        return redirect('/login')
    
    # FUTURO: Implementar cuando exista la relación usuario-recetas
    # cur = mysql.connection.cursor()
    # cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    # usuario_id = cur.fetchone()
    # 
    # if not usuario_id:
    #     session.pop('usuario', None)
    #     return redirect('/login')
    # 
    # usuario_id = usuario_id[0]
    # 
    # # Obtener recetas creadas por el usuario
    # cur.execute("SELECT * FROM recetas WHERE usuario_id = %s", (usuario_id,))
    # mis_recetas = cur.fetchall()
    # cur.close()
    
    # Por ahora, lista vacía para el frontend
    mis_recetas = []
    
    return render_template('mis_recetas.html', recetas=mis_recetas)

# NUEVA RUTA: Panel de administración
@app.route('/admin')
def mostrar_admin():
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
    rutas_protegidas = ['/comunidad', '/perfil', '/editar_perfil', '/recetas_favoritas', '/mis_recetas']
    if request.path in rutas_protegidas and 'usuario' not in session:
        return redirect('/login')
    
    # Proteger ruta de admin
    if request.path == '/admin' and ('tipo_usuario' not in session or session['tipo_usuario'] != 'admin'):
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)