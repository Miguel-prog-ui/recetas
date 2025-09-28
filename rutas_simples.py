from flask import render_template

# Aquí van TODAS las funciones que solo renderizan templates
def mostrar_presentacion():
    return render_template('presentacion.html')

def mostrar_bebidas():
    return render_template('bebidas.html')

def mostrar_bebidas_alcoholicas():
    return render_template('bebidas_alcoholicas.html')

def mostrar_postres():
    return render_template('postres.html')

def mostrar_comidas():
    return render_template('comidas.html')

def mostrar_alta_cocina():
    return render_template('alta_cocina.html')

def mostrar_login():
    return render_template('login.html')