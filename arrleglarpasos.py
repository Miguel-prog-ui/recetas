import pandas as pd
import re

def insertar_saltos(texto):
    # Detectar rangos de paréntesis
    rangos_parentesis = [m.span() for m in re.finditer(r'\([^)]*\)', texto)]

    # Palabras que anulan el salto si siguen al número
    excepciones = ['segundo', 'segundos', 'minuto', 'minutos', 'hora', 'horas']

    # Buscar secuencias numéricas válidas
    patron = r'(?<!\d)(\d+(?:/\d+)?|½|¼)(?!\d)'
    coincidencias = list(re.finditer(patron, texto))

    # Filtrar coincidencias válidas (fuera de paréntesis y no seguidas por excepciones)
    coincidencias_validas = []
    for match in coincidencias:
        idx = match.start()
        if any(start <= idx < end for start, end in rangos_parentesis):
            continue  # Está dentro de paréntesis

        # Verificar si después del número viene una palabra de excepción
        after = texto[match.end():].lstrip().lower()
        if any(after.startswith(palabra) for palabra in excepciones):
            continue  # Está seguido por una palabra que anula el salto

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
df = pd.read_csv('full.csv')
df.columns = df.columns.str.strip().str.lower()

# Aplicar transformación a la columna 'steps'
if 'steps' in df.columns:
    df['steps'] = df['steps'].astype(str).apply(insertar_saltos)
    df.to_csv('recetas_steps_formateadasAYUDA.csv', index=False)
    print("Archivo exportado como recetas_steps_formateadas.csv")
else:
    print("La columna 'steps' no fue encontrada.")
