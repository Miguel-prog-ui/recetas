from flask import jsonify, request

def buscar_recetas_michelin(mysql):
    """Búsqueda específica para recetas Michelin"""
    termino_busqueda = request.args.get('q', '').strip().lower()
    
    cur = mysql.connection.cursor()
    
    try:
        # Buscar en la tabla michelin específicamente
        if termino_busqueda:
            cur.execute("""
                SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                       categoria_michelin, chef, fotochefURL, costo_ingredientes,
                       precio_venta_sugerido, alergenos, url_imagen_plato
                FROM michelin 
                WHERE (
                    title LIKE %s OR
                    title LIKE %s OR
                    title LIKE %s OR
                    ingredients LIKE %s OR
                    chef LIKE %s
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
            # Si no hay término, devolver todas las recetas Michelin
            cur.execute("""
                SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                       categoria_michelin, chef, fotochefURL, costo_ingredientes,
                       precio_venta_sugerido, alergenos, url_imagen_plato
                FROM michelin 
                ORDER BY title
            """)
        
        recetas = cur.fetchall()
        
        # Convertir a formato JSON
        recetas_json = []
        for receta in recetas:
            recetas_json.append({
                'id': receta[0],  # id_michelin
                'plato_uuid': receta[1],
                'title': receta[2],
                'ingredients': receta[3] or '',
                'steps': receta[4] or '',
                'imagen': receta[5] or receta[12] or '',  # url_receta o url_imagen_plato
                'categoria': receta[6] or 'alta_cocina',  # categoria_michelin
                'chef': receta[7] or '',
                'fotochefURL': receta[8] or '',
                'costo_ingredientes': receta[9] or '',
                'precio_venta_sugerido': receta[10] or '',
                'alergenos': receta[11] or ''
            })
        
        return jsonify({'recetas': recetas_json})
        
    except Exception as e:
        print(f"Error en búsqueda Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        cur.close()

def buscar_michelin_ingredientes(mysql):
    """Búsqueda por ingredientes específica para recetas Michelin"""
    ingredientes = request.args.get('ingredientes', '').strip().lower()
    
    if not ingredientes:
        return jsonify({'recetas': []})
    
    cur = mysql.connection.cursor()
    
    try:
        # Dividir ingredientes por comas
        lista_ingredientes = [ing.strip() for ing in ingredientes.split(',') if ing.strip()]
        total_ingredientes_busqueda = len(lista_ingredientes)
        
        # Obtener todas las recetas Michelin
        cur.execute("""
            SELECT id_michelin, plato_uuid, title, ingredients, steps, url_receta, 
                   categoria_michelin, chef, fotochefURL, costo_ingredientes,
                   precio_venta_sugerido, alergenos, url_imagen_plato
            FROM michelin 
        """)
        
        todas_recetas = cur.fetchall()
        
        # Procesar y rankear recetas por coincidencia de ingredientes
        recetas_rankeadas = []
        
        for receta in todas_recetas:
            id_michelin, plato_uuid, title, ingredients, steps, url_receta, categoria_michelin, chef, fotochefURL, costo_ingredientes, precio_venta_sugerido, alergenos, url_imagen_plato = receta
            
            if ingredients:
                # Convertir ingredientes a lista
                ingredientes_receta = [ing.strip().lower() for ing in ingredients.split('\n') if ing.strip()]
                
                # Calcular coincidencias
                coincidencias = calcular_coincidencias_michelin(ingredientes_receta, lista_ingredientes)
                
                if coincidencias['total_coincidencias'] > 0:
                    porcentaje_coincidencia = (coincidencias['total_coincidencias'] / total_ingredientes_busqueda) * 100
                    
                    recetas_rankeadas.append({
                        'id': id_michelin,
                        'plato_uuid': plato_uuid,
                        'title': title,
                        'imagen': url_receta or url_imagen_plato or '',
                        'ingredients': ingredients,
                        'steps': steps or '',
                        'categoria': categoria_michelin or 'alta_cocina',
                        'chef': chef or '',
                        'fotochefURL': fotochefURL or '',
                        'costo_ingredientes': costo_ingredientes or '',
                        'precio_venta_sugerido': precio_venta_sugerido or '',
                        'alergenos': alergenos or '',
                        'match_percentage': porcentaje_coincidencia,
                        'matched_ingredients': coincidencias['ingredientes_coincidentes'],
                        'total_search_ingredients': total_ingredientes_busqueda,
                        'matched_count': coincidencias['total_coincidencias']
                    })
        
        # Ordenar por porcentaje de coincidencia (mayor primero)
        recetas_rankeadas.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return jsonify({'recetas': recetas_rankeadas})
        
    except Exception as e:
        print(f"Error en búsqueda por ingredientes Michelin: {e}")
        return jsonify({'recetas': []})
    finally:
        cur.close()

def obtener_estadisticas(mysql):
    """Obtener estadísticas de las recetas en la base de datos"""
    cur = mysql.connection.cursor()
    
    try:
        # Contar recetas por categoría
        cur.execute("""
            SELECT categoria, COUNT(*) as cantidad 
            FROM recetas 
            GROUP BY categoria
        """)
        stats_recetas = cur.fetchall()
        
        # Contar recetas Michelin
        cur.execute("SELECT COUNT(*) FROM michelin")
        total_michelin = cur.fetchone()[0]
        
        # Contar chefs únicos en Michelin
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
        cur.close()

# Funciones auxiliares para Michelin - MEJORADAS
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
        
        # Si no se encontró coincidencia exacta, buscar coincidencias parciales
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
    
    # 1. Coincidencia exacta
    if ing_receta_limpio == ing_busqueda_limpio:
        return True
    
    # 2. Coincidencia de palabra exacta
    palabras_receta = ing_receta_limpio.split()
    if ing_busqueda_limpio in palabras_receta:
        return True
    
    # 3. Coincidencia con plurales
    if es_coincidencia_plural(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    # 4. Coincidencia estricta para ingredientes gourmet
    if es_coincidencia_estricta_michelin(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    # 5. Coincidencia parcial (último recurso)
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
    
    # Si el término de búsqueda está en singular, buscar también en plural
    if ing_busqueda in plurales:
        for plural in plurales[ing_busqueda]:
            if plural in ing_receta:
                return True
    
    # Si el término de búsqueda está en plural, buscar también en singular
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