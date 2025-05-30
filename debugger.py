from generador_inventario import generar_movimientos, obtener_datos_periodo
import traceback

def probar_mes(año, mes):
    """Prueba la generación de movimientos para un mes específico"""
    try:
        print(f"\nProbando mes {mes}/{año}...")
        
        # Verificar datos del período
        periodo = f"{mes:02d}/{año}"
        datos_periodo = obtener_datos_periodo(periodo)
        if datos_periodo is None:
            print(f"Error: No existe el período {periodo}")
            return None
            
        print(f"Datos período: {datos_periodo}")
        
        # Generar movimientos
        movimientos = generar_movimientos(año, mes)
        
        if movimientos:
            print(f"Éxito! Se generaron {len(movimientos)} movimientos")
            return movimientos
        else:
            print("No se pudieron generar movimientos")
            return None
            
    except Exception as e:
        print(f"Error durante la prueba del mes {mes}: {str(e)}")
        traceback.print_exc()
        return None

def probar_generacion_año(año):
    """Prueba la generación para todos los meses del año"""
    print(f"Probando generación para el año {año}")
    
    for mes in range(1, 13):
        movimientos = probar_mes(año, mes)
        if not movimientos:
            print(f"❌ Error en mes {mes}")
            break
        else:
            print(f"✅ Éxito en mes {mes}")

if __name__ == "__main__":
    # Probar la generación para el año 2024
    probar_generacion_año(2024) 