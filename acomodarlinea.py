import pandas as pd
import re

def insertar_saltos(texto):
    # Detectar rangos de paréntesis
    rangos_parentesis = [m.span() for m in re.finditer(r'\([^)]*\)', texto)]

    # Buscar secuencias numéricas válidas: 1, 10, 1/2, ½, ¼, etc.
    patron = r'(?<!\d)(\d+(?:/\d+)?|½|¼|⅓)(?!\d)'
    coincidencias = list(re.finditer(patron, texto))

    # Filtrar las coincidencias que NO estén dentro de paréntesis
    coincidencias_validas = []
    for match in coincidencias:
        idx = match.start()
        if not any(start <= idx < end for start, end in rangos_parentesis):
            coincidencias_validas.append(match)

    if len(coincidencias_validas) <= 1:
        return texto  # No hay más de una válida, no se modifica

    # Insertar saltos de línea antes de la segunda coincidencia válida en adelante
    partes = []
    inicio = 0
    for i, match in enumerate(coincidencias_validas):
        if i == 0:
            continue  # Ignorar la primera válida
        idx = match.start()
        partes.append(texto[inicio:idx])
        inicio = idx
    partes.append(texto[inicio:])
    return '\n'.join([p.strip() for p in partes])



# Cargar el CSV
df = pd.read_csv('apt3.csv')
df.columns = df.columns.str.strip().str.lower()

# Aplicar transformación si 'ingredients' está presente
if 'ingredients' in df.columns:
    df['ingredients'] = df['ingredients'].astype(str).apply(insertar_saltos)
    df.to_csv('recetas_formateadas3.csv', index=False)
    print("Archivo exportado como recetas_formateadas1.csv")
else:
    print("La columna 'ingredients' no fue encontrada.")
