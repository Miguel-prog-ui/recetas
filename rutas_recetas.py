from flask import jsonify, request, render_template

def buscar_recetas_palabra_api(mysql):
    termino_busqueda = request.args.get('q', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    if not termino_busqueda:
        return jsonify({'recetas': []})
    
    cur = mysql.connection.cursor()
    
    try:
        # 🔥 BÚSQUEDA POR PALABRA COMPLETA (MEJORADO)
        if categoria:
            cur.execute("""
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
                WHERE (
                    title LIKE %s OR      -- Al inicio de la frase
                    title LIKE %s OR      -- Al final de la frase
                    title LIKE %s OR      -- En medio de la frase
                    title = %s OR         -- Exactamente igual
                    title LIKE %s         -- Después de un guión/parentesis
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
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
                WHERE (
                    title LIKE %s OR      -- Al inicio de la frase
                    title LIKE %s OR      -- Al final de la frase
                    title LIKE %s OR      -- En medio de la frase
                    title = %s OR         -- Exactamente igual
                    title LIKE %s         -- Después de un guión/parentesis
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
        
        # Convertir a formato JSON
        recetas_json = []
        for receta in recetas:
            recetas_json.append({
                'id': receta[0],
                'title': receta[1],
                'imagen': receta[2],
                'ingredients': receta[3] or '',
                'steps': receta[4] or '',
                'categoria': receta[5]
            })
        
        return jsonify({'recetas': recetas_json})
        
    except Exception as e:
        print(f"Error en búsqueda por palabra: {e}")
        return jsonify({'recetas': []})
    finally:
        cur.close()

def buscar_recetas_api(mysql):
    termino_busqueda = request.args.get('q', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    cur = mysql.connection.cursor()
    
    try:
        if categoria and not termino_busqueda:
            # 🔥 BUSCAR SOLO POR CATEGORÍA
            cur.execute("""
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
                WHERE LOWER(categoria) = LOWER(%s)
                ORDER BY title
            """, (categoria,))
        elif termino_busqueda:
            # 🔥 BUSCAR POR PALABRA COMPLETA Y CATEGORÍA
            if categoria:
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria 
                    FROM recetas 
                    WHERE (
                        title LIKE %s OR
                        title LIKE %s OR
                        title LIKE %s OR
                        title = %s OR
                        title LIKE %s
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
                # Búsqueda por palabra completa
                cur.execute("""
                    SELECT id, title, url, ingredients, steps, categoria 
                    FROM recetas 
                    WHERE (
                        title LIKE %s OR
                        title LIKE %s OR
                        title LIKE %s OR
                        title = %s OR
                        title LIKE %s
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
            # Si no hay término ni categoría, devolver vacío
            return jsonify({'recetas': []})
        
        recetas = cur.fetchall()
        
        # Convertir a formato JSON
        recetas_json = []
        for receta in recetas:
            recetas_json.append({
                'id': receta[0],
                'title': receta[1],
                'imagen': receta[2],
                'ingredients': receta[3] or '',
                'steps': receta[4] or '',
                'categoria': receta[5]
            })
        
        return jsonify({'recetas': recetas_json})
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'recetas': []})
    finally:
        cur.close()

def buscar_por_ingredientes_api(mysql):
    ingredientes = request.args.get('ingredientes', '').strip().lower()
    categoria = request.args.get('categoria', '').strip().lower()
    
    if not ingredientes:
        return jsonify({'recetas': []})
    
    cur = mysql.connection.cursor()
    
    try:
        # Dividir ingredientes por comas
        lista_ingredientes = [ing.strip() for ing in ingredientes.split(',') if ing.strip()]
        total_ingredientes_busqueda = len(lista_ingredientes)
        
        if categoria:
            # Obtener todas las recetas de la categoría
            cur.execute("""
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
                WHERE LOWER(categoria) = LOWER(%s)
            """, (categoria,))
        else:
            # Obtener todas las recetas
            cur.execute("""
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
            """)
        
        todas_recetas = cur.fetchall()
        
        # Procesar y rankear recetas por coincidencia de ingredientes
        recetas_rankeadas = []
        
        for receta in todas_recetas:
            id_receta, title, url, ingredients, steps, cat = receta
            
            if ingredients:
                # Convertir ingredientes a lista
                ingredientes_receta = [ing.strip().lower() for ing in ingredients.split('\n') if ing.strip()]
                
                # Calcular coincidencias
                coincidencias = calcular_coincidencias(ingredientes_receta, lista_ingredientes)
                
                if coincidencias['total_coincidencias'] > 0:
                    porcentaje_coincidencia = (coincidencias['total_coincidencias'] / total_ingredientes_busqueda) * 100
                    
                    recetas_rankeadas.append({
                        'id': id_receta,
                        'title': title,
                        'imagen': url,
                        'ingredients': ingredients,
                        'steps': steps,
                        'categoria': cat,
                        'match_percentage': porcentaje_coincidencia,
                        'matched_ingredients': coincidencias['ingredientes_coincidentes'],
                        'total_search_ingredients': total_ingredientes_busqueda,
                        'matched_count': coincidencias['total_coincidencias']
                    })
        
        # Ordenar por porcentaje de coincidencia (mayor primero)
        recetas_rankeadas.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return jsonify({'recetas': recetas_rankeadas})
        
    except Exception as e:
        print(f"Error en búsqueda por ingredientes: {e}")
        return jsonify({'recetas': []})
    finally:
        cur.close()

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
    # Limpiar ingredientes
    ing_receta_limpio = limpiar_ingrediente(ingrediente_receta)
    ing_busqueda_limpio = limpiar_ingrediente(ingrediente_busqueda)
    
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
    
    # 4. Coincidencia estricta (evitar falsos positivos)
    if es_coincidencia_estricta(ing_receta_limpio, ing_busqueda_limpio):
        return True
    
    return False

def es_coincidencia_plural(ing_receta, ing_busqueda):
    # Detectar plurales comunes
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
    # Solo coincidencias muy específicas para evitar falsos positivos
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