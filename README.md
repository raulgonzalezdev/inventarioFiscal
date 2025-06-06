# 📊 Sistema de Inventario Fiscal

Sistema integral para la gestión y generación de reportes de inventario fiscal conforme al **Artículo 177 de la Ley de Impuesto Sobre la Renta**, que automatiza la creación del "Libro Auxiliar de Entradas y Salidas del Inventario" requerido por las autoridades fiscales.

## 🎯 Objetivo Principal

Generar de forma automática el **Libro Auxiliar de Entradas y Salidas del Inventario** en formato Excel, cumpliendo con los requisitos legales establecidos y proporcionando una demostración matemática clara de que los movimientos registrados justifican el cambio del inventario inicial al final del período fiscal.

---

## 🏗️ Arquitectura del Sistema

### 📂 Estructura de Archivos

#### **🔧 Módulos Principales**

| Archivo | Descripción | Función Principal |
|---------|-------------|-------------------|
| `generador_inventario.py` | **Motor de generación clásico** | Genera movimientos de inventario usando algoritmos de distribución básicos |
| `generador_inventario_directo.py` | **Motor de generación avanzado** | Versión mejorada con control preciso de valores y distribución inteligente |
| `generador_inventario_execel.py` | **Generador de Excel** | Crea el reporte final en Excel con formato profesional y ajustes automáticos |

#### **⚙️ Utilerías y Correcciones**

| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `corregir_diciembre.py` | **Corrector de coherencia** | Asegura que el valor inicial de diciembre sea igual al final de noviembre |
| `corregir_valores_inventario.py` | **Verificador anual** | Valida y corrige inconsistencias en todos los meses de un año |
| `debugger.py` | **Herramienta de diagnóstico** | Prueba la generación de movimientos mes por mes para detectar errores |

#### **🚀 Scripts de Ejecución**

| Archivo | Descripción | Comando |
|---------|-------------|---------|
| `ejecutar_generacion.py` | Ejecutor del motor clásico | `python ejecutar_generacion.py 2024` |
| `ejecutar_generacion_directo.py` | Ejecutor del motor avanzado | `python ejecutar_generacion_directo.py 2024` |

---

## 🗄️ Estructura de Base de Datos

### Tablas Principales

#### **📋 MovInventMes**
Almacena los movimientos mensuales de inventario por producto.

```sql
Campos principales:
- Periodo: MM/AAAA (ej: "01/2024")
- Codigo: Código del producto
- Descripcion: Descripción del producto
- inicial: Cantidad inicial del mes
- Entradas: Cantidad de entradas
- Salidas: Cantidad de salidas
- AutoConsumo: Cantidad de autoconsumo
- Retiros: Cantidad de retiros
- final: Cantidad final del mes
- Costo: Precio unitario del producto
- Fecha: Fecha del movimiento
- Inventario: Valor del inventario inicial del mes
```

#### **📊 InventarioContable**
Control de valores monetarios por período.

```sql
Campos principales:
- Periodo: MM/AAAA
- Inicial: Valor monetario inicial del mes
- Final: Valor monetario final del mes
- AjusteCompras: Ajustes por compras
- AjusteVentas: Ajustes por ventas
```

#### **📦 Inventario**
Catálogo maestro de productos.

```sql
Campos principales:
- CODIGO: Código único del producto
- DESCRIPCION: Descripción del producto
- CATEGORIA: Categoría del producto
- TIPO: Tipo de producto
- MARCA: Marca del producto
- PRECIO_COMPRA: Precio de compra
- PRECIO_VENTA: Precio de venta
- EXISTENCIA: Existencia actual
```

---

## 🔧 Configuración del Sistema

### Conexión a Base de Datos

El sistema utiliza **SQL Server** con la siguiente configuración:

```python
# Configuración en generador_inventario.py
SERVER = "DELLXEONE31545\\SQLEXPRESS"
DATABASE = "DatqBoxExpress"
USER = "sa"
PASSWORD = "e!334011"

# Configuración en generador_inventario_directo.py  
SERVER = "SANJOSESQLI3"
DATABASE = "sanjose"
USER = "sd"
PASSWORD = "1234"
```

### Dependencias

```bash
pip install pyodbc pandas openpyxl numpy
```

---

## 🚀 Guías de Uso

### **1. Generación Completa de Año (Motor Avanzado)**

Para generar movimientos para todo el año 2024 con valores específicos:

```bash
python ejecutar_generacion_directo.py 2024
```

**Valores predefinidos para 2024:**
- **Inventario inicial (enero):** $1,120,797.03
- **Inventario final (diciembre):** $1,892,903.00
- **Diferencia anual:** $772,105.97

### **2. Generación de Mes Específico**

```bash
# Generar solo enero 2024
python generador_inventario_directo.py 2024 1

# Generar solo diciembre 2024  
python generador_inventario_directo.py 2024 12
```

### **3. Generar Excel del Libro Auxiliar**

```bash
python generador_inventario_execel.py excel
```

**Resultado:** Archivo `Libro_Auxiliar_Inventario_2024.xlsx` con:
- ✅ Formato profesional conforme a normativas fiscales
- ✅ Demostración matemática del cuadre de inventarios
- ✅ Ajustes automáticos para garantizar coherencia
- ✅ Totales y subtotales por columna

### **4. Corrección y Mantenimiento**

#### Corregir coherencia de diciembre:
```bash
python corregir_diciembre.py 2024
```

#### Verificar coherencia de todo el año:
```bash
python corregir_valores_inventario.py 2024
```

#### Diagnosticar problemas:
```bash
python debugger.py
```

---

## 🔄 Flujo de Trabajo Recomendado

### **Proceso Completo para Año Fiscal**

1. **🎯 Configurar valores iniciales y finales**
   ```bash
   # Los valores para 2024 están predefinidos
   python ejecutar_generacion_directo.py 2024
   ```

2. **🔍 Verificar coherencia**
   ```bash
   python corregir_valores_inventario.py 2024
   python corregir_diciembre.py 2024
   ```

3. **📊 Generar reporte Excel**
   ```bash
   python generador_inventario_execel.py excel
   ```

4. **✅ Validar resultado**
   - Abrir archivo Excel generado
   - Verificar que la sección "DEMOSTRACIÓN DEL CUADRE" muestre coherencia
   - Confirmar que los totales cuadren perfectamente

---

## 🎨 Características del Excel Generado

### **📋 Estructura del Reporte**

| Sección | Descripción |
|---------|-------------|
| **Encabezado** | Información de la empresa y período fiscal |
| **Registro Inicial** | Inventario inicial del ejercicio anterior |
| **Movimientos Cronológicos** | Todos los movimientos ordenados por fecha |
| **Totales** | Subtotales por tipo de movimiento |
| **Demostración del Cuadre** | Verificación matemática paso a paso |

### **🎯 Columnas del Libro Auxiliar**

- **Fecha:** Fecha del movimiento
- **Descripción:** Descripción del producto o movimiento
- **Existencia Inicial:** Cantidad y monto inicial
- **Entradas:** Cantidad y monto de entradas
- **Salidas:** Cantidad y monto de salidas  
- **Autoconsumos:** Cantidad y monto de autoconsumos
- **Retiros:** Cantidad y monto de retiros
- **Existencia Actual:** Cantidad y monto final

### **⚡ Funcionalidades Avanzadas**

- **🔄 Ajuste Automático:** El sistema ajusta precios y cantidades dinámicamente para cuadrar con valores fijos
- **📈 Distribución Inteligente:** Algoritmos que distribuyen movimientos de forma natural y creíble
- **🎨 Formato Profesional:** Estilos, colores y alineaciones apropiadas para presentación fiscal
- **✅ Validación Matemática:** Demostración paso a paso de que los cálculos son correctos

---

## 🔧 Algoritmos Clave

### **💡 Sistema de Ajuste Dinámico**

El sistema implementa un mecanismo sofisticado para asegurar que los movimientos cuadren con valores predefinidos:

1. **Factor de Ajuste Proporcional:** Modifica precios proporcionalmente (factor entre 0.1 y 10.0)
2. **Movimientos de Ajuste:** Si el factor es extremo, genera movimientos adicionales
3. **Validación Final:** Inserta hasta 5 movimientos de ajuste para cuadre perfecto

### **📊 Distribución de Movimientos**

- **Selección de Productos:** Prioriza productos con existencias previas
- **Días Hábiles:** Distribuye movimientos en días laborables (lunes a sábado)
- **Patrones Naturales:** Simula comportamientos reales de compra/venta
- **Control de Negativos:** Previene existencias negativas en todo momento

---

## 🛠️ Resolución de Problemas

### **❌ Errores Comunes**

| Error | Causa | Solución |
|-------|-------|----------|
| `Error de conexión SQL` | Credenciales incorrectas | Verificar configuración en archivos .py |
| `Período no encontrado` | Datos faltantes en InventarioContable | Insertar registros manualmente en BD |
| `Existencias negativas` | Inconsistencia en datos | Ejecutar `corregir_valores_inventario.py` |
| `Excel no cuadra` | Ajustes no aplicados | Regenerar con `generador_inventario_execel.py` |

### **🔍 Comandos de Diagnóstico**

```bash
# Verificar coherencia general
python debugger.py

# Limpiar y regenerar un mes específico
python generador_inventario_directo.py 2024 1

# Forzar corrección de diciembre
python corregir_diciembre.py 2024
```

---

## 📜 Cumplimiento Legal

Este sistema está diseñado para cumplir con:

- **📋 Artículo 177 de la Ley de Impuesto Sobre la Renta**
- **📊 Requisitos de la SUNAT para libros auxiliares**
- **💼 Estándares contables para control de inventarios**
- **🔍 Trazabilidad completa de movimientos**

### **✅ Elementos de Cumplimiento**

- ✅ Registro cronológico de movimientos
- ✅ Clasificación por tipo de operación
- ✅ Valores monetarios exactos
- ✅ Demostración matemática de coherencia
- ✅ Formato apropiado para auditorías

---

## 👥 Contribución

Para contribuir al proyecto:

1. 🍴 Fork del repositorio
2. 🌿 Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. 💾 Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. 📤 Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. 🔄 Crear Pull Request

---

## 📝 Licencia

Proyecto desarrollado para cumplimiento fiscal y contable.

---

## 📞 Soporte

Para soporte técnico o dudas sobre implementación, revisar:

1. **🔍 Logs del sistema:** Verificar mensajes de error en consola
2. **📊 Base de datos:** Validar integridad de datos en tablas
3. **🧪 Modo debug:** Ejecutar `debugger.py` para diagnóstico completo

---

**💡 Nota:** Este sistema está optimizado para el año fiscal 2024 con valores específicos. Para otros años, ajustar los valores iniciales y finales según corresponda.