from flask import jsonify, request, render_template

def buscar_recetas_api(mysql):
    termino_busqueda = request.args.get('q', '').strip().lower()
    
    if not termino_busqueda:
        return jsonify({'recetas': []})
    
    cur = mysql.connection.cursor()
    
    try:
        # 🔥 CAMBIO: Buscar por palabras completas en el título
        # Usamos REGEXP con límites de palabra \\b para buscar palabras completas
        cur.execute("""
            SELECT id, title, url, ingredients, steps, categoria 
            FROM recetas 
            WHERE title REGEXP %s
            ORDER BY title
        """, (f'\\b{termino_busqueda}\\b',))
        
        recetas = cur.fetchall()
        
        # Si no hay resultados con palabras completas, buscar coincidencias parciales como fallback
        if not recetas:
            cur.execute("""
                SELECT id, title, url, ingredients, steps, categoria 
                FROM recetas 
                WHERE LOWER(title) LIKE LOWER(%s) 
                ORDER BY title
            """, (f'%{termino_busqueda}%',))
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