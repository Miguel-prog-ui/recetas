import requests
import json

def test_obtener_recetas_comunidad():
    """Prueba la ruta para obtener recetas de la comunidad"""
    try:
        response = requests.get('http://localhost:5005/obtener_recetas_comunidad')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recetas obtenidas: {len(data.get('recetas', []))}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_agregar_receta_comunidad():
    """Prueba la ruta para agregar una receta de la comunidad"""
    try:
        # Datos de prueba
        test_data = {
            'recipeName': 'Test Recipe',
            'recipeType': 'comida',
            'recipeIngredients': 'Ingrediente 1\nIngrediente 2\nIngrediente 3',
            'recipeInstructions': 'Paso 1\nPaso 2\nPaso 3',
            'recipeDifficulty': 'Fácil',
            'recipeTime': '15 min',
            'recipeDescription': 'Esta es una receta de prueba'
        }
        
        response = requests.post('http://localhost:5005/agregar_receta_comunidad', data=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Receta agregada: {data.get('message')}")
                return True
            else:
                print(f"❌ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de funcionalidad de comunidad...")
    print("=" * 50)
    
    print("\n1. Probando obtener recetas de la comunidad...")
    test1 = test_obtener_recetas_comunidad()
    
    print("\n2. Probando agregar receta de la comunidad...")
    test2 = test_agregar_receta_comunidad()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("✅ Todas las pruebas pasaron correctamente!")
    else:
        print("❌ Algunas pruebas fallaron. Revisa los errores arriba.")
