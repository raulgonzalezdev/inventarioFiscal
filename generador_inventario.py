import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import random
import calendar
import numpy as np

# Configuración de la conexión a SQL Server
def get_connection():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=DELLXEONE31545\\SQLEXPRESS;"
        "DATABASE=DatqBoxExpress;"
        "UID=sa;"
        "PWD=e!334011"
    )
    return pyodbc.connect(conn_str)

def get_dias_habiles(año, mes):
    """Obtiene los días hábiles (lunes a sábado) del mes especificado"""
    primer_dia = datetime(año, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(año + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(año, mes + 1, 1) - timedelta(days=1)
    
    dias_habiles = []
    dia_actual = primer_dia
    
    while dia_actual <= ultimo_dia:
        if dia_actual.weekday() != 6:  # 6 = domingo
            dias_habiles.append(dia_actual)
        dia_actual += timedelta(days=1)
    
    return dias_habiles

def obtener_datos_inventario():
    """Obtiene los productos del inventario de forma segura"""
    try:
        conn = get_connection()
        query = """
        SELECT CODIGO, DESCRIPCION, PRECIO_COMPRA, PRECIO_VENTA, EXISTENCIA
        FROM Inventario
        WHERE EXISTENCIA > 0
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convertir a una lista de diccionarios para evitar problemas con Series
        productos = []
        for _, row in df.iterrows():
            try:
                producto = {
                    'CODIGO': str(row['CODIGO']).strip(),
                    'DESCRIPCION': str(row['DESCRIPCION']).strip() if 'DESCRIPCION' in row else "",
                    'PRECIO_COMPRA': float(row['PRECIO_COMPRA']) if not pd.isna(row['PRECIO_COMPRA']) else 0.0,
                    'PRECIO_VENTA': float(row['PRECIO_VENTA']) if not pd.isna(row['PRECIO_VENTA']) else 0.0,
                    'EXISTENCIA': int(row['EXISTENCIA']) if not pd.isna(row['EXISTENCIA']) else 0
                }
                productos.append(producto)
            except Exception as e:
                print(f"Error al procesar producto: {str(e)}")
                continue
                
        return productos
    except Exception as e:
        print(f"Error al obtener datos del inventario: {str(e)}")
        return []

def obtener_datos_periodo(periodo):
    """Obtiene los datos del período de InventarioContable"""
    conn = get_connection()
    query = f"""
    SELECT Inicial, Final, AjusteCompras, AjusteVentas
    FROM InventarioContable
    WHERE Periodo = '{periodo}'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def actualizar_periodo(periodo, inicial=None, final=None):
    """Actualiza los valores de un período existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if inicial is not None and final is not None:
        cursor.execute("""
            UPDATE InventarioContable
            SET Inicial = ?, Final = ?
            WHERE Periodo = ?
        """, (inicial, final, periodo))
    elif inicial is not None:
        cursor.execute("""
            UPDATE InventarioContable
            SET Inicial = ?
            WHERE Periodo = ?
        """, (inicial, periodo))
    elif final is not None:
        cursor.execute("""
            UPDATE InventarioContable
            SET Final = ?
            WHERE Periodo = ?
        """, (final, periodo))
    
    conn.commit()
    conn.close()

def insertar_periodo(periodo, descripcion, inicial, final):
    """Inserta un nuevo período en InventarioContable"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO InventarioContable (Periodo, Descripcion, Inicial, Final, AjusteCompras, AjusteVentas)
        VALUES (?, ?, ?, ?, 0, 0)
    """, (periodo, descripcion, inicial, final))
    
    conn.commit()
    conn.close()

def obtener_valores_año(año):
    """Obtiene los valores inicial y final del año desde InventarioContable"""
    print("DEBUG: Entrando a obtener_valores_año")
    # Obtener valor inicial (enero)
    periodo_enero = f"01/{año}"
    try:
        datos_enero = obtener_datos_periodo(periodo_enero)
        if datos_enero is None:
            print(f"Error: No se encontró el período inicial {periodo_enero} en InventarioContable")
            return None, None

        # Obtener valor final (diciembre)
        periodo_diciembre = f"12/{año}"
        datos_diciembre = obtener_datos_periodo(periodo_diciembre)
        if datos_diciembre is None:
            print(f"Error: No se encontró el período final {periodo_diciembre} en InventarioContable")
            return None, None

        print(f"DEBUG: Valores de año {año} - Inicial: {datos_enero['Inicial']}, Final: {datos_diciembre['Final']}")
        return datos_enero['Inicial'], datos_diciembre['Final']
    except Exception as e:
        print(f"ERROR en obtener_valores_año: {str(e)}")
        return None, None

def calcular_valor_final_mes(mes, año, valor_inicial):
    """Calcula un valor final razonable para el mes"""
    # Obtener el valor final objetivo de diciembre desde la tabla
    _, valor_final_diciembre = obtener_valores_año(año)
    if valor_final_diciembre is None:
        print(f"Error: No se pudo obtener el valor final de diciembre {año}")
        return None

    if mes == 12:
        # Para diciembre, usamos el valor de la tabla
        return valor_final_diciembre
    else:
        # Calculamos un incremento que nos lleve progresivamente hacia el valor de diciembre
        meses_restantes = 12 - mes
        valor_objetivo = valor_final_diciembre
        
        # Calculamos un factor de crecimiento mensual promedio necesario
        factor_crecimiento = (valor_objetivo / valor_inicial) ** (1 / meses_restantes)
        
        # Añadimos una variación aleatoria al factor (±5% del incremento para más control)
        variacion = random.uniform(0.95, 1.05)
        factor_final = 1 + ((factor_crecimiento - 1) * variacion)
        
        return round(valor_inicial * factor_final, 2)

def calcular_distribucion_montos(valor_inicial, valor_final, num_dias):
    """Calcula la distribución de montos para llegar del valor inicial al final"""
    # Si el valor inicial es 0, establecemos un valor mínimo para evitar división por cero
    if valor_inicial == 0:
        valor_inicial = 0.01  # Usar un valor mínimo positivo
    
    diferencia = valor_final - valor_inicial
    # Calculamos un factor de progresión logarítmico para que el crecimiento sea más natural
    if num_dias > 1:
        factor_diario = (valor_final / valor_inicial) ** (1.0 / (num_dias - 1))
    else:
        factor_diario = valor_final / valor_inicial
    
    valores_diarios = []
    valor_actual = valor_inicial
    
    for _ in range(num_dias):
        valores_diarios.append(valor_actual)
        valor_actual *= factor_diario
    
    # Ajustamos el último valor para asegurar que llegue exactamente al valor final
    valores_diarios[-1] = valor_final
    
    return valores_diarios

def limitar_valor_float(valor):
    """Limita un valor float para que esté dentro de los límites seguros de SQL Server"""
    # SQL Server float tiene un rango de -1.79E+308 a 1.79E+308
    MAX_FLOAT = 1.79e+308
    MIN_FLOAT = -1.79e+308
    
    if valor is None:
        return 0.0
    try:
        valor_float = float(valor)
        if valor_float > MAX_FLOAT:
            return MAX_FLOAT
        if valor_float < MIN_FLOAT:
            return MIN_FLOAT
        # Redondear a 2 decimales para evitar problemas de precisión
        return round(valor_float, 2)
    except:
        return 0.0

def obtener_precios_promedio():
    """Obtiene los precios promedio de cada producto"""
    conn = get_connection()
    query = """
    SELECT CODIGO, 
           AVG(PRECIO_COMPRA) as PRECIO_COMPRA_PROMEDIO,
           AVG(PRECIO_VENTA) as PRECIO_VENTA_PROMEDIO
    FROM Inventario
    WHERE EXISTENCIA > 0
    GROUP BY CODIGO
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    precios_promedio = {}
    for _, row in df.iterrows():
        precios_promedio[str(row['CODIGO'])] = {
            'compra': float(row['PRECIO_COMPRA_PROMEDIO']),
            'venta': float(row['PRECIO_VENTA_PROMEDIO'])
        }
    return precios_promedio

def calcular_totales_movimientos(movimientos):
    """Calcula los totales de los movimientos y verifica la consistencia"""
    try:
        total_inicial = 0
        total_entradas = 0
        total_salidas = 0
        
        # Agrupar movimientos por producto (convertimos a diccionarios simples)
        for mov in movimientos:
            codigo = mov.get('Codigo', '')
            
            # Tratar el registro de inventario inicial de forma especial
            if codigo == '0000000001' and mov.get('Motivo') == "INVENTARIO INICIAL MES ANTERIOR":
                total_inicial = float(mov['Precio_Compra'])
            # El código 0000000002 es para ajustes y se procesa normalmente según su tipo
            elif codigo != '0000000001' and mov.get('Tipo') == "Ingreso":
                # Es un ingreso normal o un ajuste de ingreso
                monto = float(mov['Precio_Compra']) * float(mov['Cantidad'])
                # Limitar montos extremadamente grandes
                monto = min(monto, 50000)
                total_entradas += monto
            elif codigo != '0000000001' and mov.get('Tipo') == "Egreso":
                # Es un egreso normal o un ajuste de egreso
                monto = float(mov['Precio_venta']) * float(mov['Cantidad'])
                # Limitar montos extremadamente grandes
                monto = min(monto, 50000)
                total_salidas += monto
        
        # Asegurar que no haya valores negativos
        total_inicial = max(0, total_inicial)
        total_entradas = max(0, total_entradas)
        total_salidas = max(0, total_salidas)
        
        # Calcular el total final
        total_final = total_inicial + total_entradas - total_salidas
        
        # Asegurar que el valor final no sea negativo
        total_final = max(0, total_final)
        
        return {
            'inicial': limitar_valor_float(total_inicial),
            'entradas': limitar_valor_float(total_entradas),
            'salidas': limitar_valor_float(total_salidas),
            'final': limitar_valor_float(total_final)
        }
    except Exception as e:
        print(f"Error en calcular_totales_movimientos: {str(e)}")
        return {'inicial': 0, 'entradas': 0, 'salidas': 0, 'final': 0}

def actualizar_inventario_contable(periodo, totales):
    """Actualiza la tabla InventarioContable con los totales calculados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE InventarioContable
            SET Inicial = ?,
                Final = ?
            WHERE Periodo = ?
        """, (totales['inicial'], totales['final'], periodo))
        
        conn.commit()
        print(f"\nInventarioContable actualizado para {periodo}:")
        print(f"Inicial: {totales['inicial']:.2f}")
        print(f"Final: {totales['final']:.2f}")
        
    except Exception as e:
        print(f"Error al actualizar InventarioContable: {str(e)}")
    finally:
        conn.close()

def generar_movimientos(año, mes):
    """
    Genera movimientos para un mes específico.
    
    Args:
        año (int): El año para el cual generar movimientos
        mes (int): El mes para el cual generar movimientos (1-12)
        
    Returns:
        list: Lista de movimientos generados, o None en caso de error
    """
    try:
        año = int(año)  # Asegurar que el año sea un entero
        mes = int(mes)  # Asegurar que el mes sea un entero
    except ValueError:
        print("Error: El año y el mes deben ser números enteros válidos")
        return None
        
    periodo = f"{mes:02d}/{año}"
    datos_periodo = obtener_datos_periodo(periodo)
    
    if datos_periodo is None:
        print(f"Error: No se encontró el período {periodo}")
        return None
    
    # Manejar valor inicial para enero (debe ser el final de diciembre del año anterior)
    if mes == 1:
        periodo_diciembre_anterior = f"12/{año-1}"
        datos_diciembre_anterior = obtener_datos_periodo(periodo_diciembre_anterior)
        
        if datos_diciembre_anterior is not None:
            valor_inicial = limitar_valor_float(datos_diciembre_anterior['Final'])
            # Actualizar el valor inicial en InventarioContable para mantener coherencia
            actualizar_periodo(periodo, inicial=valor_inicial)
            print(f"Actualizando valor inicial de {periodo} para que sea igual al final de {periodo_diciembre_anterior}")
        else:
            # Si no hay datos de diciembre del año anterior, usar el valor de la tabla
            valor_inicial = limitar_valor_float(datos_periodo['Inicial'])
            print(f"Advertencia: No se encontró período {periodo_diciembre_anterior}, usando valor inicial de tabla")
    else:
        # Para los demás meses, usar el valor inicial de la tabla
        valor_inicial = limitar_valor_float(datos_periodo['Inicial'])
    
    valor_final_objetivo = limitar_valor_float(datos_periodo['Final'])
    
    print(f"\nGenerando movimientos para {periodo}")
    print(f"Valor inicial: {valor_inicial:.2f}")
    print(f"Valor final objetivo: {valor_final_objetivo:.2f}")
    
    # Si es diciembre, asegurarnos de que el valor final sea respetado exactamente
    if mes == 12:
        print("Mes de diciembre: se respetará el valor final de referencia exactamente.")
    
    # Verificar que los valores sean válidos
    if valor_inicial < 0:
        print(f"Error: Valor inicial negativo detectado en {periodo}")
        return None
        
    if valor_final_objetivo < 0:
        print(f"Error: Valor final negativo detectado en {periodo}")
        return None
    
    # Obtener productos del inventario
    productos_lista = obtener_datos_inventario()
    if not productos_lista:
        print("Error: No hay productos en el inventario")
        return None
        
    # Obtener días hábiles
    dias_habiles = get_dias_habiles(año, mes)
    if not dias_habiles:
        print(f"Error: No hay días hábiles para {periodo}")
        return None
    
    # Verificar si ya existe un movimiento inicial para este período
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM MovInvent 
        WHERE (
            (Product = '0000000001' AND Motivo = 'INVENTARIO INICIAL MES ANTERIOR')
            OR
            (Product = '0000000002' AND Motivo = 'Ajuste de Inventario')
        )
        AND YEAR(Fecha) = ? AND MONTH(Fecha) = ?
    """, (año, mes))
    
    movimientos_existentes = cursor.fetchone()[0] > 0
    conn.close()
    
    # Generar movimientos
    movimientos = []
    
    # Agregar registro de inventario inicial solo si no existen movimientos
    if not movimientos_existentes:
        primer_dia = dias_habiles[0]
        movimiento_inicial = {
            'Product': '0000000001',
            'Fecha': primer_dia,
            'Tipo': "Ingreso",
            'Motivo': "INVENTARIO INICIAL MES ANTERIOR",
            'Cantidad_Actual': 0,
            'Cantidad': 1,
            'Co_Usuario': 'SUPERVISOR',
            'Codigo': '0000000001',
            'Precio_Compra': valor_inicial,
            'Precio_venta': valor_inicial,
            'cantidad_nueva': 1,
            'autoriza': None,
            'Documento': "INV-INICIAL",
            'Anulada': 0,
            'Alicuota': 16.0
        }
        movimientos.append(movimiento_inicial)
        print(f"Agregando movimiento inicial con valor {valor_inicial:.2f}")
    else:
        print(f"Movimientos para {periodo} ya existen, no se agregarán nuevamente")
        return []  # Si ya existen movimientos, retornamos una lista vacía
    
    # Diccionario para rastrear inventario
    inventario_actual = {}
    for prod in productos_lista:
        inventario_actual[prod['CODIGO']] = prod['EXISTENCIA']
    
    # Calcular diferencia entre valor inicial y final
    diferencia_total = valor_final_objetivo - valor_inicial
    
    # Determinar si necesitamos principalmente entradas o salidas
    requiere_mas_entradas = diferencia_total > 0
    
    # Calcular valor objetivo final y distribución diaria
    num_dias = len(dias_habiles)
    
    # Incremento diario - puede ser positivo (más entradas) o negativo (más salidas)
    incremento_diario = diferencia_total / num_dias if num_dias > 0 else 0
    
    # Determinar un promedio de precio por producto para evitar valores extremos
    precio_promedio_por_producto = {}
    total_valor_inventario = valor_inicial
    total_productos = sum(inventario_actual.values())
    
    if total_productos > 0:
        valor_promedio_unidad = total_valor_inventario / total_productos
    else:
        valor_promedio_unidad = 100.0  # Valor predeterminado si no hay productos
    
    # Limitar el valor promedio a un rango razonable (entre 5 y 1000)
    valor_promedio_unidad = max(5.0, min(1000.0, valor_promedio_unidad))
    
    for prod in productos_lista:
        # Asignar un precio razonable basado en el precio actual pero limitado
        precio_base = max(5.0, min(500.0, prod['PRECIO_COMPRA']))
        precio_venta_base = precio_base * 1.25  # Margen de 25%
        
        # Guardar estos precios para usarlos consistentemente
        precio_promedio_por_producto[prod['CODIGO']] = {
            'compra': precio_base,
            'venta': precio_venta_base
        }
    
    # Generar movimientos por día
    valor_acumulado = valor_inicial
    
    for i, dia in enumerate(dias_habiles[1:], 1):  # Empezamos desde el segundo día
        valor_objetivo_dia = valor_inicial + (incremento_diario * i)
        
        # Número de movimientos para este día - más controlado
        num_movimientos = min(5, len(productos_lista))
        
        # Seleccionar productos aleatoriamente pero sin repetir en un mismo día
        productos_seleccionados = random.sample(productos_lista, num_movimientos) if len(productos_lista) >= num_movimientos else productos_lista
        
        for producto in productos_seleccionados:
            codigo = producto['CODIGO'][:15]  # Limitar a 15 caracteres
            
            # Determinar si es ingreso o egreso según el objetivo del día
            diferencia_dia = valor_objetivo_dia - valor_acumulado
            es_ingreso = diferencia_dia > 0
            
            # Forzar ingreso si existencia es baja
            if inventario_actual.get(codigo, 0) < 2:
                es_ingreso = True
            
            # O si la tendencia general es de crecimiento (necesitamos más entradas)
            elif requiere_mas_entradas and random.random() < 0.7:  # 70% de probabilidad de ingreso
                es_ingreso = True
            # Si la tendencia es a la baja, favorecer salidas
            elif not requiere_mas_entradas and random.random() < 0.7:  # 70% de probabilidad de salida
                es_ingreso = False
            
            # Obtener el precio base para este producto
            precio_base = precio_promedio_por_producto.get(codigo, {'compra': 10.0, 'venta': 15.0})
            
            if es_ingreso:
                tipo = "Ingreso"
                motivo = "Compra"
                cantidad = random.randint(1, 3)  # Reducir las cantidades
                cantidad_actual = inventario_actual.get(codigo, 0)
                cantidad_nueva = cantidad_actual + cantidad
                
                # Usar el precio base con una pequeña variación
                variacion = random.uniform(0.9, 1.1)  # ±10%
                precio_compra = precio_base['compra'] * variacion
                precio_venta = precio_base['venta'] * variacion
                
                # Calcular el impacto en el valor acumulado
                impacto = precio_compra * cantidad
                
                # Limitar el impacto para evitar picos extremos
                if impacto > 5000:
                    cantidad = max(1, int(5000 / precio_compra))
                    impacto = precio_compra * cantidad
                    cantidad_nueva = cantidad_actual + cantidad
                
                # Actualizar valor acumulado
                valor_acumulado += impacto
            else:
                tipo = "Egreso"
                motivo = "Venta"
                cantidad_actual = inventario_actual.get(codigo, 0)
                
                # Limitar cantidad a existencia disponible
                max_cantidad = min(cantidad_actual, 2)
                if max_cantidad <= 0:
                    continue
                    
                cantidad = random.randint(1, max_cantidad)
                cantidad_nueva = cantidad_actual - cantidad
                
                # Usar el precio base con una pequeña variación
                variacion = random.uniform(0.9, 1.1)  # ±10%
                precio_compra = precio_base['compra'] * variacion
                precio_venta = precio_base['venta'] * variacion
                
                # Calcular el impacto en el valor acumulado
                impacto = precio_venta * cantidad
                
                # Limitar el impacto para evitar picos extremos
                if impacto > 5000:
                    cantidad = max(1, int(5000 / precio_venta))
                    impacto = precio_venta * cantidad
                    cantidad_nueva = cantidad_actual - cantidad
                
                # Actualizar valor acumulado
                valor_acumulado -= impacto
            
            # Asegurar que cantidad_nueva nunca sea negativa
            cantidad_nueva = max(0, cantidad_nueva)
            
            # Actualizar inventario actual
            inventario_actual[codigo] = cantidad_nueva
            
            # Crear movimiento
            movimiento = {
                'Product': codigo,
                'Fecha': dia,
                'Tipo': tipo,
                'Motivo': motivo,
                'Cantidad_Actual': cantidad_actual,
                'Cantidad': cantidad,
                'Co_Usuario': 'SUPERVISOR',
                'Codigo': codigo,
                'Precio_Compra': precio_compra,
                'Precio_venta': precio_venta,
                'cantidad_nueva': cantidad_nueva,
                'autoriza': None,
                'Documento': f"{random.randint(1000, 9999)}-{random.randint(1, 999):03d}",
                'Anulada': 0,
                'Alicuota': 16.0
            }
            
            movimientos.append(movimiento)
            
            # Verificar si hemos alcanzado el objetivo con suficiente precisión
            if abs(valor_acumulado - valor_objetivo_dia) < 50:
                break
    
    # Calcular totales finales
    totales = calcular_totales_movimientos(movimientos)
    
    # Si hay una diferencia significativa entre el valor final calculado y el objetivo,
    # añadir un movimiento de ajuste para que cuadre exactamente
    diferencia_final = valor_final_objetivo - totales['final']
    
    if abs(diferencia_final) > 1:
        print(f"Añadiendo movimiento de ajuste para diferencia de {diferencia_final:.2f}")
        # Determinar si el ajuste debe ser un ingreso o un egreso
        if diferencia_final > 0:
            # Necesitamos añadir un ingreso para aumentar el valor final
            ultimo_dia = dias_habiles[-1]
            movimiento_ajuste = {
                'Product': '0000000002',  # Usamos un código diferente para el ajuste
                'Fecha': ultimo_dia,
                'Tipo': "Ingreso",
                'Motivo': "Ajuste de Inventario",
                'Cantidad_Actual': 1,
                'Cantidad': 1,
                'Co_Usuario': 'SUPERVISOR',
                'Codigo': '0000000002',
                'Precio_Compra': diferencia_final,
                'Precio_venta': diferencia_final,
                'cantidad_nueva': 2,
                'autoriza': None,
                'Documento': "AJUSTE-FINAL",
                'Anulada': 0,
                'Alicuota': 16.0
            }
            movimientos.append(movimiento_ajuste)
        else:
            # Necesitamos añadir un egreso para disminuir el valor final
            ultimo_dia = dias_habiles[-1]
            movimiento_ajuste = {
                'Product': '0000000002',  # Usamos un código diferente para el ajuste
                'Fecha': ultimo_dia,
                'Tipo': "Egreso",
                'Motivo': "Ajuste de Inventario",
                'Cantidad_Actual': 2,
                'Cantidad': 1,
                'Co_Usuario': 'SUPERVISOR',
                'Codigo': '0000000002',
                'Precio_Compra': abs(diferencia_final),
                'Precio_venta': abs(diferencia_final),
                'cantidad_nueva': 1,
                'autoriza': None,
                'Documento': "AJUSTE-FINAL",
                'Anulada': 0,
                'Alicuota': 16.0
            }
            movimientos.append(movimiento_ajuste)
        
        # Recalcular totales después del ajuste
        totales = calcular_totales_movimientos(movimientos)
    
    print(f"Se generaron {len(movimientos)} movimientos para {periodo}")
    print(f"Valor final alcanzado: {totales['final']:.2f}")
    print(f"Valor objetivo: {valor_final_objetivo:.2f}")
    print(f"Diferencia: {(valor_final_objetivo - totales['final']):.2f}")
    
    return movimientos

def insertar_movimientos(movimientos):
    """Inserta los movimientos en la tabla MovInvent"""
    if not movimientos:
        print("No hay movimientos para insertar")
        return
        
    print(f"Intentando insertar {len(movimientos)} movimientos...")
    conn = get_connection()
    cursor = conn.cursor()
    
    movimientos_insertados = 0
    for mov in movimientos:
        try:
            # Convertir la fecha al formato YYYY-MM-DD para SQL Server
            fecha_sql = mov['Fecha'].strftime('%Y-%m-%d')
            
            # Imprimir detalles del movimiento que se va a insertar
            print(f"\nInsertando movimiento:")
            print(f"Product: {mov['Product']}")
            print(f"Fecha: {fecha_sql}")
            print(f"Tipo: {mov['Tipo']}")
            print(f"Motivo: {mov['Motivo']}")
            
            cursor.execute("""
                INSERT INTO MovInvent (
                    Product, Fecha, Tipo, Motivo, Cantidad_Actual,
                    Cantidad, Co_Usuario, Codigo, Precio_Compra,
                    Precio_venta, cantidad_nueva, autoriza,
                    Documento, Anulada, Alicuota
                ) VALUES (
                    ?, CONVERT(datetime, ?, 120), ?, ?, ?, 
                    ?, ?, ?, ?, 
                    ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                mov['Product'], fecha_sql, mov['Tipo'],
                mov['Motivo'], mov['Cantidad_Actual'], mov['Cantidad'],
                mov['Co_Usuario'], mov['Codigo'], mov['Precio_Compra'],
                mov['Precio_venta'], mov['cantidad_nueva'],
                mov['autoriza'], mov['Documento'], mov['Anulada'],
                mov['Alicuota']
            ))
            
            movimientos_insertados += 1
            print("Movimiento insertado correctamente")
            
        except Exception as e:
            print(f"\nError al insertar movimiento: {str(e)}")
            print("Detalles del movimiento que causó el error:")
            for key, value in mov.items():
                print(f"{key}: {value}")
            continue
    
    try:
        conn.commit()
        print(f"\nSe insertaron {movimientos_insertados} de {len(movimientos)} movimientos")
    except Exception as e:
        print(f"Error al hacer commit: {str(e)}")
    finally:
        conn.close()

def obtener_ultimo_periodo_año_anterior(año):
    """Obtiene el último período del año anterior"""
    periodo_diciembre_anterior = f"12/{año-1}"
    return obtener_datos_periodo(periodo_diciembre_anterior)

def crear_periodos_faltantes(año):
    """Crea los períodos faltantes en InventarioContable"""
    print("DEBUG: Entrando a crear_periodos_faltantes")
    try:
        # Obtener el valor inicial del último período del año anterior
        periodo_diciembre_anterior = f"12/{año-1}"
        datos_diciembre_anterior = obtener_datos_periodo(periodo_diciembre_anterior)
        if datos_diciembre_anterior is None:
            print(f"Error: No se encontró el período final del año anterior (12/{año-1})")
            return False
        
        # Obtener los valores inicial y final del año actual
        valor_inicial_año, valor_final_año = obtener_valores_año(año)
        
        print(f"Valor inicial del año {año} (tomado del final de {año-1}): {datos_diciembre_anterior['Final']:.2f}")
        print(f"Valor final del año {año} (tomado de InventarioContable): {valor_final_año:.2f}")

        # Procesar cada mes del año
        valor_actual = datos_diciembre_anterior['Final']  # Comenzamos con el final del año anterior
        for mes in range(1, 13):
            periodo = f"{mes:02d}/{año}"
            nombre_mes = calendar.month_name[mes].upper()
            descripcion = f"{nombre_mes} {año}"
            
            datos_mes = obtener_datos_periodo(periodo)
            if datos_mes is not None:
                print(f"El período {periodo} ya existe - Inicial: {datos_mes['Inicial']:.2f}, Final: {datos_mes['Final']:.2f}")
                # No modificamos los valores existentes
                valor_actual = datos_mes['Final']
                continue
                
            # Para diciembre, usamos el valor final predefinido
            if mes == 12:
                valor_final = valor_final_año
            else:
                # Calculamos un valor final progresivo para los meses intermedios
                valor_final = valor_actual * 1.05  # Incremento del 5% mensual
            
            try:
                # Insertar el período con el valor inicial y final calculado
                insertar_periodo(periodo, descripcion, valor_actual, valor_final)
                print(f"Período creado: {periodo} - Inicial: {valor_actual:.2f}, Final: {valor_final:.2f}")
                
                # El valor final de este mes será el inicial del siguiente
                valor_actual = valor_final
                
            except Exception as e:
                print(f"Error al crear período {periodo}: {str(e)}")
                return False
        
        return True
    except Exception as e:
        print(f"ERROR en crear_periodos_faltantes: {str(e)}")
        return False

def actualizar_valor_inicial_mes(año, mes, valor_inicial):
    """Actualiza solo el valor inicial de un mes"""
    try:
        periodo = f"{mes:02d}/{año}"
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE InventarioContable
                SET Inicial = ?
                WHERE Periodo = ?
            """, (valor_inicial, periodo))
            
            conn.commit()
            print(f"Actualizado valor inicial de {periodo} a {valor_inicial:.2f}")
        except Exception as e:
            print(f"Error SQL al actualizar valor inicial de {periodo}: {str(e)}")
        finally:
            conn.close()
    except Exception as e:
        print(f"Error en actualizar_valor_inicial_mes: {str(e)}")
        
def actualizar_valor_final_mes(año, mes, valor_final):
    """Actualiza el valor final de un mes (excepto diciembre)"""
    if mes == 12:
        print("No se puede actualizar el valor final de diciembre")
        return
    
    try:    
        periodo = f"{mes:02d}/{año}"
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE InventarioContable
                SET Final = ?
                WHERE Periodo = ?
            """, (valor_final, periodo))
            
            # Actualizar el valor inicial del siguiente mes
            siguiente_mes = 1
            siguiente_año = año
            if mes < 12:
                siguiente_mes = mes + 1
            else:
                siguiente_mes = 1
                siguiente_año = año + 1
                
            siguiente_periodo = f"{siguiente_mes:02d}/{siguiente_año}"
            cursor.execute("""
                UPDATE InventarioContable
                SET Inicial = ?
                WHERE Periodo = ?
            """, (valor_final, siguiente_periodo))
            
            conn.commit()
            print(f"Actualizado valor final de {periodo} a {valor_final:.2f}")
            print(f"Actualizado valor inicial de {siguiente_periodo} a {valor_final:.2f}")
        except Exception as e:
            print(f"Error SQL al actualizar valores: {str(e)}")
        finally:
            conn.close()
    except Exception as e:
        print(f"Error en actualizar_valor_final_mes: {str(e)}")

def procesar_movimientos_inventario(periodo, desde, hasta):
    """
    Implementa la lógica del SP directamente en Python para procesar los movimientos
    y preparar los datos para el informe, garantizando consistencia.
    
    Args:
        periodo (str): Período en formato MM/AAAA
        desde (datetime): Fecha de inicio del período
        hasta (datetime): Fecha de fin del período
    
    Returns:
        bool: True si se procesó correctamente, False en caso de error
    """
    try:
        print(f"Procesando movimientos de inventario para período {periodo}...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. LIMPIEZA INICIAL
        
        # Eliminar registros de servicios (mantener solo productos físicos)
        cursor.execute("""
            DELETE m
            FROM dbo.MovInvent m
            INNER JOIN dbo.Inventario i ON m.Product = i.CODIGO
            WHERE i.Linea = N'SERVICIO' AND m.Fecha BETWEEN ? AND ?
        """, (desde, hasta))
        
        # Corregir valores negativos
        cursor.execute("""
            UPDATE MovInvent 
            SET CANTIDAD_ACTUAL = 0 
            WHERE CANTIDAD_ACTUAL < 0 AND Fecha BETWEEN ? AND ?
        """, (desde, hasta))
        
        # 2. OBTENER VALORES DE INVENTARIO
        
        # Extraer mes y año del período
        mes_actual = int(periodo[:2])
        año_actual = int(periodo[3:])
        
        # Determinar el período anterior
        if mes_actual == 1:
            periodo_anterior = f"12/{año_actual - 1}"
        else:
            periodo_anterior = f"{mes_actual - 1:02d}/{año_actual}"
        
        # Obtener valor inicial y final del período actual
        cursor.execute("""
            SELECT Inicial, Final
            FROM InventarioContable
            WHERE Periodo = ?
        """, (periodo,))
        
        row = cursor.fetchone()
        if not row:
            print(f"Error: No se encontró el período {periodo} en InventarioContable")
            conn.close()
            return False
            
        inventario_inicial = float(row[0])
        inventario_final = float(row[1])
        
        # Para diciembre, destacar que utilizamos el valor final exacto de referencia
        if mes_actual == 12:
            print(f"Procesando diciembre: Utilizando valor final de referencia: {inventario_final:.2f}")
        
        # Para enero, asegurar que el valor inicial sea el final del período anterior
        if mes_actual == 1:
            cursor.execute("""
                SELECT Final
                FROM InventarioContable
                WHERE Periodo = ?
            """, (periodo_anterior,))
            
            row = cursor.fetchone()
            if row:
                valor_final_anterior = float(row[0])
                inventario_inicial = valor_final_anterior
                
                # Actualizar el valor inicial en InventarioContable
                cursor.execute("""
                    UPDATE InventarioContable
                    SET Inicial = ?
                    WHERE Periodo = ?
                """, (inventario_inicial, periodo))
            
        # Calcular diferencia
        diferencia_inventario = inventario_final - inventario_inicial
        
        # 3. VERIFICAR SI YA EXISTE EL REGISTRO DE INVENTARIO INICIAL
        cursor.execute("""
            SELECT COUNT(*)
            FROM MovInvent
            WHERE Product = '0000000001' 
              AND Motivo = 'INVENTARIO INICIAL MES ANTERIOR'
              AND Fecha BETWEEN ? AND ?
        """, (desde, hasta))
        
        registro_inicial_existe = cursor.fetchone()[0] > 0
        
        # 4. LIMPIAR TABLA DE RESULTADOS
        cursor.execute("DELETE FROM MovInventMes WHERE Periodo = ?", (periodo,))
        
        # 5. PROCESAR DATOS DEL INVENTARIO
        
        # Crear registro para el inventario inicial en MovInventMes - solo uno por período
        # Aseguramos explícitamente que Entradas, Salidas, AutoConsumo y Retiros sean cero
        cursor.execute("""
            INSERT INTO MovInventMes (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros, final, Fecha)
            VALUES (?, '0000000001', ?, ?, 'INVENTARIO INICIAL MES ANTERIOR', 0, 0, 0, 0, ?, ?)
        """, (periodo, inventario_inicial, inventario_inicial, inventario_inicial, desde))
        
        # 6. CALCULAR Y AGRUPAR MOVIMIENTOS EXISTENTES
        
        # Obtener movimientos agrupados por producto y tipo
        cursor.execute("""
            SELECT 
                m.Product,
                SUM(CASE WHEN m.Tipo = 'Ingreso' THEN m.Cantidad ELSE 0 END) AS Entradas,
                SUM(CASE WHEN m.Tipo = 'Ingreso' THEN m.Cantidad * m.Precio_Compra ELSE 0 END) AS EntradasValor,
                SUM(CASE WHEN m.Tipo = 'Egreso' THEN m.Cantidad ELSE 0 END) AS Salidas,
                SUM(CASE WHEN m.Tipo = 'Egreso' THEN m.Cantidad * m.Precio_venta ELSE 0 END) AS SalidasValor,
                SUM(CASE WHEN m.Tipo = 'Consumo' THEN m.Cantidad ELSE 0 END) AS Autoconsumo,
                SUM(CASE WHEN m.Tipo = 'Consumo' THEN m.Cantidad * m.Precio_Compra ELSE 0 END) AS AutoconsumoValor,
                SUM(CASE WHEN m.Tipo = 'Retiro' THEN m.Cantidad ELSE 0 END) AS Retiros,
                SUM(CASE WHEN m.Tipo = 'Retiro' THEN m.Cantidad * m.Precio_Compra ELSE 0 END) AS RetirosValor
            FROM MovInvent m
            WHERE m.Fecha BETWEEN ? AND ? AND m.Anulada = 0
            GROUP BY m.Product
        """, (desde, hasta))
        
        movimientos_producto = {}
        for row in cursor.fetchall():
            codigo = row[0]
            movimientos_producto[codigo] = {
                'entradas': float(row[1]) if row[1] is not None else 0.0,
                'entradas_valor': float(row[2]) if row[2] is not None else 0.0,
                'salidas': float(row[3]) if row[3] is not None else 0.0,
                'salidas_valor': float(row[4]) if row[4] is not None else 0.0,
                'autoconsumo': float(row[5]) if row[5] is not None else 0.0,
                'autoconsumo_valor': float(row[6]) if row[6] is not None else 0.0,
                'retiros': float(row[7]) if row[7] is not None else 0.0,
                'retiros_valor': float(row[8]) if row[8] is not None else 0.0
            }
        
        # 7. INSERTAR PRODUCTOS CON SUS MOVIMIENTOS
        
        # Obtener todos los productos con movimientos
        cursor.execute("""
            SELECT DISTINCT i.CODIGO, i.COSTO_REFERENCIA, 
                  i.CATEGORIA + ' ' + i.TIPO + ' ' + i.DESCRIPCION + ' ' + i.MARCA AS Descripciones
            FROM Inventario i
            INNER JOIN MovInvent m ON i.CODIGO = m.Product
            WHERE m.Fecha BETWEEN ? AND ? AND m.Anulada = 0 
            AND i.CODIGO NOT IN ('0000000001', '0000000002')
        """, (desde, hasta))
        
        for row in cursor.fetchall():
            codigo = row[0]
            costo = float(row[1]) if row[1] is not None else 0.0
            descripcion = row[2]
            
            mov = movimientos_producto.get(codigo, {
                'entradas': 0, 'salidas': 0, 'autoconsumo': 0, 'retiros': 0
            })
            
            cursor.execute("""
                INSERT INTO MovInventMes (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros, Fecha)
                VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
            """, (
                periodo, 
                codigo, 
                costo, 
                descripcion, 
                mov.get('entradas', 0),
                mov.get('salidas', 0),
                mov.get('autoconsumo', 0),
                mov.get('retiros', 0),
                desde
            ))
        
        # 8. CALCULAR TOTALES DE VALORES
        total_entradas = 0
        total_salidas = 0
        total_autoconsumo = 0
        total_retiros = 0
        
        for _, mov in movimientos_producto.items():
            total_entradas += mov.get('entradas_valor', 0)
            total_salidas += mov.get('salidas_valor', 0)
            total_autoconsumo += mov.get('autoconsumo_valor', 0)
            total_retiros += mov.get('retiros_valor', 0)
        
        # 9. VERIFICAR SI NECESITAMOS AJUSTAR ENTRADAS O SALIDAS PARA CUADRAR
        
        # Calcular el valor final teórico
        valor_final_calculado = inventario_inicial + total_entradas - total_salidas - total_autoconsumo - total_retiros
        
        # Si la diferencia es mayor a 1, ajustar
        if abs(valor_final_calculado - inventario_final) > 1:
            print(f"Ajustando valores para cuadrar: valor calculado = {valor_final_calculado:.2f}, valor objetivo = {inventario_final:.2f}")
            
            # En lugar de ajustar entradas/salidas en el registro 0000000001, 
            # creamos o actualizamos un registro de ajuste separado
            if valor_final_calculado < inventario_final:
                # Necesitamos aumentar entradas - lo hacemos con un registro de ajuste
                entradas_adicionales = inventario_final - valor_final_calculado
                
                # Verificar si existe un registro de ajuste
                cursor.execute("""
                    SELECT COUNT(*) FROM MovInventMes 
                    WHERE Periodo = ? AND Codigo = '0000000002'
                """, (periodo,))
                
                tiene_ajuste = cursor.fetchone()[0] > 0
                
                if tiene_ajuste:
                    # Actualizar el registro de ajuste existente
                    cursor.execute("""
                        UPDATE MovInventMes
                        SET Entradas = ?, Salidas = 0,
                            final = inicial + ?
                        WHERE Periodo = ? AND Codigo = '0000000002'
                    """, (entradas_adicionales, entradas_adicionales, periodo))
                else:
                    # Crear un nuevo registro de ajuste
                    cursor.execute("""
                        INSERT INTO MovInventMes 
                        (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros, final, Fecha)
                        VALUES (?, '0000000002', 0, ?, 'AJUSTE DE INVENTARIO', ?, 0, 0, 0, ?, ?)
                    """, (periodo, entradas_adicionales, entradas_adicionales, entradas_adicionales, hasta))
                
                print(f"Añadiendo entradas adicionales al registro de ajuste: {entradas_adicionales:.2f}")
            else:
                # Necesitamos aumentar salidas - lo hacemos con un registro de ajuste
                salidas_adicionales = valor_final_calculado - inventario_final
                
                # Verificar si existe un registro de ajuste
                cursor.execute("""
                    SELECT COUNT(*) FROM MovInventMes 
                    WHERE Periodo = ? AND Codigo = '0000000002'
                """, (periodo,))
                
                tiene_ajuste = cursor.fetchone()[0] > 0
                
                if tiene_ajuste:
                    # Actualizar el registro de ajuste existente
                    cursor.execute("""
                        UPDATE MovInventMes
                        SET Entradas = 0, Salidas = ?,
                            final = inicial - ?
                        WHERE Periodo = ? AND Codigo = '0000000002'
                    """, (salidas_adicionales, salidas_adicionales, periodo))
                else:
                    # Crear un nuevo registro de ajuste
                    cursor.execute("""
                        INSERT INTO MovInventMes 
                        (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros, final, Fecha)
                        VALUES (?, '0000000002', 0, ?, 'AJUSTE DE INVENTARIO', 0, ?, 0, 0, ?, ?)
                    """, (periodo, salidas_adicionales, salidas_adicionales, -salidas_adicionales, hasta))
                
                print(f"Añadiendo salidas adicionales al registro de ajuste: {salidas_adicionales:.2f}")
        
        # 10. CÁLCULOS FINALES Y AJUSTES
        
        # Calcular valor final para cada producto (pero mantener un valor positivo o cero) excepto para 0000000001
        cursor.execute("""
            UPDATE MovInventMes
            SET final = 
                CASE 
                    WHEN (ISNULL(inicial, 0) + ISNULL(Entradas, 0) - ISNULL(Salidas, 0) - 
                          ISNULL(AutoConsumo, 0) - ISNULL(Retiros, 0)) >= 0 
                    THEN (ISNULL(inicial, 0) + ISNULL(Entradas, 0) - ISNULL(Salidas, 0) - 
                          ISNULL(AutoConsumo, 0) - ISNULL(Retiros, 0))
                    ELSE 0
                END
            WHERE Periodo = ? AND Codigo <> '0000000001'
        """, (periodo,))
        
        # 11. ACTUALIZAR INVENTARIO ACUMULADO FINAL
        
        # Asegurarnos que el registro principal tenga el valor inicial y final correcto (el de InventarioContable)
        # Y que sus entradas y salidas sean siempre cero
        cursor.execute("""
            UPDATE MovInventMes
            SET inicial = ?,
                final = ?,
                Entradas = 0,
                Salidas = 0,
                AutoConsumo = 0,
                Retiros = 0
            WHERE Periodo = ? AND Codigo = '0000000001'
        """, (inventario_inicial, inventario_final, periodo))
        
        # 12. GENERAR RESUMEN PARA MOVPERIDOMES
        
        cursor.execute("DELETE FROM MovPeridoMes WHERE Periodo = ?", (periodo,))
        
        cursor.execute("""
            INSERT INTO MovPeridoMes (Periodo, Codigo, Descripcion, Costo, Inicial, Entradas, Salidas, AutoConsumo, Retiros, Fecha)
            SELECT 
                Periodo, Codigo, Descripcion, Costo, Inicial, 
                Entradas, Salidas, AutoConsumo, Retiros, Fecha
            FROM MovInventMes  
            WHERE Periodo = ?
        """, (periodo,))
        
        # Commit y cerrar conexión
        conn.commit()
        conn.close()
        
        print(f"Procesamiento de movimientos para {periodo} completado con éxito.")
        return True
        
    except Exception as e:
        print(f"Error al procesar movimientos: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Intentar hacer rollback si la conexión sigue abierta
        try:
            if conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def generar_y_procesar_mes(año, mes):
    """
    Genera y procesa los movimientos para un mes específico en un solo paso.
    Integra la generación de movimientos con el procesamiento para el informe.
    
    Args:
        año (int): El año para el cual generar movimientos
        mes (int): El mes para el cual generar movimientos (1-12)
        
    Returns:
        bool: True si se completó con éxito, False en caso de error
    """
    try:
        # Verificar que existe el período en InventarioContable
        periodo = f"{mes:02d}/{año}"
        datos_periodo = obtener_datos_periodo(periodo)
        
        if datos_periodo is None:
            print(f"No se encontró el período {periodo} en InventarioContable.")
            print("Creando período faltante...")
            # Crear el período si no existe
            if mes == 1:
                # Para enero, intentar obtener el valor final de diciembre del año anterior
                periodo_diciembre_anterior = f"12/{año-1}"
                datos_diciembre_anterior = obtener_datos_periodo(periodo_diciembre_anterior)
                
                if datos_diciembre_anterior is not None:
                    valor_inicial = datos_diciembre_anterior['Final']
                    valor_final = valor_inicial * 1.05  # Incremento del 5%
                else:
                    # Si no hay datos de diciembre, usar valores predeterminados
                    valor_inicial = 1000000.0
                    valor_final = 1050000.0
            else:
                # Para otros meses, obtener el valor final del mes anterior
                periodo_anterior = f"{mes-1:02d}/{año}"
                datos_mes_anterior = obtener_datos_periodo(periodo_anterior)
                
                if datos_mes_anterior is not None:
                    valor_inicial = datos_mes_anterior['Final']
                    valor_final = valor_inicial * 1.05  # Incremento del 5%
                else:
                    # Si no hay datos del mes anterior, usar valores predeterminados
                    valor_inicial = 1000000.0
                    valor_final = 1050000.0
            
            # Crear el período en InventarioContable
            nombre_mes = calendar.month_name[mes].upper()
            descripcion = f"{nombre_mes} {año}"
            insertar_periodo(periodo, descripcion, valor_inicial, valor_final)
            print(f"Período creado: {periodo} - Inicial: {valor_inicial:.2f}, Final: {valor_final:.2f}")
        
        # Generar los movimientos
        print(f"\nGenerando movimientos para {mes:02d}/{año}...")
        movimientos = generar_movimientos(año, mes)
        
        if movimientos is None or len(movimientos) == 0:
            print(f"No se pudieron generar movimientos para {mes:02d}/{año}")
            # Si no se generaron movimientos, verificar si ya existen en la base de datos
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM MovInvent 
                WHERE YEAR(Fecha) = ? AND MONTH(Fecha) = ?
            """, (año, mes))
            
            movimientos_existentes = cursor.fetchone()[0] > 0
            conn.close()
            
            if not movimientos_existentes:
                return False
            
            print("Se encontraron movimientos existentes, continuando con el procesamiento...")
            
        else:
            # Insertar los movimientos
            insertar_movimientos(movimientos)
            print(f"Se generaron e insertaron {len(movimientos)} movimientos para {mes:02d}/{año}")
        
        # Calcular rango de fechas del período
        primer_dia = datetime(año, mes, 1)
        if mes == 12:
            ultimo_dia = datetime(año + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(año, mes + 1, 1) - timedelta(days=1)
            
        # Procesar los movimientos para el informe
        exito = procesar_movimientos_inventario(periodo, primer_dia, ultimo_dia)
        
        if exito:
            print(f"Proceso completo para {periodo} finalizado correctamente.")
            
            # Verificar si los valores finales coinciden con los de InventarioContable
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT SUM(final) FROM MovInventMes WHERE Periodo = ? AND Codigo = '0000000001'
            """, (periodo,))
            
            valor_final_movimientos = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT Final FROM InventarioContable WHERE Periodo = ?
            """, (periodo,))
            
            valor_final_inventario = cursor.fetchone()[0]
            
            conn.close()
            
            if valor_final_movimientos is not None and valor_final_inventario is not None:
                if abs(float(valor_final_movimientos) - float(valor_final_inventario)) > 1:
                    print(f"Advertencia: Los valores finales no coinciden:")
                    print(f"Valor final en MovInventMes: {valor_final_movimientos:.2f}")
                    print(f"Valor final en InventarioContable: {valor_final_inventario:.2f}")
                    
                    # Si es diciembre, no actualizar el valor final en InventarioContable
                    if mes == 12:
                        print(f"No se actualizará el valor final de diciembre en InventarioContable, ya que es un valor de referencia")
                    else:
                        # Solo actualizar para otros meses
                        actualizar_periodo(periodo, final=valor_final_movimientos)
                        print(f"Se actualizó el valor final en InventarioContable a {valor_final_movimientos:.2f}")
            
        else:
            print(f"Hubo errores en el procesamiento para {periodo}")
            
        return exito
    
    except Exception as e:
        print(f"Error en generar_y_procesar_mes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def generar_año_completo(año):
    """
    Genera movimientos para todo el año, asegurando coherencia entre los valores
    de cada mes y manteniéndolos dentro de rangos razonables.
    
    Args:
        año (int): El año para el cual generar movimientos
        
    Returns:
        None
    """
    print(f"Creando períodos faltantes para el año {año}...")
    try:
        # Asegurar que existan todos los períodos del año
        if not crear_periodos_faltantes(año):
            print("Error al crear los períodos faltantes")
            return
        
        # Obtener el valor final de diciembre (valor de referencia) - NO debemos modificarlo
        conexion = get_connection()
        cursor = conexion.cursor()
        
        # Verificar valor de diciembre
        cursor.execute("SELECT Final FROM InventarioContable WHERE Periodo = ?", (f"12/{año}",))
        row = cursor.fetchone()
        
        if row is None:
            print(f"No se encontró el período 12/{año}")
            conexion.close()
            return
        
        valor_final_diciembre = float(row[0])
        print(f"Valor final de referencia para diciembre: {valor_final_diciembre:.2f}")
        
        # Verificar si existe el valor inicial para enero
        cursor.execute("SELECT Inicial FROM InventarioContable WHERE Periodo = ?", (f"01/{año}",))
        row = cursor.fetchone()
        
        if row is None:
            print(f"No se encontró el período 01/{año}")
            conexion.close()
            return
        
        valor_inicial_enero = float(row[0])
        
        # Calcular el incremento anual basado en el valor inicial de enero y el valor final de diciembre
        incremento_anual = valor_final_diciembre / valor_inicial_enero
        
        # Distribuir el incremento de manera progresiva entre los meses
        incremento_mensual = incremento_anual ** (1.0 / 12)  # Raíz 12 del incremento anual
        
        # Recalcular los valores iniciales y finales para cada mes, respetando el valor final de diciembre
        valor_actual = valor_inicial_enero
        for mes in range(1, 13):
            periodo = f"{mes:02d}/{año}"
            
            # Para todos los meses excepto diciembre
            if mes < 12:
                # Calcular valor final basado en incremento mensual
                valor_final = valor_actual * incremento_mensual
                
                # Actualizar los valores en la base de datos
                cursor.execute("UPDATE InventarioContable SET Inicial = ?, Final = ? WHERE Periodo = ?", 
                              (valor_actual, valor_final, periodo))
                
                # El valor final de este mes será el inicial del siguiente
                valor_actual = valor_final
            else:
                # Para diciembre, solo actualizar el valor inicial, manteniendo el valor final existente
                cursor.execute("UPDATE InventarioContable SET Inicial = ? WHERE Periodo = ?", 
                              (valor_actual, periodo))
        
        conexion.commit()
        conexion.close()
        
        print("\nValores coherentes establecidos para todo el año")
        print(f"Valor inicial del año: {valor_inicial_enero:.2f}")
        print(f"Valor final del año (referencia): {valor_final_diciembre:.2f}")
        print(f"Incremento anual: {(incremento_anual - 1) * 100:.2f}%")
        
        print("\nGenerando movimientos para cada mes...")
        for mes in range(1, 13):
            try:
                print(f"\nGenerando movimientos para {calendar.month_name[mes]} {año}...")
                
                # Usar la función integrada para generar y procesar en un solo paso
                exito = generar_y_procesar_mes(año, mes)
                
                if not exito:
                    print(f"Error al procesar {calendar.month_name[mes]}, continuando con el siguiente mes...")
                
            except Exception as e:
                print(f"Error en mes {mes}: {str(e)}")
                continue
                
        print("\nGeneración de movimientos completada para el año completo")
        
    except Exception as e:
        print(f"Error en generar_año_completo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Por favor, use ejecutar_generacion.py para generar los movimientos.")
    print("Ejemplo: python ejecutar_generacion.py 2025") 