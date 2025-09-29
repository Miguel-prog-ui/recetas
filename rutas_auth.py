from flask import render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

def logout():
    session.pop('usuario', None)
    session.pop('tipo_usuario', None)
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

    cur.execute("INSERT INTO usuarios (usuario, correo, password, tipo) VALUES (%s, %s, %s, %s)", 
                (usuario, correo, password, ''))
    mysql.connection.commit()
    cur.close()

    return render_template('login.html', mensaje='Cuenta creada exitosamente')

def acceso_login(mysql):
    correo = request.form['txt_correo']
    password = request.form['txt_password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, password, tipo FROM usuarios WHERE correo = %s", (correo,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        session['usuario'] = user[1]
        session['tipo_usuario'] = user[3]  # Guardar el tipo de usuario en la sesión
        
        # Redirigir según el tipo de usuario
        if user[3] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/')
    else:
        return render_template('login.html', mensaje_malo='Correo o contraseña incorrectos')