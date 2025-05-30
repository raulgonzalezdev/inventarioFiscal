from generador_inventario_directo import generar_año_directo, inicializar_periodos_año
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
        
        # Valores específicos para 2024
        if año == 2024:
            VALOR_INICIAL_2024 = 1120797.03  # Final de 2023
            VALOR_FINAL_2024 = 1892903.00    # Final de 2024
            
            print(f"Iniciando generación de movimientos para {año}...")
            print(f"Valor inicial enero: {VALOR_INICIAL_2024}")
            print(f"Valor final diciembre: {VALOR_FINAL_2024}")
            print(f"Diferencia anual: {VALOR_FINAL_2024 - VALOR_INICIAL_2024:.2f}")
            
            # Primero inicializar los valores de los periodos
            print("\nInicializando períodos para distribución de valores...")
            inicializar_periodos_año(año, VALOR_INICIAL_2024, VALOR_FINAL_2024)
            
            # Luego generar los movimientos
            generar_año_directo(año, VALOR_INICIAL_2024, VALOR_FINAL_2024)
        else:
            # Para otros años, usar valores default
            print(f"Iniciando generación de movimientos para {año}...")
            generar_año_directo(año)
            
        print("Generación completada con éxito.")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error durante la generación: {str(e)}")
        print("Detalles del error:")
        traceback.print_exc() 