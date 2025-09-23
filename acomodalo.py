import pandas as pd
import re

# Cargar el archivo CSV
df = pd.read_csv('parentesis.csv')

# Identificar la tercera columna por posición (índice 2)
columna_objetivo = df.columns[2]

# Función para insertar salto de línea después de cada ')'
def insertar_salto_linea(texto):
    if pd.isna(texto):
        return texto
    return re.sub(r'\)(?!\n)', r')\n', str(texto))

# Aplicar la transformación solo a la tercera columna
df[columna_objetivo] = df[columna_objetivo].apply(insertar_salto_linea)

# Guardar el resultado
df.to_csv('parentesis_modificado.csv', index=False)
