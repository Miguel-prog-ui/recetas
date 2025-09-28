from flask import render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

def logout():
    session.pop('usuario', None)
    return redirect('/')

def crear_cuenta(mysql):
    usuario = request.form['txt_usuario']
    correo = request.form['txt_correo']
    password = generate_password_hash(request.form['txt_password'])

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
    existe = cur.fetchone()
    if existe:
        return render_template('login.html', mensaje_malo='Este correo ya está registrado')

    cur.execute("INSERT INTO usuarios (usuario, correo, password) VALUES (%s, %s, %s)", (usuario, correo, password))
    mysql.connection.commit()
    cur.close()

    return render_template('login.html', mensaje='Cuenta creada exitosamente')

def acceso_login(mysql):
    correo = request.form['txt_correo']
    password = request.form['txt_password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, password FROM usuarios WHERE correo = %s", (correo,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        session['usuario'] = user[1]
        return redirect('/')
    else:
        return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')