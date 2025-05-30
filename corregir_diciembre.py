from generador_inventario_directo import get_connection
import sys
import traceback

def corregir_inicial_diciembre(año):
    """
    Corrige específicamente el valor inicial de diciembre para que sea
    exactamente igual al valor final de noviembre.
    
    Args:
        año (int): Año a corregir
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Obtener el valor final de noviembre
        periodo_noviembre = f"11/{año}"
        cursor.execute("""
            SELECT Final
            FROM InventarioContable
            WHERE Periodo = ?
        """, (periodo_noviembre,))
        
        row = cursor.fetchone()
        if not row:
            print(f"Error: No se encontró el período {periodo_noviembre} en InventarioContable.")
            conn.close()
            return False
        
        valor_final_noviembre = float(row[0])
        print(f"Valor final de noviembre {año}: {valor_final_noviembre:.2f}")
        
        # 2. Obtener valores actuales de diciembre
        periodo_diciembre = f"12/{año}"
        cursor.execute("""
            SELECT Inicial, Final
            FROM InventarioContable
            WHERE Periodo = ?
        """, (periodo_diciembre,))
        
        row = cursor.fetchone()
        if not row:
            print(f"Error: No se encontró el período {periodo_diciembre} en InventarioContable.")
            conn.close()
            return False
        
        valor_inicial_diciembre = float(row[0])
        valor_final_diciembre = float(row[1])
        
        print(f"Valores actuales de diciembre {año}:")
        print(f"  Inicial: {valor_inicial_diciembre:.2f}")
        print(f"  Final: {valor_final_diciembre:.2f}")
        
        # 3. Actualizar el valor inicial de diciembre si es necesario
        if abs(valor_inicial_diciembre - valor_final_noviembre) > 0.01:
            print(f"Corrigiendo valor inicial de diciembre {año}...")
            
            # Actualizar en InventarioContable
            cursor.execute("""
                UPDATE InventarioContable
                SET Inicial = ?
                WHERE Periodo = ?
            """, (valor_final_noviembre, periodo_diciembre))
            
            print(f"  Valor inicial de diciembre actualizado a: {valor_final_noviembre:.2f}")
            
            # 4. Verificar si existe el registro 0000000001 en diciembre
            cursor.execute("""
                SELECT COUNT(*)
                FROM MovInventMes
                WHERE Periodo = ? AND Codigo = '0000000001'
            """, (periodo_diciembre,))
            
            if cursor.fetchone()[0] > 0:
                # Actualizar el campo Costo en MovInventMes
                cursor.execute("""
                    UPDATE MovInventMes
                    SET Costo = ?
                    WHERE Periodo = ? AND Codigo = '0000000001'
                """, (valor_final_noviembre, periodo_diciembre))
                
                print(f"  Campo Costo del registro 0000000001 actualizado a: {valor_final_noviembre:.2f}")
            else:
                print(f"  No se encontró el registro 0000000001 para diciembre {año}.")
            
            conn.commit()
            print(f"Actualización completada.")
        else:
            print(f"El valor inicial de diciembre ya es correcto (igual al final de noviembre).")
        
        # 5. Actualizar el valor inicial de enero del siguiente año si existe
        siguiente_año = año + 1
        periodo_enero_siguiente = f"01/{siguiente_año}"
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM InventarioContable
            WHERE Periodo = ?
        """, (periodo_enero_siguiente,))
        
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                UPDATE InventarioContable
                SET Inicial = ?
                WHERE Periodo = ?
            """, (valor_final_diciembre, periodo_enero_siguiente))
            
            print(f"Valor inicial de enero {siguiente_año} actualizado a: {valor_final_diciembre:.2f} (final de diciembre {año})")
            conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error al corregir valor inicial de diciembre {año}: {str(e)}")
        traceback.print_exc()
        
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        
        return False

if __name__ == "__main__":
    try:
        # Obtener el año de los argumentos de línea de comandos
        if len(sys.argv) > 1:
            año = int(sys.argv[1])
        else:
            año = int(input("Ingrese el año para corregir diciembre: "))
            
        if año < 1900 or año > 2100:
            raise ValueError("El año debe estar entre 1900 y 2100")
        
        print(f"\nCorrigiendo valor inicial de diciembre {año}...")
        corregir_inicial_diciembre(año)
        print("\nProceso completado.")
        
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error durante la corrección: {str(e)}")
        traceback.print_exc() 