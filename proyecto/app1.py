from flask import Flask, render_template, request, session, jsonify, redirect
import psycopg2

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
from rutas_recetas import buscar_recetas_api as func_buscar_recetas_api
from rutas_recetas import buscar_recetas_palabra_api as func_buscar_recetas_palabra_api
from rutas_recetas import buscar_por_ingredientes_api

from rutas_michelin import (
    buscar_recetas_michelin as func_buscar_recetas_michelin,
    buscar_michelin_ingredientes as func_buscar_michelin_ingredientes,
    obtener_estadisticas as func_obtener_estadisticas
)


from likes_controller import (
    dar_like, quitar_like, toggle_like, verificar_usuario_likeo, 
    obtener_likes_receta, obtener_recetas_populares,obtener_recetas_con_like
)


import uuid
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'


app.config['UPLOAD_FOLDER'] = 'static/imagenes_recetas'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


DB_CONFIG = {
    "host": "localhost",
    "user": "moya_user", 
    "password": "moya123",
    "database": "recetas_db",
    "client_encoding": "UTF8"
}

def get_db_connection():
    """Función de conexión a PostgreSQL"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

def crear_tabla_usuarios():
    """Crea la tabla de usuarios si no existe"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    usuario TEXT NOT NULL,
                    correo TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("✅ Tabla 'usuarios' creada/verificada")
    except Exception as e:
        print(f"❌ Error creando tabla usuarios: {e}")
    finally:
        conn.close()

def verificar_tabla_recetas_usuarios():
    """Verifica que la tabla recetas_usuarios existe y tiene las columnas necesarias"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
        
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'recetas_usuarios'
                );
            """)
            tabla_existe = cur.fetchone()[0]
            
            if tabla_existe:
                print("✅ Tabla 'recetas_usuarios' existe")
                
            
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'recetas_usuarios' AND column_name = 'categoria'
                """)
                if not cur.fetchone():
                    try:
                        cur.execute("ALTER TABLE recetas_usuarios ADD COLUMN categoria TEXT")
                        conn.commit()
                        print("✅ Columna 'categoria' agregada a la tabla")
                    except Exception as e:
                        print(f"⚠️ No se pudo agregar columna categoria: {e}")
            else:
                print("⚠️ Tabla 'recetas_usuarios' no existe")
    except Exception as e:
        print(f"❌ Error verificando tabla recetas_usuarios: {e}")
    finally:
        conn.close()

def verificar_tabla_michelin():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'michelin'
);
            """)
            tabla_existe = cur.fetchone()[0]
            
            if tabla_existe:
                print("✅ Tabla 'michelin' existe")
            else:
                print("⚠️ Tabla 'michelin' NO existe - necesitas crearla")
                
    except Exception as e:
        print(f"❌ Error verificando tabla michelin: {e}")
    finally:
        conn.close()


crear_tabla_usuarios()
verificar_tabla_recetas_usuarios()


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
@app.route('/admin')

def mostrar_admin():
    if 'tipo_usuario' not in session or session['tipo_usuario'] != 'admin':
        return redirect('/login')
    return render_template('admin.html')

@app.route('/login')
def mostrar_login():
    return func_login()

@app.route('/logout')
def logout():
    return func_logout()

@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
   
    return func_crear_cuenta()

@app.route('/acceso_login', methods=['POST'])
def acceso_login():

    return func_acceso_login()

# NUEVAS RUTAS PARA EL PERFIL DE USUARIO
@app.route('/perfil')
def perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    # Obtener datos básicos del usuario
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
            usuario = cur.fetchone()
        
        if not usuario:
            session.pop('usuario', None)
            return redirect('/login')
        
        # FUTURO: Obtener estadísticas cuando existan las tablas relacionadas
        # with conn.cursor() as cur:
        #     cur.execute("SELECT COUNT(*) as total_recetas FROM recetas WHERE usuario_id = %s", (usuario[0],))
        #     stats_result = cur.fetchone()
        #     total_recetas = stats_result[0] if stats_result else 0
        
        # Por ahora, datos de ejemplo para el frontend
        total_recetas = 0  # FUTURO: Reemplazar con consulta real
        total_likes = 0    # FUTURO: Reemplazar con consulta real
        favoritos_count = 0 # FUTURO: Reemplazar con consulta real
        
        return render_template('perfil.html', 
                             usuario=usuario, 
                             total_recetas=total_recetas,
                             total_likes=total_likes,
                             favoritos_count=favoritos_count)
    finally:
        conn.close()

@app.route('/editar_perfil')
def editar_perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
            usuario = cur.fetchone()
        
        if not usuario:
            session.pop('usuario', None)
            return redirect('/login')
        
        return render_template('editar_perfil.html', usuario=usuario)
    finally:
        conn.close()

@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'usuario' not in session:
        return redirect('/login')
    
    nombre = request.form['nombre']
    email = request.form['email']
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si el nuevo nombre de usuario ya existe (excluyendo el usuario actual)
            cur.execute("SELECT id FROM usuarios WHERE usuario = %s AND usuario != %s", (nombre, session['usuario']))
            if cur.fetchone():
                # Obtener datos actuales del usuario para mostrar en el formulario
                cur.execute("SELECT id, usuario, correo, tipo FROM usuarios WHERE usuario = %s", (session['usuario'],))
                usuario_actual = cur.fetchone()
                return render_template('editar_perfil.html', 
                                     usuario=usuario_actual,
                                     error="El nombre de usuario ya está en uso")
            
            # Actualizar datos básicos
            cur.execute("""
                UPDATE usuarios 
                SET usuario = %s, correo = %s 
                WHERE usuario = %s
            """, (nombre, email, session['usuario']))
            
            conn.commit()
        
        # Actualizar la sesión con el nuevo nombre
        session['usuario'] = nombre
        
        return redirect('/perfil')
    finally:
        conn.close()

@app.route('/recetas_favoritas')
def recetas_favoritas():
    if 'usuario' not in session:
        return redirect('/login')
    
    # FUTURO: Implementar cuando exista la tabla favoritos
    # conn = get_db_connection()
    # try:
    #     with conn.cursor() as cur:
    #         cur.execute("SELECT id FROM usuarios WHERE usuario = %s", (session['usuario'],))
    #         usuario_id = cur.fetchone()
    #     
    #     if not usuario_id:
    #         session.pop('usuario', None)
    #         return redirect('/login')
    #     
    #     usuario_id = usuario_id[0]
    #     
    #     # Verificar si existe la tabla favoritos
    #     cur.execute("""
    #         SELECT EXISTS (
    #             SELECT FROM information_schema.tables 
    #             WHERE table_schema = 'public' 
    #             AND table_name = 'favoritos'
    #         )
    #     """)
    #     tabla_existe = cur.fetchone()[0]
    #     
    #     if not tabla_existe:
    #         return render_template('recetas_favoritas.html', recetas=[])
    #     
    #     # Obtener recetas favoritas del usuario
    #     cur.execute("""
    #         SELECT r.* FROM recetas r
    #         JOIN favoritos f ON r.id = f.receta_id
    #         WHERE f.usuario_id = %s
    #     """, (usuario_id,))
    #     recetas_favoritas = cur.fetchall()
    #     
    #     return render_template('recetas_favoritas.html', recetas=recetas_favoritas)
    # finally:
    #     conn.close()
    
    # Por ahora, lista vacía para el frontend
    recetas_favoritas = []
    
    return render_template('recetas_favoritas.html', recetas=recetas_favoritas)

@app.route('/mis_recetas')
def mis_recetas():
    if 'usuario' not in session:
        return redirect('/login')
    
    print(f"🔍 Buscando recetas para usuario: {session['usuario']}")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si la columna 'usuario' existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'recetas_usuarios' AND column_name = 'usuario'
            """)
            columna_existe = cur.fetchone()
            
            if not columna_existe:
                print("❌ Columna 'usuario' no existe en recetas_usuarios")
                cur.execute("ALTER TABLE recetas_usuarios ADD COLUMN usuario TEXT")
                conn.commit()
                print("✅ Columna 'usuario' agregada a recetas_usuarios")
                return render_template('mis_recetas.html', recetas=[])
            
            # Verificar cuántas recetas tiene este usuario
            cur.execute("SELECT COUNT(*) FROM recetas_usuarios WHERE usuario = %s", (session['usuario'],))
            count_result = cur.fetchone()
            print(f"📊 Recetas encontradas para {session['usuario']}: {count_result[0]}")
            
            # Verificar algunas recetas de ejemplo
            cur.execute("SELECT id, title, usuario FROM recetas_usuarios WHERE usuario IS NOT NULL LIMIT 5")
            ejemplo_recetas = cur.fetchall()
            print(f"📋 Ejemplo de recetas en la BD: {ejemplo_recetas}")
            
            # Obtener recetas del usuario actual
            cur.execute("""
                SELECT 
                    id,
                    title,
                    ingredients,
                    steps,
                    COALESCE(categoria, 'Comunidad') as categoria,
                    imagen_filename,
                    url,
                    TO_CHAR(COALESCE(fecha_creacion, CURRENT_TIMESTAMP), 'DD/MM/YYYY') as fecha,
                    (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = recetas_usuarios.id) as likes_count
                FROM recetas_usuarios 
                WHERE usuario = %s 
                ORDER BY COALESCE(fecha_creacion, CURRENT_TIMESTAMP) DESC
            """, (session['usuario'],))
            
            mis_recetas = cur.fetchall()
            print(f"✅ Recetas procesadas: {len(mis_recetas)}")
            
            # Debug detallado de cada receta
            for i, receta in enumerate(mis_recetas):
                print(f"  📝 Receta {i+1}:")
                print(f"     ID: {receta[0]}")
                print(f"     Título: {receta[1]}")
                print(f"     Categoría: {receta[4]}")
                print(f"     Imagen: {receta[5]}")
                print(f"     Likes: {receta[8]}")
                print(f"     Fecha: {receta[7]}")
            
            return render_template('mis_recetas.html', recetas=mis_recetas)
            
    except Exception as e:
        print(f"❌ Error obteniendo mis recetas: {e}")
        import traceback
        traceback.print_exc()
        return render_template('mis_recetas.html', recetas=[])
    finally:
        conn.close()

@app.route('/buscar_recetas')
def buscar_recetas_api():
    
    return func_buscar_recetas_api()

@app.route('/buscar_recetas_palabra')
def buscar_recetas_palabra_api():
   
    return func_buscar_recetas_palabra_api()

@app.route('/buscar_por_ingredientes')
def buscar_por_ingredientes():
  
    return buscar_por_ingredientes_api()


@app.route('/agregar_receta_comunidad', methods=['POST'])
def agregar_receta_comunidad():
    """Procesa el formulario de agregar receta desde comunidad"""
    try:
        print("=" * 50)
        print("🔍 DEBUG: INICIANDO AGREGAR_RECETA_COMUNIDAD")
        print("=" * 50)
        
        # Obtener datos del formulario
        title = request.form.get("recipeName", "").strip()
        url = request.form.get("recipeUrl", "").strip()
        ingredients = request.form.get("recipeIngredients", "").strip()
        instructions = request.form.get("recipeInstructions", "").strip()
        
        print(f"📝 DATOS DEL FORMULARIO:")
        print(f"   Título: {title}")
        print(f"   URL: {url}")
        print(f"   Ingredientes: {ingredients[:50]}...")
        print(f"   Instrucciones: {instructions[:50]}...")
        
        # Validar campos obligatorios
        if not title or not ingredients or not instructions:
            return jsonify({
                "success": False,
                "error": "Por favor completa todos los campos obligatorios (*)"
            })
        
        # Inicializar la variable con valor por defecto
        imagen_filename = None
        
        # Manejar la imagen
        if 'recipeImage' in request.files:
            imagen = request.files['recipeImage']
            if imagen.filename != '' and allowed_file(imagen.filename):
                # Generar nombre único para la imagen
                file_extension = imagen.filename.rsplit('.', 1)[1].lower()
                nuevo_filename = f"{uuid.uuid4()}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_filename)
                
                # Guardar la imagen
                imagen.save(filepath)
                imagen_filename = nuevo_filename
                print(f"✅ IMAGEN GUARDADA: {imagen_filename}")
        
        # Generar UUID para la receta
        nuevo_uuid = str(uuid.uuid4())
        print(f"🆔 UUID generado: {nuevo_uuid}")
        
        # Conectar a la base de datos
        conn = get_db_connection()
        
        # SOLUCIÓN TEMPORAL: Obtener el próximo ID manualmente
        with conn.cursor() as cur:
            # Obtener el máximo ID actual
            cur.execute("SELECT COALESCE(MAX(id), 0) FROM recetas_usuarios")
            max_id = cur.fetchone()[0]
            next_id = max_id + 1
            print(f"🆔 Próximo ID a usar: {next_id}")
            
            # Insertar con ID explícito
# En la función agregar_receta_comunidad(), modifica la consulta INSERT:
# Cámbiala por:
            insert_query = """
            INSERT INTO recetas_usuarios (id, title, url, ingredients, steps, uuid, imagen_filename, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (next_id, title, url, ingredients, instructions, nuevo_uuid, imagen_filename, session['usuario']))
            conn.commit()

# En la función agregar_receta_comunidad(), modifica la consulta INSERT:


            print("✅ RECETA GUARDADA EN LA BASE DE DATOS")
        
        conn.close()
        
        print("=" * 50)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 50)
        
        return jsonify({
            "success": True,
            "message": f"¡Receta '{title}' agregada exitosamente! 🎉",
            "uuid": nuevo_uuid
        })
        
    except Exception as e:
        print(f"❌ ERROR EXCEPCIÓN: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Error al agregar la receta: {str(e)}"
        })




@app.route('/admin/agregar_receta', methods=['POST'])
def admin_agregar_receta():
    """Procesa el formulario de agregar receta desde admin - ACTUALIZADO"""
    try:
        print("=" * 50)
        print("🔍 DEBUG: INICIANDO ADMIN_AGREGAR_RECETA")
        print("=" * 50)
        
       
        title = request.form.get("recipeName", "").strip()         
        categoria = request.form.get("recipeType", "").strip()     
        ingredients = request.form.get("recipeIngredients", "").strip() 
        steps = request.form.get("recipeInstructions", "").strip()   
        url = request.form.get("recipeUrl", "").strip()              
        
        print(f"📝 DATOS DEL FORMULARIO:")
        print(f"   Título: {title}")
        print(f"   Categoría: {categoria}")
        print(f"   URL: {url}")
        print(f"   Ingredientes: {ingredients[:50]}...")
        print(f"   Pasos: {steps[:50]}...")
        
        
        if not title or not categoria or not ingredients or not steps:
            return jsonify({
                "success": False,
                "error": "Por favor completa todos los campos obligatorios"
            })
        
        
        imagen_filename = None
        if 'recipeImage' in request.files: 
            imagen = request.files['recipeImage']
            if imagen.filename != '' and allowed_file(imagen.filename):
                
                file_extension = imagen.filename.rsplit('.', 1)[1].lower()
                nuevo_filename = f"{uuid.uuid4()}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_filename)
                
               
                imagen.save(filepath)
                imagen_filename = nuevo_filename
                print(f"✅ IMAGEN GUARDADA: {imagen_filename}")
        
        
        nuevo_uuid = str(uuid.uuid4())
        print(f"🆔 UUID generado: {nuevo_uuid}")
        
        conn = get_db_connection()
        with conn.cursor() as cur: 
            insert_query = """
            INSERT INTO recetas (title, url, ingredients, steps, uuid, categoria, imagen_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (title, url, ingredients, steps, nuevo_uuid, categoria, imagen_filename))
            conn.commit()
            print("✅ RECETA GUARDADA EN LA BASE DE DATOS")
        
        conn.close()
        
        print("=" * 50)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 50)
        
        return jsonify({
            "success": True,
            "message": f"¡Receta '{title}' agregada exitosamente! 🎉",
            "uuid": nuevo_uuid
        })
        
    except Exception as e:
        print(f"❌ ERROR EXCEPCIÓN: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Error al agregar la receta: {str(e)}"
        })
@app.route('/admin/obtener_recetas')
def admin_obtener_recetas():
    """Obtiene todas las recetas para el panel de administración (de ambas tablas) - CORREGIDO"""
    conn = get_db_connection()
    recetas = []
    
    try:
        with conn.cursor() as cur:
           
            cur.execute("""
                SELECT id, title, url, ingredients, steps, uuid, categoria, imagen_filename,
                       TO_CHAR(fecha_importacion, 'DD/MM/YYYY HH24:MI') as fecha, 'recetas' as tabla_origen
                FROM recetas 
                ORDER BY fecha_importacion DESC;
            """)
            
            resultados_recetas = cur.fetchall()
            
            for receta in resultados_recetas:
                recetas.append({
                    'id': receta[0],
                    'title': receta[1],
                    'url': receta[2],
                    'ingredients': receta[3],
                    'steps': receta[4],
                    'uuid': receta[5],
                    'categoria': receta[6],
                    'imagen_filename': receta[7],
                    'fecha': receta[8],
                    'tabla_origen': receta[9]
                })
            
           
            cur.execute("""
                SELECT id, title, url, ingredients, steps, uuid, imagen_filename,
                       TO_CHAR(fecha_creacion, 'DD/MM/YYYY HH24:MI') as fecha, 'recetas_usuarios' as tabla_origen
                FROM recetas_usuarios 
                ORDER BY fecha_creacion DESC;
            """)
            
            resultados_usuarios = cur.fetchall()
            
            for receta in resultados_usuarios:
                recetas.append({
                    'id': receta[0],
                    'title': receta[1],
                    'url': receta[2],
                    'ingredients': receta[3],
                    'steps': receta[4],
                    'uuid': receta[5],
                    'imagen_filename': receta[6],
                    'fecha': receta[7],
                    'tabla_origen': receta[8],
                    'categoria': 'comunidad'
                })
            
           
            recetas.sort(key=lambda x: x['fecha'], reverse=True)
                
    except Exception as e:
        print(f"Error obteniendo recetas para admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    return jsonify({"recetas": recetas})

@app.route('/admin/eliminar_receta/<int:receta_id>', methods=['DELETE'])
def admin_eliminar_receta(receta_id):
    """Elimina una receta específica de cualquier tabla"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            
            receta_encontrada = None
            tabla_origen = None
            
            
            cur.execute("SELECT title, imagen_filename FROM recetas WHERE id = %s", (receta_id,))
            receta = cur.fetchone()
            if receta:
                receta_encontrada = receta
                tabla_origen = 'recetas'
            else:
                
                cur.execute("SELECT title, imagen_filename FROM recetas_usuarios WHERE id = %s", (receta_id,))
                receta = cur.fetchone()
                if receta:
                    receta_encontrada = receta
                    tabla_origen = 'recetas_usuarios'
            
            if not receta_encontrada:
                return jsonify({
                    "success": False,
                    "error": "Receta no encontrada"
                })
            
           
            if tabla_origen == 'recetas':
                cur.execute("DELETE FROM recetas WHERE id = %s", (receta_id,))
            else:
                cur.execute("DELETE FROM recetas_usuarios WHERE id = %s", (receta_id,))
            
            conn.commit()
            
         
            if receta_encontrada[1]: 
                try:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], receta_encontrada[1])
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        print(f"✅ Imagen eliminada: {receta_encontrada[1]}")
                except Exception as e:
                    print(f"⚠️ Error eliminando imagen: {e}")
            
            print(f"✅ Receta '{receta_encontrada[0]}' eliminada exitosamente de {tabla_origen}")
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Receta '{receta_encontrada[0]}' eliminada exitosamente"
        })
        
    except Exception as e:
        print(f"❌ Error eliminando receta: {e}")
        return jsonify({
            "success": False,
            "error": f"Error al eliminar la receta: {str(e)}"
        })

@app.route('/buscar_recetas_michelin')
def buscar_recetas_michelin():
    """Búsqueda de recetas Michelin por nombre"""
    return func_buscar_recetas_michelin()

@app.route('/buscar_michelin_ingredientes')
def buscar_michelin_ingredientes():
    """Búsqueda de recetas Michelin por ingredientes"""
    return func_buscar_michelin_ingredientes()

@app.route('/estadisticas_michelin')
def obtener_estadisticas():
    """Obtener estadísticas de recetas Michelin"""
    return func_obtener_estadisticas()













# Rutas para los likes
@app.route('/dar_like', methods=['POST'])
def route_dar_like():
    return dar_like()

@app.route('/quitar_like', methods=['POST'])
def route_quitar_like():
    return quitar_like()

@app.route('/toggle_like', methods=['POST'])
def route_toggle_like():
    return toggle_like()

@app.route('/verificar_like', methods=['GET'])
def route_verificar_like():
    return verificar_usuario_likeo()

@app.route('/likes_receta', methods=['GET'])
def route_likes_receta():
    return obtener_likes_receta()

@app.route('/recetas_populares', methods=['GET'])
def route_recetas_populares():
    return obtener_recetas_populares()

@app.route('/recetas_con_like', methods=['GET'])
def route_recetas_con_like():
    return obtener_recetas_con_like()

@app.route('/obtener_recetas_comunidad')
def obtener_recetas_comunidad():
    """Obtiene las recetas de la comunidad - ACTUALIZADA"""
    conn = get_db_connection()
    recetas = []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ru.id,
                    ru.title,
                    ru.url,
                    ru.ingredients,
                    ru.steps,
                    ru.uuid,
                    ru.imagen_filename,
                    'Sin fecha' as fecha,
                    COALESCE(like_counts.likes_count, 0) as likes_count
                FROM recetas_usuarios ru
                LEFT JOIN (
                    SELECT recipe_id, COUNT(*) as likes_count 
                    FROM recipe_likes 
                    GROUP BY recipe_id
                ) like_counts ON ru.id = like_counts.recipe_id
                ORDER BY ru.id DESC
                LIMIT 50;
            """)
            
            resultados = cur.fetchall()
            
            for receta in resultados:
                recetas.append({
                    'id': receta[0],
                    'title': receta[1],
                    'url': receta[2],
                    'ingredients': receta[3],
                    'steps': receta[4],
                    'uuid': receta[5],
                    'imagen_filename': receta[6],
                    'tabla_origen': receta[7],
                    'likes_count': receta[8]  # Información de likes
                })
                
    except Exception as e:
        print(f"Error obteniendo recetas de comunidad: {e}")
    finally:
        conn.close()
    
    return jsonify({"recetas": recetas})

@app.route('/buscar_recetas_comunidad')
def buscar_recetas_comunidad():
    """Búsqueda específica para recetas de la comunidad - ACTUALIZADA"""
    try:
        search_term = request.args.get('q', '').strip()
        categoria = request.args.get('categoria', 'comunidad')
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            if search_term:
                # Búsqueda en recetas_usuarios
                query = """
                    SELECT 
                        ru.id,
                        ru.title,
                        ru.url,
                        ru.ingredients,
                        ru.steps,
                        ru.uuid,
                        ru.imagen_filename,
                        'Comunidad' as fuente,
                        COALESCE(like_counts.likes_count, 0) as likes_count
                    FROM recetas_usuarios ru
                    LEFT JOIN (
                        SELECT recipe_id, COUNT(*) as likes_count 
                        FROM recipe_likes 
                        GROUP BY recipe_id
                    ) like_counts ON ru.id = like_counts.recipe_id
                    WHERE (ru.title ILIKE %s OR ru.ingredients ILIKE %s OR ru.steps ILIKE %s)
                    ORDER BY ru.id DESC
                """
                search_pattern = f'%{search_term}%'
                cur.execute(query, (search_pattern, search_pattern, search_pattern))
            else:
                # Todas las recetas de la comunidad
                cur.execute("""
                    SELECT 
                        ru.id,
                        ru.title,
                        ru.url,
                        ru.ingredients,
                        ru.steps,
                        ru.uuid,
                        ru.imagen_filename,
                        'Comunidad' as fuente,
                        COALESCE(like_counts.likes_count, 0) as likes_count
                    FROM recetas_usuarios ru
                    LEFT JOIN (
                        SELECT recipe_id, COUNT(*) as likes_count 
                        FROM recipe_likes 
                        GROUP BY recipe_id
                    ) like_counts ON ru.id = like_counts.recipe_id
                    ORDER BY ru.id DESC
                    LIMIT 50
                """)
            
            resultados = cur.fetchall()
            recetas = []
            
            for receta in resultados:
                recetas.append({
                    'id': receta[0],
                    'title': receta[1],
                    'url': receta[2],
                    'ingredients': receta[3],
                    'steps': receta[4],
                    'uuid': receta[5],
                    'imagen_filename': receta[6],
                    'fuente': receta[7],
                    'likes_count': receta[8]  # Información de likes
                })
            
            return jsonify({"recetas": recetas})
            
    except Exception as e:
        print(f"Error en búsqueda comunidad: {e}")
        return jsonify({"recetas": []})
    finally:
        if 'conn' in locals():
            conn.close()

def verificar_tabla_recipe_likes():
    """Verifica que la tabla recipe_likes existe y la crea si no"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'recipe_likes'
                );
            """)
            tabla_existe = cur.fetchone()[0]
            
            if not tabla_existe:
                print("⚠️ Tabla 'recipe_likes' no existe - creándola...")
                cur.execute("""
                    CREATE TABLE recipe_likes (
                        id SERIAL PRIMARY KEY,
                        recipe_id INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(recipe_id, user_id)
                    );
                """)
                conn.commit()
                print("✅ Tabla 'recipe_likes' creada exitosamente")
            else:
                print("✅ Tabla 'recipe_likes' existe")
                
    except Exception as e:
        print(f"❌ Error verificando tabla recipe_likes: {e}")
    finally:
        conn.close()

# Llamar esta función después de crear las otras tablas
crear_tabla_usuarios()
verificar_tabla_recetas_usuarios()
verificar_tabla_recipe_likes()  # ← AGREGAR ESTA LÍNEA
            
if __name__ == '__main__':
    app.run(debug=True, port=5005)
