# recetas_controller.py
from flask import jsonify, request
import psycopg2

def get_db_connection():
    """Usa la misma configuración existente de PostgreSQL"""
    DB_CONFIG = {
        "host": "localhost",
        "user": "moya_user", 
        "password": "moya123",
        "database": "recetas_db",
        "client_encoding": "UTF8"
    }
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

def obtener_recetas_usuario(usuario=None, orden="fecha_desc"):
    """Obtiene todas las recetas de recetas_usuarios, opcionalmente filtradas por usuario y orden"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            
            # Definir el ordenamiento
            if orden == "fecha_desc":
                orden_sql = "ORDER BY fecha_creacion DESC"
            elif orden == "fecha_asc":
                orden_sql = "ORDER BY fecha_creacion ASC"
            elif orden == "titulo_asc":
                orden_sql = "ORDER BY title ASC"
            elif orden == "titulo_desc":
                orden_sql = "ORDER BY title DESC"
            elif orden == "likes_desc":
                # Ordenar por likes (más populares primero)
                orden_sql = "ORDER BY likes_count DESC, fecha_creacion DESC"
            elif orden == "likes_asc":
                # Ordenar por likes (menos populares primero)
                orden_sql = "ORDER BY likes_count ASC, fecha_creacion DESC"
            else:
                orden_sql = "ORDER BY fecha_creacion DESC"  # Por defecto
            
            if usuario:
                # Obtener recetas de un usuario específico con conteo de likes
                query = f"""
                    SELECT 
                        ru.id,
                        ru.title,
                        ru.ingredients,
                        ru.steps,
                        ru.uuid,
                        ru.fecha_creacion,
                        ru.imagen_filename,
                        ru.usuario,
                        COALESCE(like_counts.likes_count, 0) as likes_count
                    FROM recetas_usuarios ru
                    LEFT JOIN (
                        SELECT recipe_id, COUNT(*) as likes_count 
                        FROM recipe_likes 
                        GROUP BY recipe_id
                    ) like_counts ON ru.id = like_counts.recipe_id
                    WHERE usuario = %s
                    {orden_sql}
                """
                cur.execute(query, (usuario,))
            else:
                # Obtener todas las recetas con conteo de likes
                query = f"""
                    SELECT 
                        ru.id,
                        ru.title,
                        ru.ingredients,
                        ru.steps,
                        ru.uuid,
                        ru.fecha_creacion,
                        ru.imagen_filename,
                        ru.usuario,
                        COALESCE(like_counts.likes_count, 0) as likes_count
                    FROM recetas_usuarios ru
                    LEFT JOIN (
                        SELECT recipe_id, COUNT(*) as likes_count 
                        FROM recipe_likes 
                        GROUP BY recipe_id
                    ) like_counts ON ru.id = like_counts.recipe_id
                    {orden_sql}
                """
                cur.execute(query)
            
            recetas = cur.fetchall()
            return recetas
            
    except Exception as e:
        print(f"Error al obtener recetas: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def obtener_todas_recetas(orden="fecha_desc"):
    """Obtiene todas las recetas sin filtrar por usuario"""
    return obtener_recetas_usuario(usuario=None, orden=orden)

def obtener_mis_recetas(usuario, orden="fecha_desc"):
    """Obtiene solo las recetas del usuario actual"""
    return obtener_recetas_usuario(usuario=usuario, orden=orden)

def obtener_recetas_filtradas():
    """Endpoint para obtener recetas con filtros desde el frontend"""
    try:
        usuario = request.args.get('usuario')
        orden = request.args.get('orden', 'fecha_desc')
        
        if usuario:
            recetas = obtener_mis_recetas(usuario, orden)
        else:
            recetas = obtener_todas_recetas(orden)
        
        # Convertir a formato JSON
        recetas_json = []
        for receta in recetas:
            recetas_json.append({
                'id': receta[0],
                'title': receta[1],
                'ingredients': receta[2],
                'steps': receta[3],
                'uuid': receta[4],
                'fecha_creacion': receta[5].strftime('%d/%m/%Y') if receta[5] else '',
                'imagen_filename': receta[6],
                'usuario': receta[7],
                'likes_count': receta[8]
            })
        
        return jsonify({
            'success': True,
            'recetas': recetas_json,
            'total': len(recetas_json)
        })
        
    except Exception as e:
        print(f"Error en obtener_recetas_filtradas: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener recetas',
            'recetas': []
        })