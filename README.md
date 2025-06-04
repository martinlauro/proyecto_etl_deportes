# Proyecto ETL: Análisis de Ventas de Deportes Online

## 1. Introducción

Este proyecto implementa un pipeline ETL (Extracción, Transformación y Carga) en Python para procesar datos de ventas de una base de datos MySQL de una tienda de deportes online. El objetivo principal es generar una tabla de hechos (`ventas_diarias_productos`) que resuma las transacciones de ventas a nivel diario por producto, enriquecida con atributos clave de clientes, categorías y marcas. Esta tabla está diseñada para facilitar el análisis de datos y la creación de dashboards interactivos en herramientas de Business Intelligence como Power BI.

## 2. Arquitectura del Proyecto

El sistema se compone de los siguientes elementos:

* **Base de Datos MySQL:** Origen y destino de los datos. Contiene tablas transaccionales (clientes, pedidos, productos, etc.).
* **Script Python (`etl_script.py`):** Contiene la lógica principal del ETL, gestionando la conexión a la base de datos, la extracción, transformación y carga de datos.
* **Pandas:** Librería de Python utilizada para la manipulación y transformación eficiente de DataFrames.
* **Power BI:** Herramienta de Business Intelligence para la visualización y análisis interactivo de los datos cargados.

## 3. Fases del Proceso ETL

El `etl_script.py` ejecuta las tres fases principales del ETL de manera secuencial:

### 3.1. Fase de Extracción (Extract)

* **Objetivo:** Conectarse a la base de datos MySQL de origen y recuperar los datos brutos de las tablas transaccionales (`clientes`, `pedidos`, `detalle_pedidos`, `productos`, `categorias`, `marcas`, `envios`).
* **Tecnología:** `mysql.connector` para la conexión a la base de datos y `pandas.read_sql_query` para cargar los datos directamente en DataFrames de Pandas.
* **Salida:** Un diccionario de DataFrames, donde cada clave es el nombre de la tabla y el valor es el DataFrame correspondiente.

### 3.2. Fase de Transformación (Transform)

* **Objetivo:** Consolidar y agregar los datos brutos extraídos para crear una tabla de hechos (`ventas_diarias_productos`) optimizada para análisis. Este proceso implica:
    * **Renombrado de Columnas:** Estandarización de nombres de columnas para evitar conflictos y mejorar la legibilidad.
    * **Uniones (Joins):** Fusión de múltiples tablas (`detalle_pedidos`, `pedidos`, `productos`, `categorias`, `marcas`, `clientes`) utilizando claves primarias y foráneas (`pedido_id`, `producto_id`, `categoria_id`, `marca_id`, `cliente_id`).
    * **Preparación de Fechas:** Conversión de la columna de fecha a un formato adecuado para agrupación diaria.
    * **Agregación:** Resumen de las ventas diarias por `fecha_venta`, `producto_id`, `cliente_id`, `nombre_producto`, `nombre_categoria`, `nombre_marca` y `ciudad_cliente`. Las métricas agregadas incluyen:
        * `precio_unitario_promedio_dia` (media)
        * `cantidad_vendida_dia` (suma)
        * `total_ventas_dia` (suma)
        * `numero_pedidos_dia` (conteo de pedidos únicos)
* **Tecnología:** Librería Pandas para todas las operaciones de manipulación y agregación de DataFrames.
* **Salida:** Un DataFrame `df_ventas_agregadas` listo para ser cargado.

### 3.3. Fase de Carga (Load)

* **Objetivo:** Almacenar el DataFrame transformado (`df_ventas_agregadas`) en una nueva tabla de hechos llamada `ventas_diarias_productos` en la misma base de datos MySQL.
* **Proceso:**
    1.  Eliminación de la tabla existente (si la hay) para asegurar una carga limpia y consistente.
    2.  Creación de la tabla `ventas_diarias_productos` con la estructura de columnas y tipos de datos adecuados, incluyendo `producto_id` y `cliente_id` para futuras relaciones en Power BI.
    3.  Inserción masiva de los datos del DataFrame transformado en la nueva tabla.
* **Tecnología:** `mysql.connector` para ejecutar sentencias DDL (Data Definition Language) como `DROP TABLE` y `CREATE TABLE`, y sentencias DML (Data Manipulation Language) como `INSERT INTO` (utilizando `executemany` para una inserción eficiente).

## 4. Gestión de Errores y Soluciones Implementadas

Durante el desarrollo de este pipeline, se identificaron y resolvieron varios errores comunes, mejorando la robustez del script:

* **Error de Sintaxis SQL (`1064 (42000)`):**
    * **Descripción:** Causado por una coma extra al final de la última definición de columna en la consulta `CREATE TABLE`.
    * **Solución:** Eliminación de la coma final en la sentencia `CREATE TABLE` dentro de la función `load_data`.
* **Error de Clave Inexistente (`KeyError: 'producto_idnombre_producto'`):**
    * **Descripción:** Ocasionado por una coma faltante en la lista de agrupamiento (`groupby`) de Pandas, lo que concatenó accidentalmente dos nombres de columna (`'producto_id'` y `'nombre_producto'`) en una sola cadena.
    * **Solución:** Inclusión de la coma faltante entre `'producto_id'` y `'nombre_producto'` en la lista de columnas del `groupby` en la función `transform_data`.
* **Error de Variable Local no Asignada (`cannot access local variable 'err'`):**
    * **Descripción:** Surgió al intentar referenciar la variable `err` (definida solo en un bloque `except`) fuera de su alcance cuando no se producía un error.
    * **Solución:** Refactorización de la lógica de manejo de excepciones en la función `load_data` para asegurar que `err` solo se acceda cuando realmente se ha capturado una excepción.
* **Ausencia de `producto_id` y `cliente_id` en la tabla final:**
    * **Descripción:** Inicialmente, estas claves primarias de dimensión no se incluían en la tabla de hechos agregada, limitando las relaciones en Power BI.
    * **Solución:** Inclusión explícita de `producto_id` y `cliente_id` en la lista de agrupamiento (`groupby`) de la función `transform_data` y su correspondiente adición a la definición `CREATE TABLE` y la lista de columnas de inserción en `load_data`.

## 5. Modelado de Datos en Power BI

Una vez cargada la tabla `ventas_diarias_productos`, el siguiente paso es conectar Power BI a la base de datos MySQL y establecer un modelo de datos robusto:

* **Conexión:** Importar la tabla `ventas_diarias_productos` (y las tablas de dimensión si es necesario, como `productos`, `clientes`, `categorias`, `marcas`) desde MySQL a Power BI.
* **Creación de Tabla Calendario:** Generar una tabla de fechas en Power BI Desktop utilizando DAX (`CALENDAR(MIN('fecha_venta'), MAX('fecha_venta'))`) para facilitar el análisis de tiempo y la inteligencia de tiempo.
* **Establecimiento de Relaciones:**
    * `ventas_diarias_productos[producto_id]` (Muchos) con `productos[producto_id]` (Uno).
    * `ventas_diarias_productos[cliente_id]` (Muchos) con `clientes[cliente_id]` (Uno).
    * `ventas_diarias_productos[fecha_venta]` (Muchos) con `Tabla Calendario[Date]` (Uno).
    * Relaciones entre tablas de dimensión (`productos` con `categorias` y `marcas`).
* **Medidas DAX:** Creación de medidas clave para el análisis (ej. `Total Cantidad Vendida`, `Promedio Cantidad Vendida por Producto y Día`, `Total Ventas Brutas`, `Clientes Únicos`, `Ventas Brutas Año Anterior`, etc.).

## 6. Dashboards y Análisis (Power BI)

El modelo de datos permite la creación de dashboards interactivos para obtener insights sobre el negocio, tales como:

* **Rendimiento de Productos:** Identificación de los productos más vendidos por volumen, valor y promedio de ventas.
* **Análisis Temporal:** Tendencias de ventas diarias, mensuales y anuales, y comparaciones con periodos anteriores.
* **Perfil de Clientes:** Cantidad de clientes únicos y su distribución por ciudad.
* **Rendimiento por Categoría y Marca:** Contribución de cada categoría y marca a las ventas totales.

---
