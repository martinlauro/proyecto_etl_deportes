import mysql.connector
import pandas as pd
from datetime import datetime
from decimal import Decimal

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
db_config = {
    'host': 'localhost',
    'user': 'root',  # Revisa esto si usas otro usuario
    'password': 'Juanleon644Marcelo', # ¡ASEGÚRATE DE QUE ESTA CONTRASEÑA SEA LA CORRECTA!
    'database': 'deportes_online'
}

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(**db_config)
        print("Conexión a la base de datos exitosa.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def extract_data(conn):
    """
    Extrae datos de varias tablas de la base de datos y los carga en DataFrames.
    """
    data = {}
    queries = {
        'clientes': "SELECT * FROM Clientes",
        'pedidos': "SELECT * FROM Pedidos",
        'detalle_pedidos': "SELECT * FROM Detalle_Pedidos",
        'productos': "SELECT * FROM Productos",
        'categorias': "SELECT * FROM Categorias",
        'marcas': "SELECT * FROM Marcas"
    }

    for table_name, query in queries.items():
        print(f"Extrayendo datos de la tabla: {table_name}...")
        try:
            data[table_name] = pd.read_sql_query(query, conn)
            print(f"'{table_name}' extraída con {len(data[table_name])} filas.")
        except pd.io.sql.DatabaseError as e:
            print(f"ERROR al extraer datos de '{table_name}': {e}")
            data[table_name] = None
        except Exception as e:
            print(f"Ocurrió un error inesperado al extraer '{table_name}': {e}")
    return data

def transform_data(raw_data):
    """
    Transforma los datos extraídos para crear un resumen de ventas diarias por producto.
    """
    print("\nIniciando fase de Transformación...")

    if any(df is None for df in raw_data.values()):
        print("ERROR: No todos los DataFrames se extrajeron correctamente. Abortando transformación.")
        return None

    # Renombrar columnas para evitar conflictos y facilitar la unión
    raw_data['pedidos'] = raw_data['pedidos'].rename(columns={'cliente_id': 'id_cliente_pedido'})
    raw_data['productos'] = raw_data['productos'].rename(columns={'nombre': 'nombre_producto', 'categoria_id': 'id_categoria_producto', 'marca_id': 'id_marca_producto'})
    raw_data['categorias'] = raw_data['categorias'].rename(columns={'nombre': 'nombre_categoria'})
    raw_data['marcas'] = raw_data['marcas'].rename(columns={'nombre': 'nombre_marca'})

    # 1. Unir Pedidos y Detalle_Pedidos
    df_ventas = pd.merge(raw_data['detalle_pedidos'], raw_data['pedidos'], on='pedido_id', how='inner')
    print(f"Paso 1: Detalle_Pedidos + Pedidos = {df_ventas.shape[0]} filas.")

    # 2. Unir con Productos
    df_ventas = pd.merge(df_ventas, raw_data['productos'], on='producto_id', how='inner')
    print(f"Paso 2: + Productos = {df_ventas.shape[0]} filas.")

    # 3. Unir con Categorias
    df_ventas = pd.merge(df_ventas, raw_data['categorias'], left_on='id_categoria_producto', right_on='categoria_id', how='inner')
    print(f"Paso 3: + Categorias = {df_ventas.shape[0]} filas.")

    # 4. Unir con Marcas (ya corregido)
    df_ventas = pd.merge(df_ventas, raw_data['marcas'], left_on='id_marca_producto', right_on='marca_id', how='inner')
    print(f"Paso 4: + Marcas = {df_ventas.shape[0]} filas.")

    # 5. Unir con Clientes para obtener la ciudad
    df_ventas = pd.merge(df_ventas, raw_data['clientes'][['cliente_id', 'ciudad']], left_on='id_cliente_pedido', right_on='cliente_id', how='inner')
    print(f"Paso 5: + Clientes = {df_ventas.shape[0]} filas.")

    # Preparar la fecha para la agrupación diaria
    df_ventas['fecha_venta'] = pd.to_datetime(df_ventas['fecha_pedido']).dt.date

    # 6. Agregación final
    df_ventas_agregadas = df_ventas.groupby([
        'fecha_venta',
        'nombre_producto',
        'nombre_categoria',
        'nombre_marca',
        'ciudad' # Ciudad del cliente
    ]).agg(
        precio_unitario_promedio_dia=('precio_unitario_en_momento_compra', 'mean'),
        cantidad_vendida_dia=('cantidad', 'sum'),
        total_ventas_dia=('subtotal', 'sum'),
        numero_pedidos_dia=('pedido_id', 'nunique')
    ).reset_index()

    df_ventas_agregadas['precio_unitario_promedio_dia'] = df_ventas_agregadas['precio_unitario_promedio_dia'].round(2)
    df_ventas_agregadas['total_ventas_dia'] = df_ventas_agregadas['total_ventas_dia'].round(2)

    print(f"Transformación completada: DataFrame final con {df_ventas_agregadas.shape[0]} filas y {df_ventas_agregadas.shape[1]} columnas.")
    return df_ventas_agregadas

def load_data(transformed_df, conn):
    """
    Carga el DataFrame transformado en una nueva tabla en la base de datos MySQL.
    Contiene un error intencionado en la sintaxis SQL.
    """
    print("\nIniciando fase de Carga...")
    if transformed_df is None:
        print("ERROR: No hay datos transformados para cargar.")
        return

    table_name = "ventas_diarias_productos" # Nombre correcto para la tabla final

    cursor = conn.cursor()

    # Primero, eliminar la tabla si existe para asegurar una carga limpia
    drop_table_query = f"DROP TABLE IF EXISTS {table_name}"
    try:
        cursor.execute(drop_table_query)
        conn.commit()
        print(f"Tabla '{table_name}' eliminada (si existía).")
    except mysql.connector.Error as err:
        print(f"Advertencia al eliminar tabla '{table_name}': {err}")

    # Crear la tabla con un ERROR INTENCIONADO en la sintaxis SQL
    # La primera línea del texto SQL debe empezar SIN INDENTACIÓN EXTRA
    create_table_query = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_venta DATE NOT NULL,
    nombre_producto VARCHAR(255) NOT NULL,
    nombre_categoria VARCHAR(100),
    nombre_marca VARCHAR(100),
    ciudad_cliente VARCHAR(100),
    precio_unitario_promedio_dia DECIMAL(10, 2),
    cantidad_vendida_dia INT,
    total_ventas_dia DECIMAL(10, 2),
    numero_pedidos_dia INT -- ERROR INTENCIONADO: coma extra al final
)
"""
    try:
        cursor.execute(create_table_query)
        conn.commit()
        print(f"ERROR al crear tabla '{table_name}': creada/verificada.") # <-- Cambiado para imprimir el error aquí
        return # Si la tabla no se puede crear, abortamos la carga
    except mysql.connector.Error as err:
        print(f"ERROR al crear tabla '{table_name}': {err}")
        return # Si la tabla no se puede crear, abortamos la carga


    # Preparar los datos para la inserción
    transformed_df['fecha_venta'] = transformed_df['fecha_venta'].astype(str)

    columns_to_insert = [
        'fecha_venta', 'nombre_producto', 'nombre_categoria', 'nombre_marca', 'ciudad',
        'precio_unitario_promedio_dia', 'cantidad_vendida_dia', 'total_ventas_dia', 'numero_pedidos_dia'
    ]
    data_to_insert = transformed_df[columns_to_insert].values.tolist()

    placeholders = ', '.join(['%s'] * len(columns_to_insert))
    insert_query = f"""
    INSERT INTO {table_name} (
        fecha_venta, nombre_producto, nombre_categoria, nombre_marca, ciudad_cliente,
        precio_unitario_promedio_dia, cantidad_vendida_dia, total_ventas_dia, numero_pedidos_dia
    ) VALUES ({placeholders})
    """

    try:
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        print(f"Se cargaron {len(data_to_insert)} filas en la tabla '{table_name}' correctamente.")
    except mysql.connector.Error as err:
        print(f"ERROR al cargar datos en la tabla '{table_name}': {err}")
        conn.rollback()
    finally:
        cursor.close()


def main():
    conn = None
    try:
        conn = get_db_connection()
        if conn:
            raw_data = extract_data(conn)
            transformed_data = transform_data(raw_data)

            # --- FASE DE CARGA ---
            if transformed_data is not None:
                load_data(transformed_data, conn) # Llamada a load_data

    except Exception as e:
        print(f"Ocurrió un error inesperado durante el proceso principal: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main()