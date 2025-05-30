from generador_inventario_directo import verificar_coherencia_valores
import sys
import traceback

if __name__ == "__main__":
    try:
        # Obtener el año de los argumentos de línea de comandos
        if len(sys.argv) > 1:
            año = int(sys.argv[1])
        else:
            año = int(input("Ingrese el año para verificar y corregir los movimientos: "))
            
        if año < 1900 or año > 2100:
            raise ValueError("El año debe estar entre 1900 y 2100")
        
        print(f"\nIniciando verificación y corrección de valores para el año {año}...")
        
        # Verificar y corregir cada mes
        for mes in range(1, 13):
            print(f"\nVerificando mes {mes:02d}/{año}...")
            verificar_coherencia_valores(año, mes)
        
        print(f"\nVerficación y corrección completada para el año {año}.")
        
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error durante la verificación: {str(e)}")
        print("Detalles del error:")
        traceback.print_exc() 