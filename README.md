# proyecto_etl_deportes
### Fase 3: Carga (Load)

**Objetivo:** Cargar los datos transformados en una nueva tabla `ventas_diarias_productos` en la base de datos MySQL.

**Estado Actual:**
El script `etl_script.py` ahora incluye la fase de carga. Intenta crear una nueva tabla y cargar el DataFrame transformado.
Actualmente, falla durante el intento de creación de la tabla.

**Errores Comunes y Soluciones (Fase de Carga):**

1.  **Error:** `(Pega aquí el mensaje de error exacto que obtuviste en la Consola IPython)`
    * **Causa:** Un error de sintaxis SQL en la consulta `CREATE TABLE`. Específicamente, una coma extra después de la última definición de columna (`numero_pedidos_dia INT,`).
    * **Solución:** (Aún no la has implementado, pero aquí la pondrás después).

---
