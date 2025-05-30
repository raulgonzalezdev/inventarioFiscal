from generador_inventario import generar_año_completo
import sys
import traceback

if __name__ == "__main__":
    try:
        # Obtener el año de los argumentos de línea de comandos
        if len(sys.argv) > 1:
            año = int(sys.argv[1])
        else:
            año = int(input("Ingrese el año para generar los movimientos: "))
            
        if año < 1900 or año > 2100:
            raise ValueError("El año debe estar entre 1900 y 2100")
            
        print(f"Iniciando generación de movimientos para {año}...")
        generar_año_completo(año)
        print("Generación completada.")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error durante la generación: {str(e)}")
        print("Detalles del error:")
        traceback.print_exc() 