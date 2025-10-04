from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

def get_db_connection():
    """Usa tu configuración existente de PostgreSQL"""
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

def buscar_recetas_palabra_api():
    termino_busqueda = request.args.get('q', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    if not termino_busqueda:
        return jsonify({'recetas': []})
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
          
            if categoria:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria, imagen_filename  -- 🔥 AGREGADO
                    FROM recetas 
                    WHERE (
                        title ILIKE %s OR
                        title ILIKE %s OR  
                        title ILIKE %s OR
                        title ILIKE %s OR
                        title ILIKE %s
                    ) AND LOWER(categoria) = LOWER(%s)
                    ORDER BY title
                """, (
                    f'{termino_busqueda} %',
                    f'% {termino_busqueda}',
                    f'% {termino_busqueda} %',
                    termino_busqueda,
                    f'%({termino_busqueda} %',
                    categoria
                ))
            else:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria, imagen_filename  -- 🔥 AGREGADO
                    FROM recetas 
                    WHERE (
                        title ILIKE %s OR
                        title ILIKE %s OR
                        title ILIKE %s OR
                        title ILIKE %s OR
                        title ILIKE %s
                    )
                    ORDER BY title
                """, (
                    f'{termino_busqueda} %',
                    f'% {termino_busqueda}',
                    f'% {termino_busqueda} %',
                    termino_busqueda,
                    f'%({termino_busqueda} %'
                ))
            
            recetas = cur.fetchall()
            
            recetas_json = []
            for receta in recetas:
                recetas_json.append({
                    'id': receta[0],
                    'title': receta[1],
                    'imagen': receta[2],
                    'ingredients': receta[3] or '',
                    'steps': receta[4] or '',
                    'categoria': receta[5],
                    'imagen_filename': receta[6]
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en búsqueda por palabra: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()

@app.route('/buscar_recetas_michelin')
def buscar_recetas_michelin():
    termino_busqueda = request.args.get('q', '').strip().lower()
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if termino_busqueda:
                
                cur.execute("""
                    SELECT id_michelin, title, ingredients, steps, chef, 
                           costo_ingredientes, precio_venta_sugerido, alergenos, url_imagen_plato
                    FROM michelin 
                    WHERE (
                        title ILIKE %s OR
                        ingredients ILIKE %s
                    )
                    ORDER BY title
                """, (
                    f'%{termino_busqueda}%',
                    f'%{termino_busqueda}%'
                ))
            else:
               
                cur.execute("""
                    SELECT id_michelin, title, ingredients, steps, chef, 
                           costo_ingredientes, precio_venta_sugerido, alergenos, url_imagen_plato
                    FROM michelin 
                    ORDER BY title
                """)
            
            recetas = cur.fetchall()
            
            recetas_json = []
            for receta in recetas:
                recetas_json.append({
                    'id_michelin': receta[0],
                    'title': receta[1],
                    'ingredients': receta[2] or '',
                    'steps': receta[3] or '',
                    'chef': receta[4] or 'Chef Especializado',
                    'costo_ingredientes': receta[5] or 'N/A',
                    'precio_venta_sugerido': receta[6] or 'N/A',
                    'alergenos': receta[7] or 'Sin alergenos identificados',
                    'url_imagen_plato': receta[8] or ''
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en búsqueda Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()


@app.route('/buscar_recetas_michelin_palabra')
def buscar_recetas_michelin_palabra():
    termino_busqueda = request.args.get('q', '').strip().lower()
    
    if not termino_busqueda:
        return jsonify({'recetas': []})
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            
            cur.execute("""
                SELECT id_michelin, title, ingredients, steps, chef, 
                       costo_ingredientes, precio_venta_sugerido, alergenos, url_imagen_plato
                FROM michelin 
                WHERE (
                    title ILIKE %s OR      -- Al inicio de la frase
                    title ILIKE %s OR      -- Al final de la frase  
                    title ILIKE %s OR      -- En medio de la frase
                    title ILIKE %s OR      -- Exactamente igual
                    title ILIKE %s         -- Después de un guión/parentesis
                )
                ORDER BY title
            """, (
                f'{termino_busqueda} %',
                f'% {termino_busqueda}',
                f'% {termino_busqueda} %',
                termino_busqueda,
                f'%({termino_busqueda} %'
            ))
            
            recetas = cur.fetchall()
            
            
            recetas_json = []
            for receta in recetas:
                recetas_json.append({
                    'id_michelin': receta[0],
                    'title': receta[1],
                    'ingredients': receta[2] or '',
                    'steps': receta[3] or '',
                    'chef': receta[4] or 'Chef Especializado',
                    'costo_ingredientes': receta[5] or 'N/A',
                    'precio_venta_sugerido': receta[6] or 'N/A',
                    'alergenos': receta[7] or 'Sin alergenos identificados',
                    'url_imagen_plato': receta[8] or ''
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en búsqueda por palabra Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()

@app.route('/buscar_michelin_por_ingredientes')
def buscar_michelin_por_ingredientes():
    ingredientes = request.args.get('ingredientes', '').strip().lower()
    
    if not ingredientes:
        return jsonify({'recetas': []})
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            
            lista_ingredientes = [ing.strip() for ing in ingredientes.split(',') if ing.strip()]
            total_ingredientes_busqueda = len(lista_ingredientes)
            
            
            cur.execute("""
                SELECT id_michelin, title, ingredients, steps, chef, 
                       costo_ingredientes, precio_venta_sugerido, alergenos, url_imagen_plato
                FROM michelin 
            """)
            
            todas_recetas = cur.fetchall()
            
        
            recetas_rankeadas = []
            
            for receta in todas_recetas:
                id_michelin, title, ingredients, steps, chef, costo, precio, alergenos, url_imagen = receta
                
                if ingredients:
                    
                    ingredientes_receta = [ing.strip().lower() for ing in ingredients.split('\n') if ing.strip()]
                    
                    
                    coincidencias = calcular_coincidencias(ingredientes_receta, lista_ingredientes)
                    
                    if coincidencias['total_coincidencias'] > 0:
                        porcentaje_coincidencia = (coincidencias['total_coincidencias'] / total_ingredientes_busqueda) * 100
                        
                        recetas_rankeadas.append({
                            'id_michelin': id_michelin,
                            'title': title,
                            'ingredients': ingredients,
                            'steps': steps,
                            'chef': chef or 'Chef Especializado',
                            'costo_ingredientes': costo or 'N/A',
                            'precio_venta_sugerido': precio or 'N/A',
                            'alergenos': alergenos or 'Sin alergenos identificados',
                            'url_imagen_plato': url_imagen or '',
                            'match_percentage': porcentaje_coincidencia,
                            'matched_ingredients': coincidencias['ingredientes_coincidentes'],
                            'total_search_ingredients': total_ingredientes_busqueda,
                            'matched_count': coincidencias['total_coincidencias']
                        })
            
           
            recetas_rankeadas.sort(key=lambda x: x['match_percentage'], reverse=True)
            
            return jsonify({'recetas': recetas_rankeadas})
            
    except Exception as e:
        print(f"Error en búsqueda por ingredientes Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()

        
@app.route('/get_recetas_michelin')
def get_recetas_michelin():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id_michelin, title, ingredients, steps, chef, 
                       costo_ingredientes, precio_venta_sugerido, alergenos, 
                       url_imagen_plato, categoria_michelin, plato_uuid
                FROM michelin 
                ORDER BY title
            """)
            
            recetas = cur.fetchall()
            
            
            recetas_json = []
            for receta in recetas:
                recetas_json.append({
                    'id_michelin': receta[0],
                    'title': receta[1],
                    'ingredients': receta[2] or '',
                    'steps': receta[3] or '',
                    'chef': receta[4] or 'Chef Especializado',
                    'costo_ingredientes': float(receta[5]) if receta[5] else 0,
                    'precio_venta_sugerido': float(receta[6]) if receta[6] else 0,
                    'alergenos': receta[7] or 'Sin alergenos identificados',
                    'url_imagen_plato': receta[8] or '',
                    'categoria_michelin': receta[9] or '',
                    'plato_uuid': receta[10] or ''
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en get_recetas_michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()
        
def buscar_recetas_api():
    termino_busqueda = request.args.get('q', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if categoria and not termino_busqueda:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria, imagen_filename  -- 🔥 AGREGADO
                    FROM recetas 
                    WHERE LOWER(categoria) = LOWER(%s)
                    ORDER BY title
                """, (categoria,))
            elif termino_busqueda:
                if categoria:
                    cur.execute("""
                        SELECT id, title, url, ingredients, steps, categoria, imagen_filename  -- 🔥 AGREGADO
                        FROM recetas 
                        WHERE (
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s
                        ) AND LOWER(categoria) = LOWER(%s)
                        ORDER BY title
                    """, (
                        f'{termino_busqueda} %',
                        f'% {termino_busqueda}',
                        f'% {termino_busqueda} %',
                        termino_busqueda,
                        f'%({termino_busqueda} %',
                        categoria
                    ))
                else:
                    cur.execute("""
                        SELECT id, title, url, ingredients, steps, categoria, imagen_filename  -- 🔥 AGREGADO
                        FROM recetas 
                        WHERE (
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s OR
                            title ILIKE %s
                        )
                        ORDER BY title
                    """, (
                        f'{termino_busqueda} %',
                        f'% {termino_busqueda}',
                        f'% {termino_busqueda} %',
                        termino_busqueda,
                        f'%({termino_busqueda} %'
                    ))
            else:
               
                return jsonify({'recetas': []})
            
            recetas = cur.fetchall()
            
            
            recetas_json = []
            for receta in recetas:
                recetas_json.append({
                    'id': receta[0],
                    'title': receta[1],
                    'imagen': receta[2],
                    'ingredients': receta[3] or '',
                    'steps': receta[4] or '',
                    'categoria': receta[5],
                    'imagen_filename': receta[6]
                })
            
            return jsonify({'recetas': recetas_json})
            
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'recetas': []})
    finally:
        conn.close()

def buscar_por_ingredientes_api():
    ingredientes = request.args.get('ingredientes', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    if not ingredientes:
        return jsonify({'recetas': []})
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
           
            lista_ingredientes = [ing.strip() for ing in ingredientes.split(',') if ing.strip()]
            total_ingredientes_busqueda = len(lista_ingredientes)
            
            if categoria:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria, imagen_filename
                    FROM recetas 
                    WHERE LOWER(categoria) = LOWER(%s)
                """, (categoria,))
            else:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria, imagen_filename
                    FROM recetas
                """)
            
            todas_recetas = cur.fetchall()
            
            
            recetas_rankeadas = []
            
            for receta in todas_recetas:
                
                id_receta, title, url, ingredients, steps, cat, imagen_filename = receta
                
                if ingredients:
                    
                    ingredientes_receta = [ing.strip().lower() for ing in ingredients.split('\n') if ing.strip()]
                    
                   
                    coincidencias = calcular_coincidencias(ingredientes_receta, lista_ingredientes)
                    
                    if coincidencias['total_coincidencias'] > 0:
                        porcentaje_coincidencia = (coincidencias['total_coincidencias'] / total_ingredientes_busqueda) * 100
                        
                        
                        recetas_rankeadas.append({
                            'id': id_receta,
                            'title': title,
                            'imagen_filename': f"/static/imagenes_recetas/{imagen_filename}" if imagen_filename else '',  
                            'ingredients': ingredients,
                            'steps': steps,
                            'categoria': cat,
                            'match_percentage': porcentaje_coincidencia,
                            'matched_ingredients': coincidencias['ingredientes_coincidentes'],
                            'total_search_ingredients': total_ingredientes_busqueda,
                            'matched_count': coincidencias['total_coincidencias']
                        })
            
            
            recetas_rankeadas.sort(key=lambda x: x['match_percentage'], reverse=True)
            
            return jsonify({'recetas': recetas_rankeadas})
            
    except Exception as e:
        print(f"Error en búsqueda por ingredientes: {e}")
        import traceback
        traceback.print_exc()  
        return jsonify({'recetas': []})
    finally:
        conn.close()



def calcular_coincidencias(ingredientes_receta, ingredientes_busqueda):
    coincidencias = 0
    ingredientes_coincidentes = []
    
    for ing_busqueda in ingredientes_busqueda:
        for ing_receta in ingredientes_receta:
            if es_coincidencia_con_plurales(ing_receta, ing_busqueda):
                coincidencias += 1
                ingredientes_coincidentes.append(ing_receta)
                break
    
    return {
        'total_coincidencias': coincidencias,
        'ingredientes_coincidentes': ingredientes_coincidentes
    }

def es_coincidencia_con_plurales(ingrediente_receta, ingrediente_busqueda):
    
    ing_receta_limpio = limpiar_ingrediente(ingrediente_receta)
    ing_busqueda_limpio = limpiar_ingrediente(ingrediente_busqueda)
    
    
    if ing_receta_limpio == ing_busqueda_limpio:
        return True
    
    
    palabras_receta = ing_receta_limpio.split()
    if ing_busqueda_limpio in palabras_receta:
        return True
    
    
    if es_coincidencia_plural(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    
    if es_coincidencia_estricta(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    return False

def es_coincidencia_plural(ing_receta, ing_busqueda):
    
    plurales = {
        'mango': ['mangos'],
        'fresa': ['fresas'],
        'limón': ['limones', 'limon', 'limons'],
        'naranja': ['naranjas'],
        'manzana': ['manzanas'],
        'plátano': ['plátanos', 'banana', 'bananas'],
        'piña': ['piñas'],
        'uva': ['uvas'],
        'sandía': ['sandías', 'sandias'],
        'melón': ['melones', 'melon'],
        'fructosa': ['fructosas'],
        'cereza': ['cerezas'],
        'frambuesa': ['frambuesas'],
        'arándano': ['arándanos'],
        'mora': ['moras'],
        'durazno': ['duraznos'],
        'ciruela': ['ciruelas']
    }
    
    
    if ing_busqueda in plurales:
        for plural in plurales[ing_busqueda]:
            if plural in ing_receta:
                return True
    
    
    for singular, plurales_lista in plurales.items():
        if ing_busqueda in plurales_lista and singular in ing_receta:
            return True
    
    return False

def limpiar_ingrediente(ingrediente):
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

def es_coincidencia_estricta(ing_receta, ing_busqueda):
    
    coincidencias_estrictas = {
        'leche': ['leche'],
        'azúcar': ['azúcar', 'azucar'],
        'menta': ['menta', 'hierbabuena'],
        'canela': ['canela'],
        'jengibre': ['jengibre'],
        'miel': ['miel'],
        'agua': ['agua'],
        'hielo': ['hielo'],
        'yogur': ['yogur', 'yogurt'],
        'chocolate': ['chocolate'],
        'coco': ['coco'],
        'vainilla': ['vainilla'],
        'almendra': ['almendra'],
        'nuez': ['nuez'],
        'avena': ['avena']
    }
    
    if ing_busqueda in coincidencias_estrictas:
        return any(term in ing_receta for term in coincidencias_estrictas[ing_busqueda])
    
    return False

if __name__ == '__main__':
    app.run(debug=True)