from flask import jsonify, request
import psycopg2

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

def buscar_recetas_michelin():
    """Búsqueda específica para recetas Michelin - POSTGRESQL"""
    termino_busqueda = request.args.get('q', '').strip().lower()
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
          
            if termino_busqueda:
                cur.execute("""
                    SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                           categoria_michelin, chef, fotochefURL, costo_ingredientes,
                           precio_venta_sugerido, alergenos, url_imagen_plato
                    FROM michelin 
                    WHERE (
                        title ILIKE %s OR
                        title ILIKE %s OR
                        title ILIKE %s OR
                        ingredients ILIKE %s OR
                        chef ILIKE %s
                    )
                    ORDER BY title
                """, (
                    f'{termino_busqueda}%',
                    f'%{termino_busqueda}%',
                    f'%{termino_busqueda}',
                    f'%{termino_busqueda}%',
                    f'%{termino_busqueda}%'
                ))
            else:
                cur.execute("""
                    SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                           categoria_michelin, chef, fotochefURL, costo_ingredientes,
                           precio_venta_sugerido, alergenos, url_imagen_plato
                    FROM michelin 
                    ORDER BY title
                """)
            
            recetas = cur.fetchall()
        
            recetas_json = []
            for receta in recetas:
               
                imagen_principal = receta[12] or receta[5] or '' 
                
                recetas_json.append({
                    'id': receta[0],  
                    'plato_uuid': receta[1],
                    'title': receta[2],
                    'ingredients': receta[3] or '',
                    'steps': receta[4] or '',
                    'imagen': imagen_principal,
                    'categoria': receta[6] or 'alta_cocina',
                    'chef': receta[7] or '',
                    'fotochefURL': receta[8] or '',
                    'costo_ingredientes': float(receta[9]) if receta[9] else '',
                    'precio_venta_sugerido': float(receta[10]) if receta[10] else '',
                    'alergenos': receta[11] or ''
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en búsqueda Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()

def buscar_michelin_ingredientes():
    """Búsqueda por ingredientes específica para recetas Michelin - POSTGRESQL"""
    ingredientes = request.args.get('ingredientes', '').strip().lower()
    
    if not ingredientes:
        return jsonify({'recetas': []})
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
           
            lista_ingredientes = [ing.strip() for ing in ingredientes.split(',') if ing.strip()]
            total_ingredientes_busqueda = len(lista_ingredientes)
            
          
            cur.execute("""
                SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                       categoria_michelin, chef, fotochefURL, costo_ingredientes,
                       precio_venta_sugerido, alergenos, url_imagen_plato
                FROM michelin 
            """)
            
            todas_recetas = cur.fetchall()
            
          
            recetas_rankeadas = []
            
            for receta in todas_recetas:
                (id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                 categoria_michelin, chef, fotochefURL, costo_ingredientes, 
                 precio_venta_sugerido, alergenos, url_imagen_plato) = receta
                
                if ingredients:
                    
                    ingredientes_receta = [ing.strip().lower() for ing in ingredients.split('\n') if ing.strip()]
                    
                   
                    coincidencias = calcular_coincidencias_michelin(ingredientes_receta, lista_ingredientes)
                    
                    if coincidencias['total_coincidencias'] > 0:
                        porcentaje_coincidencia = (coincidencias['total_coincidencias'] / total_ingredientes_busqueda) * 100
                        
                        
                        imagen_principal = url_imagen_plato or url_receta or ''
                        
                        recetas_rankeadas.append({
                            'id': id_michelin,
                            'plato_uuid': plato_uuid,
                            'title': title,
                            'imagen': imagen_principal, 
                            'ingredients': ingredients,
                            'steps': steps or '',
                            'categoria': categoria_michelin or 'alta_cocina',
                            'chef': chef or '',
                            'fotochefURL': fotochefURL or '',
                            'costo_ingredientes': float(costo_ingredientes) if costo_ingredientes else '',
                            'precio_venta_sugerido': float(precio_venta_sugerido) if precio_venta_sugerido else '',
                            'alergenos': alergenos or '',
                            'match_percentage': porcentaje_coincidencia,
                            'matched_ingredients': coincidencias['ingredientes_coincidentes'],
                            'total_search_ingredients': total_ingredientes_busqueda,
                            'matched_count': coincidencias['total_coincidencias']
                        })
            
           
            recetas_rankeadas.sort(key=lambda x: x['match_percentage'], reverse=True)
            
            return jsonify({'recetas': recetas_rankeadas})
            
    except Exception as e:
        print(f"Error en búsqueda por ingredientes Michelin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'recetas': []})
    finally:
        conn.close()

def obtener_estadisticas():
    """Obtener estadísticas de las recetas en la base de datos - POSTGRESQL"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            
            cur.execute("""
                SELECT categoria, COUNT(*) as cantidad 
                FROM recetas 
                GROUP BY categoria
            """)
            stats_recetas = cur.fetchall()
            
            
            cur.execute("SELECT COUNT(*) FROM michelin")
            total_michelin = cur.fetchone()[0]
            
            
            cur.execute("SELECT COUNT(DISTINCT chef) FROM michelin WHERE chef IS NOT NULL AND chef != ''")
            total_chefs = cur.fetchone()[0]
            
            estadisticas = {
                'recetas_por_categoria': {row[0]: row[1] for row in stats_recetas},
                'total_recetas_michelin': total_michelin,
                'total_chefs_michelin': total_chefs
            }
            
            return jsonify(estadisticas)
            
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'No se pudieron obtener las estadísticas'})
    finally:
        conn.close()


def calcular_coincidencias_michelin(ingredientes_receta, ingredientes_busqueda):
    """Función auxiliar para calcular coincidencias en recetas Michelin"""
    coincidencias = 0
    ingredientes_coincidentes = []
    
    for ing_busqueda in ingredientes_busqueda:
        ing_busqueda_limpio = ing_busqueda.strip().lower()
        encontrado = False
        
        for ing_receta in ingredientes_receta:
            if es_coincidencia_michelin(ing_receta, ing_busqueda_limpio):
                coincidencias += 1
                ingredientes_coincidentes.append(ing_receta)
                encontrado = True
                break
        
        
        if not encontrado:
            for ing_receta in ingredientes_receta:
                if ing_busqueda_limpio in ing_receta.lower():
                    coincidencias += 1
                    ingredientes_coincidentes.append(ing_receta)
                    break
    
    return {
        'total_coincidencias': coincidencias,
        'ingredientes_coincidentes': ingredientes_coincidentes
    }

def es_coincidencia_michelin(ingrediente_receta, ingrediente_busqueda):
    """Función auxiliar para detectar coincidencias en ingredientes gourmet"""
    ing_receta_limpio = limpiar_ingrediente_michelin(ingrediente_receta)
    ing_busqueda_limpio = limpiar_ingrediente_michelin(ingrediente_busqueda)
    
    
    if ing_receta_limpio == ing_busqueda_limpio:
        return True
    
    
    palabras_receta = ing_receta_limpio.split()
    if ing_busqueda_limpio in palabras_receta:
        return True
    
    
    if es_coincidencia_plural(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    
    if es_coincidencia_estricta_michelin(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    
    if ing_busqueda_limpio in ing_receta_limpio:
        return True
    
    return False

def es_coincidencia_estricta_michelin(ing_receta, ing_busqueda):
    """Coincidencias estrictas para ingredientes gourmet"""
    coincidencias_estrictas = {
        'trufa': ['trufa', 'trufas', 'trufa negra', 'trufa blanca'],
        'foie': ['foie', 'foie gras', 'foie-gras'],
        'caviar': ['caviar', 'caviars'],
        'langosta': ['langosta', 'langostas'],
        'vieira': ['vieira', 'vieiras'],
        'ostra': ['ostra', 'ostras'],
        'salmón': ['salmón', 'salmon', 'salmones'],
        'atún': ['atún', 'atun', 'atunes'],
        'ternera': ['ternera', 'terneras'],
        'cordero': ['cordero', 'corderos'],
        'pato': ['pato', 'patos'],
        'queso': ['queso', 'quesos'],
        'champán': ['champán', 'champan', 'champagne'],
        'vino': ['vino', 'vinos'],
        'aceite': ['aceite', 'aceites'],
        'mantequilla': ['mantequilla', 'mantequillas'],
        'nata': ['nata', 'crema'],
        'huevo': ['huevo', 'huevos'],
        'sal': ['sal'],
        'pimienta': ['pimienta', 'pimientas']
    }
    
    if ing_busqueda in coincidencias_estrictas:
        return any(term in ing_receta for term in coincidencias_estrictas[ing_busqueda])
    
    return False

def es_coincidencia_plural(ing_receta, ing_busqueda):
    """Detectar plurales para ingredientes gourmet"""
    plurales = {
        'trufa': ['trufas'],
        'foie': ['fois'],
        'caviar': ['caviares'],
        'langosta': ['langostas'],
        'vieira': ['vieiras'],
        'ostra': ['ostras'],
        'salmón': ['salmones'],
        'atún': ['atunes'],
        'ternera': ['terneras'],
        'cordero': ['corderos'],
        'pato': ['patos'],
        'queso': ['quesos'],
        'champán': ['champanes'],
        'vino': ['vinos'],
        'aceite': ['aceites'],
        'mantequilla': ['mantequillas']
    }
    
    
    if ing_busqueda in plurales:
        for plural in plurales[ing_busqueda]:
            if plural in ing_receta:
                return True
    
    
    for singular, plurales_lista in plurales.items():
        if ing_busqueda in plurales_lista and singular in ing_receta:
            return True
    
    return False

def limpiar_ingrediente_michelin(ingrediente):
    """Limpieza específica para ingredientes gourmet"""
    return (
        ingrediente.lower()
        .replace('.', '')
        .replace(',', '')
        .replace(';', '')
        .replace('!', '')
        .replace('?', '')
        .replace('(', '')
        .replace(')', '')
        .replace('/', ' ')
        .replace('  ', ' ')
        .strip()
    )