from flask import render_template, request, session, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import re
import uuid

DB_CONFIG = {
    "host": "localhost",
    "user": "moya_user", 
    "password": "moya123",
    "database": "recetas_db",
    "client_encoding": "UTF8"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

def logout():
    session.pop('usuario', None)
    session.pop('tipo_usuario', None)
    return redirect('/')

def crear_cuenta():
    """Función para crear cuenta - CON VALIDACIÓN DE DUPLICADOS Y LÍMITES DE CARACTERES"""
    try:
        usuario = request.form['txt_usuario'].strip()
        correo = request.form['txt_correo'].strip().lower()
        password = request.form['txt_password']
        
        print(f"📝 Intentando crear cuenta: {usuario}, {correo}")
        
       
        if len(usuario) < 3 or len(usuario) > 20:
            return render_template('login.html', 
                mensaje_malo='El nombre de usuario debe tener entre 3 y 20 caracteres')
        
     
        if not re.match(r'^[a-zA-Z0-9_-]+$', usuario):
            return render_template('login.html', 
                mensaje_malo='El nombre de usuario solo puede contener letras, números, guiones y guiones bajos')
        
        
        if len(correo) > 20:
            return render_template('login.html', 
                mensaje_malo='El correo no puede exceder los 20 caracteres')
        
       
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            return render_template('login.html', 
                mensaje_malo='Formato de correo electrónico inválido')
        
       
        if len(password) < 6 or len(password) > 20:
            return render_template('login.html', 
                mensaje_malo='La contraseña debe tener entre 6 y 20 caracteres')
        
       
        if not any(char.isdigit() for char in password):
            return render_template('login.html', 
                mensaje_malo='La contraseña debe contener al menos un número')
        
        if not any(char.isalpha() for char in password):
            return render_template('login.html', 
                mensaje_malo='La contraseña debe contener al menos una letra')

        conn = get_db_connection()
        with conn.cursor() as cur:
            
            cur.execute("SELECT usuario FROM usuarios WHERE usuario = %s", (usuario,))
            usuario_existente = cur.fetchone()
            
            if usuario_existente:
                conn.close()
                return render_template('login.html', 
                    mensaje_malo=f'❌ El nombre de usuario "{usuario}" ya está en uso. Por favor elige otro.')
            
            
            cur.execute("SELECT correo FROM usuarios WHERE correo = %s", (correo,))
            correo_existente = cur.fetchone()
            
            if correo_existente:
                conn.close()
                return render_template('login.html', 
                    mensaje_malo=f'❌ El correo "{correo}" ya está registrado. ¿Olvidaste tu contraseña?')
            
            user_uuid = str(uuid.uuid4())
            print(f"🆔 UUID generado: {user_uuid}")
        
            password_hash = generate_password_hash(password)
            
           
            cur.execute(
                "INSERT INTO usuarios (usuario, correo, password, tipo, user_uuid) VALUES (%s, %s, %s, %s, %s)", 
                (usuario, correo, password_hash, 'usuario', user_uuid)  # AGREGADO user_uuid
            )
            conn.commit()
            
            print(f"✅ Cuenta creada exitosamente: {usuario}")
        
        conn.close()
        
        return render_template('login.html', 
            mensaje=f'✅ ¡Cuenta creada exitosamente! Bienvenido/a {usuario}')
            
    except Exception as e:
        print(f"❌ Error creando cuenta: {e}")
        import traceback
        traceback.print_exc()
        return render_template('login.html', 
            mensaje_malo='Error del servidor al crear la cuenta')

def acceso_login():
    """Función para login - CON VALIDACIÓN DE CARACTERES"""
    try:
        correo = request.form['txt_correo'].strip().lower()
        password = request.form['txt_password']
        
        # Validaciones básicas
        if len(correo) > 20:
            return render_template('login.html', 
                mensaje_malo='Correo electrónico demasiado largo')
        
        if len(password) > 20:
            return render_template('login.html', 
                mensaje_malo='Contraseña demasiado larga')

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, usuario, password, tipo, user_uuid FROM usuarios WHERE correo = %s", (correo,))
            user = cur.fetchone()

        if user and check_password_hash(user[2], password):
            session['usuario'] = user[1]
            session['tipo_usuario'] = user[3]  
            session['user_uuid'] = user[4] 
            
            if user[3] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/')
        else:
            return render_template('login.html', 
                mensaje_malo='Correo o contraseña incorrectos')
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        import traceback
        traceback.print_exc()
        return render_template('login.html', 
            mensaje_malo='Error en el servidor')
    finally:
        conn.close()