from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='recetas'
    )

def cargar_recetas():
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT title, url, ingredients, steps, uuid FROM recetas")
    recetas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return recetas

def dar_like_receta(receta_uuid):
    """Agrega un like a una receta"""
    print(f"Intentando dar like al UUID: {receta_uuid}")  # DEBUG
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT uuid FROM recetas WHERE uuid = %s;", (receta_uuid,))
            if not cur.fetchone():
                print("❌ UUID no encontrado en la tabla recetas")
                return False
            
            insert_query = """
            INSERT IGNORE INTO recetas_likes (receta_uuid) 
            VALUES (%s);
            """
            cur.execute(insert_query, (receta_uuid,))
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Like agregado para UUID: {receta_uuid}")
            else:
                print("ℹ️ Like ya existía (ignorado por INSERT IGNORE)")
            return True
                
    except Exception as e:
        print(f"❌ Error dando like: {e}")
        return False
    finally:
        conn.close()

def obtener_likes_receta(receta_uuid):
    """Obtiene el número de likes de una receta"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM recetas_likes WHERE receta_uuid = %s;", (receta_uuid,))
            count = cur.fetchone()[0]
            print(f"📊 Likes para {receta_uuid}: {count}")  # DEBUG
            return count
    except Exception as e:
        print(f"Error obteniendo likes: {e}")
        return 0
    finally:
        conn.close()

def obtener_likes_masivos(lista_uuids):
    """Obtiene los likes para múltiples recetas de una sola vez"""
    if not lista_uuids:
        return {}
    
    conn = get_db_connection()
    likes_dict = {}
    try:
        with conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(lista_uuids))
            query = f"""
            SELECT receta_uuid, COUNT(*) AS total_likes 
            FROM recetas_likes 
            WHERE receta_uuid IN ({placeholders}) 
            GROUP BY receta_uuid;
            """
            cur.execute(query, lista_uuids)
            for receta_uuid, count in cur.fetchall():
                likes_dict[receta_uuid] = count
                
    except Exception as e:
        print(f"Error obteniendo likes masivos: {e}")
    finally:
        conn.close()
    
    return likes_dict

@app.route('/', methods=['GET', 'POST'])
def mostrar_recetas():
    recetas = cargar_recetas()
    ingredientes = ''
    if request.method == 'POST':
        ingredientes = request.form.get('ingredientes', '').lower()
        lista_ingredientes = [i.strip() for i in ingredientes.split(',') if i.strip()]
        recetas = [
            r for r in recetas
            if all(ing in r['ingredients'].lower() for ing in lista_ingredientes)
        ]
    # Agregar likes masivos
    lista_uuids = [r['uuid'] for r in recetas]
    likes_dict = obtener_likes_masivos(lista_uuids)
    for r in recetas:
        r['likes'] = likes_dict.get(r['uuid'], 0)
    return render_template('recetas.html', recetas=recetas, ingredientes=ingredientes)

def buscar_recetas_por_ingredientes(ingredientes_busqueda):
    conn = get_db_connection()
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
                parametros.append(f"%{ingrediente}%")
            
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
                
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    finally:
        conn.close()
    
    return recetas

def get_recetas_recientes(limite=20):
    conn = get_db_connection()
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
                
    except Exception as e:
        print(f"Error obteniendo recetas recientes: {e}")
    finally:
        conn.close()
    
    return recetas


if __name__ == '__main__':
    app.run(debug=True)
