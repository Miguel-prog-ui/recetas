from flask import Flask, render_template, request, jsonify, send_file
import mysql.connector
from mysql.connector import Error
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# === CONFIGURACIÓN PARA IMÁGENES ===
app.config['UPLOAD_FOLDER'] = 'static/imagenes_recetas'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Configuración para MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root", 
    "password": "",
    "database": "recetas",
    "charset": "utf8mb4"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None

# === FUNCIONES DE LIKES ===
def dar_like_receta(receta_uuid):
    """Agrega un like a una receta"""
    print(f"Intentando dar like al UUID: {receta_uuid}")
    conn = get_db_connection()
    if conn is None:
        return False
        
    try:
        with conn.cursor() as cur:
            # Primero verifiquemos si la receta existe
            cur.execute("SELECT uuid FROM recetas WHERE uuid = %s;", (receta_uuid,))
            if not cur.fetchone():
                print("❌ UUID no encontrado en la tabla recetas")
                return False
            
            # MySQL usa IGNORE en lugar de ON CONFLICT
            insert_query = """
            INSERT IGNORE INTO recetas_likes (receta_uuid) 
            VALUES (%s);
            """
            cur.execute(insert_query, (receta_uuid,))
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Like agregado para UUID: {receta_uuid}")
                return True
            else:
                print("ℹ️ Like ya existía (ignorado)")
                return True
                
    except Error as e:
        print(f"❌ Error dando like: {e}")
        return False
    finally:
        conn.close()

def obtener_likes_receta(receta_uuid):
    """Obtiene el número de likes de una receta"""
    conn = get_db_connection()
    if conn is None:
        return 0
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM recetas_likes WHERE receta_uuid = %s;", (receta_uuid,))
            result = cur.fetchone()
            count = result[0] if result else 0
            print(f"📊 Likes para {receta_uuid}: {count}")
            return count
    except Error as e:
        print(f"Error obteniendo likes: {e}")
        return 0
    finally:
        conn.close()

def obtener_likes_masivos(lista_uuids):
    """Obtiene los likes para múltiples recetas de una sola vez"""
    if not lista_uuids:
        return {}
    
    conn = get_db_connection()
    if conn is None:
        return {}
        
    likes_dict = {}
    try:
        with conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(lista_uuids))
            query = f"SELECT receta_uuid, COUNT(*) FROM recetas_likes WHERE receta_uuid IN ({placeholders}) GROUP BY receta_uuid;"
            cur.execute(query, lista_uuids)
            
            for receta_uuid, count in cur.fetchall():
                likes_dict[receta_uuid] = count
                
    except Error as e:
        print(f"Error obteniendo likes masivos: {e}")
    finally:
        conn.close()
    
    return likes_dict

# === RUTAS DE LIKES ===
@app.route("/like/<receta_uuid>")
def like_receta(receta_uuid):
    """Ruta para dar like a una receta - ahora devuelve JSON"""
    print(f"📨 Petición LIKE recibida para: {receta_uuid}")
    
    # Validar que el UUID tenga formato correcto
    try:
        uuid.UUID(receta_uuid)
    except ValueError:
        return jsonify({"success": False, "error": "UUID inválido"})
    
    success = dar_like_receta(receta_uuid)
    
    if success:
        nuevo_conteo = obtener_likes_receta(receta_uuid)
        return jsonify({
            "success": True, 
            "message": "✅ Like agregado!",
            "nuevo_conteo": nuevo_conteo
        })
    else:
        return jsonify({
            "success": False, 
            "error": "❌ Error al agregar like"
        })

@app.route("/likes/<receta_uuid>")
def ver_likes_receta(receta_uuid):
    """Ruta para ver los likes de una receta específica"""
    try:
        uuid.UUID(receta_uuid)  # Validar UUID
    except ValueError:
        return "UUID inválido", 400
    
    likes = obtener_likes_receta(receta_uuid)
    return f"Likes: {likes}"

# === FUNCIONES DE BÚSQUEDA ===
def buscar_recetas_por_ingredientes(ingredientes_busqueda):
    conn = get_db_connection()
    if conn is None:
        return []
        
    recetas = []
    
    try:
        with conn.cursor() as cur:
            ingredientes_lista = [ing.strip() for ing in ingredientes_busqueda.split(',') if ing.strip()]
            
            if not ingredientes_lista:
                return []
            
            condiciones = []
            parametros = []
            
            for ingrediente in ingredientes_lista:
                condiciones.append("ingredients LIKE %s")
                parametros.append(f'%{ingrediente}%')
            
            where_clause = " AND ".join(condiciones)
            query = f"""
                SELECT title, url, ingredients, steps, uuid, imagen_filename
                FROM recetas 
                WHERE {where_clause}
                ORDER BY title
                LIMIT 50;
            """
            
            cur.execute(query, parametros)
            resultados = cur.fetchall()
            
            uuids = [receta[4] for receta in resultados]
            likes_dict = obtener_likes_masivos(uuids)
            
            for receta in resultados:
                recetas.append({
                    'title': receta[0],
                    'url': receta[1],
                    'ingredients': receta[2],
                    'steps': receta[3],
                    'uuid': receta[4],
                    'imagen_filename': receta[5],
                    'likes': likes_dict.get(receta[4], 0)
                })
                
    except Error as e:
        print(f"Error en búsqueda: {e}")
    finally:
        conn.close()
    
    return recetas

def get_recetas_recientes(limite=20):
    conn = get_db_connection()
    if conn is None:
        return []
        
    recetas = []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT title, url, ingredients, steps, uuid, imagen_filename
                FROM recetas 
                ORDER BY id DESC
                LIMIT %s;
            """, (limite,))
            
            resultados = cur.fetchall()
            
            uuids = [receta[4] for receta in resultados]
            likes_dict = obtener_likes_masivos(uuids)
            
            for receta in resultados:
                recetas.append({
                    'title': receta[0],
                    'url': receta[1],
                    'ingredients': receta[2],
                    'steps': receta[3],
                    'uuid': receta[4],
                    'imagen_filename': receta[5],
                    'likes': likes_dict.get(receta[4], 0)
                })
                
    except Error as e:
        print(f"Error obteniendo recetas recientes: {e}")
    finally:
        conn.close()
    
    return recetas

# === RUTAS PRINCIPALES ===
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Búsqueda por ingredientes
        consulta = request.form["ingredientes"]
        resultados = buscar_recetas_por_ingredientes(consulta)
        return render_template("busqueda.html", 
                             recetas=resultados, 
                             consulta=consulta,
                             tipo_busqueda="ingredientes")
    else:
        # Página inicial - mostrar recetas recientes
        recetas_recientes = get_recetas_recientes(20)
        return render_template("busqueda.html", 
                             recetas=recetas_recientes,
                             consulta="",
                             tipo_busqueda="recientes")

@app.route("/receta/<uuid>")
def ver_receta(uuid):
    """Página para ver una receta completa"""
    conn = get_db_connection()
    if conn is None:
        return "Error de conexión a la base de datos", 500
        
    receta = None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT title, url, ingredients, steps
                FROM recetas 
                WHERE uuid = %s;
            """, (uuid,))
            
            resultado = cur.fetchone()
            if resultado:
                receta = {
                    'title': resultado[0],
                    'url': resultado[1],
                    'ingredients': resultado[2],
                    'steps': resultado[3],
                    'likes': obtener_likes_receta(uuid)
                }
                
    except Error as e:
        print(f"Error obteniendo receta: {e}")
    finally:
        conn.close()
    
    return render_template("receta_detalle.html", receta=receta)

@app.route("/agregar_receta", methods=["GET", "POST"])
def agregar_receta():
    if request.method == "POST":
        try:
            print("=" * 50)
            print("🔍 DEBUG: INICIANDO AGREGAR_RECETA")
            print("=" * 50)
            
            # Debug completo de la request
            print("📨 HEADERS:", dict(request.headers))
            print("📝 FORM DATA:", dict(request.form))
            print("📁 FILES RECIBIDOS:", dict(request.files))
            
            # Verificar cada archivo individualmente
            for key, file in request.files.items():
                print(f"📂 Archivo '{key}': nombre='{file.filename}', tamaño={len(file.read())}")
                file.seek(0)  # Resetear después de leer
            
            # Obtener datos del formulario
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()
            ingredients = request.form.get("ingredients", "").strip()
            steps = request.form.get("steps", "").strip()
            
            print(f"📝 DATOS DEL FORMULARIO:")
            print(f"   Título: {title}")
            print(f"   URL: {url}")
            print(f"   Ingredientes: {ingredients[:50]}...")
            print(f"   Pasos: {steps[:50]}...")
            
            # Validar campos requeridos
            if not title or not ingredients or not steps:
                print("❌ ERROR: Campos requeridos vacíos")
                return """
                <html>
                    <body style="font-family: Arial; padding: 20px;">
                        <h1>❌ Error: Campos requeridos vacíos</h1>
                        <p>Por favor completa al menos el título, ingredientes y pasos.</p>
                        <a href="/agregar_receta">Intentar de nuevo</a>
                    </body>
                </html>
                """
            
            # MANEJO DE IMAGEN
            imagen_filename = None
            
            if 'imagen' not in request.files:
                print("❌ No se encontró el campo 'imagen' en request.files")
                print("ℹ️ Campos disponibles:", list(request.files.keys()))
            else:
                imagen = request.files['imagen']
                print(f"📂 IMAGEN RECIBIDA: nombre='{imagen.filename}', tipo='{imagen.content_type}'")
                
                if imagen.filename == '':
                    print("ℹ️ Campo 'imagen' está vacío (sin archivo seleccionado)")
                else:
                    if allowed_file(imagen.filename):
                        # Generar nombre único
                        file_extension = imagen.filename.rsplit('.', 1)[1].lower()
                        nuevo_filename = f"{uuid.uuid4()}.{file_extension}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_filename)
                        
                        print(f"💾 Guardando imagen en: {filepath}")
                        
                        # Guardar la imagen
                        imagen.save(filepath)
                        
                        # Verificar que se guardó
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            imagen_filename = nuevo_filename
                            print(f"✅ IMAGEN GUARDADA: {imagen_filename} ({file_size} bytes)")
                        else:
                            print("❌ ERROR: La imagen no se guardó correctamente")
                    else:
                        print(f"❌ Archivo no permitido: {imagen.filename}")
            
            # Generar UUID
            nuevo_uuid = str(uuid.uuid4())
            print(f"🆔 UUID generado: {nuevo_uuid}")
            print(f"📊 RESUMEN - Imagen: {imagen_filename}")
            
            # Insertar en la base de datos
            conn = get_db_connection()
            if conn is None:
                return "Error de conexión a la base de datos", 500
                
            with conn.cursor() as cur:
                insert_query = """
                INSERT INTO recetas_usuarios (title, url, ingredients, steps, uuid, imagen_filename)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (title, url, ingredients, steps, nuevo_uuid, imagen_filename))
                conn.commit()
                print("✅ RECETA GUARDADA EN LA BASE DE DATOS")
            
            conn.close()
            
            print("=" * 50)
            print("✅ PROCESO COMPLETADO EXITOSAMENTE")
            print("=" * 50)
            
            # Mensaje de éxito
            return f"""
            <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h1>✅ Receta agregada exitosamente!</h1>
                    <p>Tu receta ha sido guardada en la base de datos de recetas de usuarios.</p>
                    {'<p style="color: green;">✅ Imagen subida correctamente: ' + imagen_filename + '</p>' 
                     if imagen_filename else '<p style="color: orange;">ℹ️ No se subió imagen</p>'}
                    <p><strong>Debug Info:</strong></p>
                    <ul>
                        <li>UUID: {nuevo_uuid}</li>
                        <li>Imagen: {imagen_filename or 'None'}</li>
                        <li>Archivos recibidos: {list(request.files.keys())}</li>
                    </ul>
                    <a href="/">Volver al buscador</a> | 
                    <a href="/agregar_receta">Agregar otra receta</a>
                </body>
            </html>
            """
            
        except Exception as e:
            print(f"❌ ERROR EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = str(e)
            if "permission denied" in error_msg.lower():
                error_msg = "Error de permisos: El usuario no tiene permisos para agregar recetas. Contacta al administrador."
            
            return f"""
            <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h1>❌ Error al agregar la receta</h1>
                    <p><strong>Error:</strong> {error_msg}</p>
                    <a href="/agregar_receta">Intentar de nuevo</a> |
                    <a href="/">Volver al buscador</a>
                </body>
            </html>
            """
    
    # Si es GET, mostrar el formulario
    return render_template("agregar_receta.html")

def get_recetas_usuarios(limite=50):
    """Obtiene las recetas agregadas por usuarios"""
    conn = get_db_connection()
    if conn is None:
        return []
        
    recetas = []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT title, url, ingredients, steps, uuid, imagen_filename,
                       DATE_FORMAT(fecha_creacion, '%%d/%%m/%%Y %%H:%%i') as fecha
                FROM recetas_usuarios 
                ORDER BY fecha_creacion DESC
                LIMIT %s;
            """, (limite,))
            
            resultados = cur.fetchall()
            
            # Obtener UUIDs para buscar likes
            uuids = [receta[4] for receta in resultados]
            likes_dict = obtener_likes_masivos(uuids)
            
            for receta in resultados:
                recetas.append({
                    'title': receta[0],
                    'url': receta[1],
                    'ingredients': receta[2],
                    'steps': receta[3],
                    'uuid': receta[4],
                    'imagen_filename': receta[5],
                    'fecha': receta[6],
                    'likes': likes_dict.get(receta[4], 0)
                })
                
    except Error as e:
        print(f"Error obteniendo recetas de usuarios: {e}")
    finally:
        conn.close()
    
    return recetas

@app.route("/recetas_usuarios")
def recetas_usuarios():
    """Página para mostrar solo las recetas agregadas por usuarios"""
    recetas = get_recetas_usuarios(50)
    
    return render_template("recetas_usuarios.html", 
                         recetas=recetas,
                         total_recetas=len(recetas))

if __name__ == "__main__":
    # Ejecutar la aplicación
    app.run(debug=True, port=5005)