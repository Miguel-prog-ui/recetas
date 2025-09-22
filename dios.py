from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

def cargar_recetas():
    conexion = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='recetas'
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT title, url, ingredients, steps, uuid FROM recetas")
    recetas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return recetas

@app.route('/', methods=['GET', 'POST'])
def mostrar_recetas():
    recetas = cargar_recetas()
    ingredientes = ''
    if request.method == 'POST':
        ingredientes = request.form.get('ingredientes', '').lower()
        lista_ingredientes = [i.strip() for i in ingredientes.split(',') if i.strip()]
        recetas = [
            r for r in recetas
            if all(ing in r['ingredients'].lower() for ing in lista_ingredientes)
        ]
    return render_template('recetas.html', recetas=recetas, ingredientes=ingredientes)

if __name__ == '__main__':
    app.run(debug=True)
