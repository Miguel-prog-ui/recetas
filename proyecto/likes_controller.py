# likes_controller.py - ACTUALIZADO
from flask import jsonify, request
import psycopg2
from psycopg2 import sql

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

def verificar_receta_existe(recipe_id):
    """Verifica si una receta existe en cualquiera de las tablas"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Verificar en recetas
            cur.execute("SELECT id FROM recetas WHERE id = %s", (recipe_id,))
            if cur.fetchone():
                return True
            
            # Verificar en recetas_usuarios
            cur.execute("SELECT id FROM recetas_usuarios WHERE id = %s", (recipe_id,))
            if cur.fetchone():
                return True
            
            return False
    except Exception as e:
        print(f"Error verificando receta: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def toggle_like():
    """Toggle like: si no tiene like, lo da; si ya tiene like, lo quita - ACTUALIZADO"""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        user_id = data.get('user_id')
        
        if not recipe_id or not user_id:
            return jsonify({'error': 'recipe_id y user_id son requeridos'}), 400
        
        # Convertir recipe_id a integer
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'recipe_id debe ser un número válido'}), 400
        
        # Verificar que la receta existe
        if not verificar_receta_existe(recipe_id_int):
            return jsonify({'error': 'La receta no existe'}), 404
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Primero verificar si ya existe el like
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM recipe_likes 
                    WHERE recipe_id = %s AND user_id = %s
                )
            """, (recipe_id_int, user_id))
            
            exists_result = cur.fetchone()
            already_liked = exists_result[0] if exists_result else False
            
            if already_liked:
                # Quitar like
                cur.execute("""
                    DELETE FROM recipe_likes 
                    WHERE recipe_id = %s AND user_id = %s
                """, (recipe_id_int, user_id))
                action = 'removed'
            else:
                # Dar like
                cur.execute("""
                    INSERT INTO recipe_likes (recipe_id, user_id) 
                    VALUES (%s, %s)
                """, (recipe_id_int, user_id))
                action = 'added'
            
            conn.commit()
            
            # Obtener conteo actualizado
            total_likes = obtener_conteo_likes(recipe_id_int)
            
            return jsonify({
                'success': True,
                'action': action,
                'total_likes': total_likes,
                'user_liked': not already_liked
            })
                
    except Exception as e:
        print(f"Error en toggle like: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def obtener_conteo_likes(recipe_id):
    """Obtener el número total de likes de una receta"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM recipe_likes 
                WHERE recipe_id = %s
            """, (recipe_id,))
            
            result = cur.fetchone()
            return result[0] if result else 0
            
    except Exception as e:
        print(f"Error al obtener conteo de likes: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def verificar_usuario_likeo():
    """Verificar si un usuario dio like a una receta específica - ACTUALIZADO"""
    try:
        recipe_id = request.args.get('recipe_id')
        user_id = request.args.get('user_id')
        
        if not recipe_id or not user_id:
            return jsonify({'error': 'recipe_id y user_id son requeridos'}), 400
        
        # Convertir recipe_id a integer
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'recipe_id debe ser un número válido'}), 400
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM recipe_likes 
                    WHERE recipe_id = %s AND user_id = %s
                )
            """, (recipe_id_int, user_id))
            
            result = cur.fetchone()
            user_liked = result[0] if result else False
            
            return jsonify({
                'user_liked': user_liked
            })
                
    except Exception as e:
        print(f"Error al verificar like: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def obtener_likes_receta():
    """Obtener información completa de likes de una receta - ACTUALIZADO"""
    try:
        recipe_id = request.args.get('recipe_id')
        user_id = request.args.get('user_id')  # Opcional
        
        if not recipe_id:
            return jsonify({'error': 'recipe_id es requerido'}), 400
        
        # Convertir recipe_id a integer
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'recipe_id debe ser un número válido'}), 400
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Obtener conteo total de likes
            cur.execute("""
                SELECT COUNT(*) FROM recipe_likes 
                WHERE recipe_id = %s
            """, (recipe_id_int,))
            
            total_likes_result = cur.fetchone()
            total_likes = total_likes_result[0] if total_likes_result else 0
            
            # Verificar si el usuario específico dio like (si se proporciona user_id)
            user_liked = False
            if user_id:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM recipe_likes 
                        WHERE recipe_id = %s AND user_id = %s
                    )
                """, (recipe_id_int, user_id))
                
                user_liked_result = cur.fetchone()
                user_liked = user_liked_result[0] if user_liked_result else False
            
            return jsonify({
                'recipe_id': recipe_id_int,
                'total_likes': total_likes,
                'user_liked': user_liked
            })
                
    except Exception as e:
        print(f"Error al obtener likes de receta: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def obtener_recetas_populares():
    """Obtener las recetas más populares (con más likes) de AMBAS tablas"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Recetas de la tabla principal
            cur.execute("""
                SELECT 
                    r.id,
                    r.title,
                    r.categoria,
                    r.imagen_filename,
                    COUNT(rl.id) as likes_count,
                    'recetas' as tabla_origen
                FROM recetas r
                LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                GROUP BY r.id, r.title, r.categoria, r.imagen_filename
                
                UNION ALL
                
                -- Recetas de la comunidad
                SELECT 
                    ru.id,
                    ru.title,
                    'comunidad' as categoria,
                    ru.imagen_filename,
                    COUNT(rl.id) as likes_count,
                    'recetas_usuarios' as tabla_origen
                FROM recetas_usuarios ru
                LEFT JOIN recipe_likes rl ON ru.id = rl.recipe_id
                GROUP BY ru.id, ru.title, ru.imagen_filename
                
                ORDER BY likes_count DESC, title
                LIMIT %s
            """, (limit,))
            
            recetas_populares = cur.fetchall()
            
            recetas_json = []
            for receta in recetas_populares:
                imagen_url = f"/static/imagenes_recetas/{receta[3]}" if receta[3] else ""
                
                recetas_json.append({
                    'id': receta[0],
                    'title': receta[1],
                    'categoria': receta[2],
                    'imagen': imagen_url,
                    'likes_count': receta[4],
                    'tabla_origen': receta[5]
                })
            
            return jsonify({'recetas_populares': recetas_json})
                
    except Exception as e:
        print(f"Error al obtener recetas populares: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()
            
def obtener_recetas_con_like():
    """Obtener todas las recetas que un usuario ha dado like, ordenadas por fecha - ACTUALIZADO"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id es requerido'}), 400
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                -- Recetas de la tabla principal
                SELECT 
                    r.id,
                    r.title,
                    r.ingredients,
                    r.steps,
                    r.categoria,
                    r.imagen_filename,
                    r.url,
                    rl.created_at as liked_at,
                    (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as total_likes,
                    'recetas' as tabla_origen
                FROM recetas r
                INNER JOIN recipe_likes rl ON r.id = rl.recipe_id
                WHERE rl.user_id = %s
                
                UNION ALL
                
                -- Recetas de la comunidad
                SELECT 
                    ru.id,
                    ru.title,
                    ru.ingredients,
                    ru.steps,
                    'comunidad' as categoria,
                    ru.imagen_filename,
                    ru.url,
                    rl.created_at as liked_at,
                    (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = ru.id) as total_likes,
                    'recetas_usuarios' as tabla_origen
                FROM recetas_usuarios ru
                INNER JOIN recipe_likes rl ON ru.id = rl.recipe_id
                WHERE rl.user_id = %s
                
                ORDER BY liked_at DESC
            """, (user_id, user_id))
            
            recetas = cur.fetchall()
            
            recetas_json = []
            for receta in recetas:
                imagen_url = f"/static/imagenes_recetas/{receta[5]}" if receta[5] else ""
                
                recetas_json.append({
                    'id': receta[0],
                    'title': receta[1],
                    'ingredients': receta[2],
                    'steps': receta[3],
                    'categoria': receta[4],
                    'imagen': imagen_url,
                    'url': receta[6],
                    'liked_at': receta[7].isoformat() if receta[7] else None,
                    'total_likes': receta[8],
                    'tabla_origen': receta[9]
                })
            
            return jsonify({
                'success': True,
                'recetas': recetas_json,
                'total': len(recetas_json)
            })
                
    except Exception as e:
        print(f"Error al obtener recetas con like: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Mantener las funciones existentes para compatibilidad
def dar_like():
    """Dar like a una receta"""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        user_id = data.get('user_id')
        
        if not recipe_id or not user_id:
            return jsonify({'error': 'recipe_id y user_id son requeridos'}), 400
        
        # Convertir recipe_id a integer
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'recipe_id debe ser un número válido'}), 400
        
        # Verificar que la receta existe
        if not verificar_receta_existe(recipe_id_int):
            return jsonify({'error': 'La receta no existe'}), 404
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Intentar insertar el like
            cur.execute("""
                INSERT INTO recipe_likes (recipe_id, user_id) 
                VALUES (%s, %s)
                ON CONFLICT (recipe_id, user_id) DO NOTHING
                RETURNING id
            """, (recipe_id_int, user_id))
            
            conn.commit()
            
            if cur.rowcount > 0:
                # Like exitoso, obtener conteo actualizado
                total_likes = obtener_conteo_likes(recipe_id_int)
                return jsonify({
                    'success': True,
                    'message': 'Like agregado',
                    'total_likes': total_likes,
                    'user_liked': True
                })
            else:
                # El usuario ya había dado like
                total_likes = obtener_conteo_likes(recipe_id_int)
                return jsonify({
                    'success': False,
                    'message': 'Ya habías dado like a esta receta',
                    'total_likes': total_likes,
                    'user_liked': True
                })
                
    except Exception as e:
        print(f"Error al dar like: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def quitar_like():
    """Quitar like de una receta"""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        user_id = data.get('user_id')
        
        if not recipe_id or not user_id:
            return jsonify({'error': 'recipe_id y user_id son requeridos'}), 400
        
        # Convertir recipe_id a integer
        try:
            recipe_id_int = int(recipe_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'recipe_id debe ser un número válido'}), 400
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM recipe_likes 
                WHERE recipe_id = %s AND user_id = %s
            """, (recipe_id_int, user_id))
            
            conn.commit()
            
            total_likes = obtener_conteo_likes(recipe_id_int)
            
            return jsonify({
                'success': True,
                'message': 'Like removido',
                'total_likes': total_likes,
                'user_liked': False
            })
                
    except Exception as e:
        print(f"Error al quitar like: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'conn' in locals():
            conn.close()