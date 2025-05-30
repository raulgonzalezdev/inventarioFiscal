USE [DatqBoxExpress]
GO
/****** Object:  StoredProcedure [dbo].[sp_MovUnidadesMes]    Script Date: 13/05/2025 09:13:46 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER procedure [dbo].[sp_MovUnidadesMes] (
  @periodo varchar(7),
  @desde datetime,
  @hasta datetime,
  @todos bit
 )
as
BEGIN
    SET NOCOUNT ON;
    
    -- Variables para manejar los valores de inventario inicial y final
    DECLARE @inventarioInicial FLOAT;
    DECLARE @inventarioFinal FLOAT;
    DECLARE @diferenciaInventario FLOAT;
    DECLARE @registroInicialExiste INT = 0;
    DECLARE @mesActual INT;
    DECLARE @añoActual INT;
    DECLARE @periodoAnterior VARCHAR(7) = NULL;
    
    -- Extraer mes y año del período
    SET @mesActual = CAST(LEFT(@periodo, 2) AS INT);
    SET @añoActual = CAST(RIGHT(@periodo, 4) AS INT);
    
    -- Determinar el período anterior (mes anterior o diciembre del año anterior)
    IF @mesActual = 1
    BEGIN
        -- Si es enero, el período anterior es diciembre del año anterior
        SET @periodoAnterior = '12/' + CAST(@añoActual - 1 AS VARCHAR);
    END
    ELSE
    BEGIN
        -- De lo contrario, es el mes anterior del mismo año
        SET @periodoAnterior = RIGHT('0' + CAST(@mesActual - 1 AS VARCHAR), 2) + '/' + CAST(@añoActual AS VARCHAR);
    END
    
    BEGIN TRANSACTION;
    
    -- 1. LIMPIEZA INICIAL
    
    -- Eliminar registros de servicios (mantener solo productos físicos)
    DELETE m
    FROM dbo.MovInvent m
    INNER JOIN dbo.Inventario i ON m.Product = i.CODIGO
    WHERE i.Linea = N'SERVICIO' AND m.Fecha BETWEEN @desde AND @hasta;
    
    -- Corregir valores negativos
    UPDATE MovInvent 
    SET CANTIDAD_ACTUAL = 0 
    WHERE CANTIDAD_ACTUAL < 0 AND Fecha BETWEEN @desde AND @hasta;
    
    -- 2. OBTENER VALORES DE INVENTARIO
    
    -- Obtener valor inicial y final del período actual
    SELECT @inventarioInicial = Inicial, @inventarioFinal = Final
    FROM InventarioContable
    WHERE Periodo = @periodo;
    
    -- Para enero, asegurar que el valor inicial sea el final del período anterior (diciembre año anterior)
    IF @mesActual = 1
    BEGIN
        -- Obtener el valor final de diciembre del año anterior para usarlo como inicial
        DECLARE @valorFinalAnterior FLOAT;
        
        SELECT @valorFinalAnterior = Final
        FROM InventarioContable
        WHERE Periodo = @periodoAnterior;
        
        -- Si encontramos un valor, actualizar el valor inicial
        IF @valorFinalAnterior IS NOT NULL
        BEGIN
            -- Actualizar el valor inicial en la variable
            SET @inventarioInicial = @valorFinalAnterior;
            
            -- Y actualizar también en la tabla InventarioContable para que haya coherencia
            UPDATE InventarioContable
            SET Inicial = @valorFinalAnterior
            WHERE Periodo = @periodo;
        END
    END
    
    -- Calcular diferencia para saber si hay más entradas o salidas
    SET @diferenciaInventario = @inventarioFinal - @inventarioInicial;
    
    -- 3. VERIFICAR SI YA EXISTE EL REGISTRO DE INVENTARIO INICIAL
    SELECT @registroInicialExiste = COUNT(*)
                 FROM MovInvent 
    WHERE Product = '0000000001' 
      AND Motivo = 'INVENTARIO INICIAL MES ANTERIOR'
      AND Fecha BETWEEN @desde AND @hasta;
    
    -- 4. LIMPIAR TABLA DE RESULTADOS RESPETANDO LOS DATOS EXISTENTES
    -- Solo eliminamos los registros de este período pero mantenemos los datos de la tabla MovInvent
    DELETE FROM MovInventMes WHERE Periodo = @periodo;
    
    -- 5. PROCESAR DATOS DEL INVENTARIO
    -- Solo inserta en MovInventMes, NO en MovInvent (que ya fue creado por Python)
    INSERT INTO MovInventMes (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros, final)
    VALUES (
        @periodo, 
        '0000000001', 
        @inventarioInicial,
        @inventarioInicial, 
        'INVENTARIO INICIAL MES ANTERIOR', 
        0, 0, 0, 0,
        @inventarioInicial
    );
    
    -- 6. CALCULAR MOVIMIENTOS EXISTENTES
    
    -- Tabla temporal para movimientos agrupados por producto
    DECLARE @MovimientosProducto TABLE (
        Codigo VARCHAR(50),
        Entradas FLOAT,
        EntradasValor FLOAT,
        Salidas FLOAT,
        SalidasValor FLOAT,
        Autoconsumo FLOAT,
        AutoconsumoValor FLOAT,
        Retiros FLOAT,
        RetirosValor FLOAT
    );
    
    -- Insertar en la tabla temporal los movimientos agrupados por producto
    INSERT INTO @MovimientosProducto (Codigo, Entradas, EntradasValor, Salidas, SalidasValor, 
                                     Autoconsumo, AutoconsumoValor, Retiros, RetirosValor)
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
    WHERE m.Fecha BETWEEN @desde AND @hasta AND m.Anulada = 0
    GROUP BY m.Product;
    
    -- 7. INSERTAR PRODUCTOS CON SUS MOVIMIENTOS
    
    -- Insertar productos con su inventario basado en los movimientos existentes
    INSERT INTO MovInventMes (Periodo, Codigo, inicial, Costo, Descripcion, Entradas, Salidas, AutoConsumo, Retiros)
    SELECT 
        @periodo, 
        i.CODIGO, 
        0, -- El inicial es 0 para todos los productos excepto el registro de inventario inicial
        i.COSTO_REFERENCIA,
        i.CATEGORIA + ' ' + i.TIPO + ' ' + i.DESCRIPCION + ' ' + i.MARCA AS Descripciones,
        ISNULL(mp.Entradas, 0),
        ISNULL(mp.Salidas, 0),
        ISNULL(mp.Autoconsumo, 0),
        ISNULL(mp.Retiros, 0)
    FROM Inventario i
    INNER JOIN @MovimientosProducto mp ON i.CODIGO = mp.Codigo
    WHERE i.CODIGO <> '0000000001'; -- Excluir el registro de inventario inicial que ya fue creado
    
    -- 8. CALCULAR TOTALES DE VALORES
    DECLARE @totalEntradas FLOAT = 0;
    DECLARE @totalSalidas FLOAT = 0;
    DECLARE @totalAutoconsumo FLOAT = 0;
    DECLARE @totalRetiros FLOAT = 0;
    
    SELECT 
        @totalEntradas = ISNULL(SUM(EntradasValor), 0),
        @totalSalidas = ISNULL(SUM(SalidasValor), 0),
        @totalAutoconsumo = ISNULL(SUM(AutoconsumoValor), 0),
        @totalRetiros = ISNULL(SUM(RetirosValor), 0)
    FROM @MovimientosProducto;
    
    -- 9. VERIFICAR SI NECESITAMOS AJUSTAR ENTRADAS O SALIDAS PARA CUADRAR
    
    -- Calcular el valor final teórico basado en los movimientos existentes
    DECLARE @valorFinalCalculado FLOAT;
    SET @valorFinalCalculado = @inventarioInicial + @totalEntradas - @totalSalidas - @totalAutoconsumo - @totalRetiros;
    
    -- Si la diferencia es mayor a 1, necesitamos ajustar
    IF ABS(@valorFinalCalculado - @inventarioFinal) > 1
    BEGIN
        -- Determinar si necesitamos agregar entradas o salidas
        IF @valorFinalCalculado < @inventarioFinal
        BEGIN
            -- Necesitamos aumentar entradas para llegar al valor final deseado
            DECLARE @entradasAdicionales FLOAT = @inventarioFinal - @valorFinalCalculado;
            
            -- Actualizar el registro del inventario inicial para incluir las entradas adicionales
            UPDATE MovInventMes
            SET Entradas = @entradasAdicionales,
                final = inicial + @entradasAdicionales - Salidas - AutoConsumo - Retiros
            WHERE Periodo = @periodo AND Codigo = '0000000001';
        END
        ELSE
        BEGIN
            -- Necesitamos aumentar salidas para llegar al valor final deseado
            DECLARE @salidasAdicionales FLOAT = @valorFinalCalculado - @inventarioFinal;
            
            -- Actualizar el registro del inventario inicial para incluir las salidas adicionales
            UPDATE MovInventMes
            SET Salidas = @salidasAdicionales,
                final = inicial - @salidasAdicionales - AutoConsumo - Retiros
            WHERE Periodo = @periodo AND Codigo = '0000000001';
        END
    END
    
    -- 10. CÁLCULOS FINALES Y AJUSTES
    
    -- Calcular valor final para cada producto
    UPDATE MovInventMes
    SET final = ISNULL(inicial, 0) + ISNULL(entradas, 0) - ISNULL(salidas, 0) - 
               ISNULL(autoconsumo, 0) - ISNULL(retiros, 0)
    WHERE Periodo = @periodo;
    
    -- Asegurarse que no haya valores negativos en el inventario final
    UPDATE MovInventMes
    SET final = 0
    WHERE final < 0 AND Periodo = @periodo;
    
    -- 11. ACTUALIZAR INVENTARIO ACUMULADO FINAL
    
    -- Asegurarnos que el registro principal tenga el valor final correcto
    UPDATE MovInventMes
    SET final = @inventarioFinal
    WHERE Periodo = @periodo AND Codigo = '0000000001';
    
    -- 12. GENERAR RESUMEN PARA MOVPERIDOMES SI ES SOLICITADO
    IF @todos = 1 
    BEGIN
        DELETE FROM MovPeridoMes WHERE Periodo = @periodo;
        
        INSERT INTO MovPeridoMes (Periodo, Codigo, Descripcion, Costo, Inicial, Entradas, Salidas, AutoConsumo, Retiros)
        SELECT 
            Periodo, Codigo, Descripcion, Costo, Inicial, 
            Entradas, Salidas, AutoConsumo, Retiros
        FROM MovInventMes  
        WHERE Periodo = @periodo;
    END
    
    COMMIT TRANSACTION;
END
