<div align="center">
  <img src="https://github.com/Luismartco/Craftroutev2/blob/main/resources/media/logo/logo.jpg" alt="Craftroute" width="150"/>
</div>

# Sistema de Recomendaciones Craftroute

Este proyecto implementa un sistema de recomendaciones para [Craftroute](https://github.com/Luismartco/Craftroutev2), una plataforma de comercio de artesanías. El sistema proporciona recomendaciones personalizadas de productos y tiendas para los usuarios basándose en técnicas de procesamiento de lenguaje natural y similitud de coseno.

## Características

- API REST desarrollada con Flask.
- Sistema de recomendación basado en contenido.
- Análisis de similitud usando TF-IDF, kNN y similitud de coseno.
- Integración con base de datos SQL.
- Recomendaciones personalizadas de productos y tiendas.

## Requisitos

- Python 3.x
- Dependencias principales:
  - Flask
  - pandas
  - numpy
  - scikit-learn
  - pymysql
  - python-dotenv
  - sqlalchemy

## Uso

### Iniciar el servidor

```bash
python app.py
```

### Endpoints disponibles

1. **Recomendación de Productos**
   ```
   GET /recomendar_productos?user_id=<id>
   ```
   Ejemplo: `http://127.0.0.1:5055/recomendar_productos?user_id=23`
   
   Retorna una lista de productos recomendados para el usuario especificado.

2. **Recomendación de Tiendas**
   ```
   GET /recomendar_tiendas?user_id=<id>
   ```
   Ejemplo: `http://127.0.0.1:5055/recomendar_tiendas?user_id=23`

   Retorna una lista de tiendas recomendadas para el usuario especificado.

3. **Ver detalle de alimentacion del modelo**
   ```
   GET /ver_datos_usuario?user_id=<id>
   ```
   Ejemplo: `http://127.0.0.1:5055/ver_datos_usuario?user_id=26`

   Retorna una lista con el ID de los productos y tiendas que ha comprado y ha marcado como recomendado.

   
   

   ## Descripción de las funciones en `recommender.py`

   Resumen de las funciones públicas y cómo funcionan (firma, objetivo y comportamiento):

   - `cargar_productos()` -> DataFrame
      - Lee la tabla `productos` desde la base de datos (usando `get_engine()` de `config.py`).
      - Construye una columna `features` que concatena `nombre`, `descripcion`, `categoria_id`, `material_id`, `tecnica_id`, `municipio_venta` y `color` como texto para vectorización.
      - Retorna un `pandas.DataFrame` con los productos y la columna `features`.

   - `cargar_tiendas()` -> DataFrame
      - Lee la tabla `tiendas` desde la base de datos y retorna un `DataFrame` con columnas como `id`, `user_id`, `nombre`, `barrio`, `municipio_venta`, `latitude` y `longitude`.

   - `obtener_preferencias_usuario(user_id)` -> list
      - Consulta la tabla `user_preferences` por `user_id` y retorna las preferencias del usuario como lista (parseando JSON). Si no hay preferencias o en caso de error, retorna lista vacía.

   - `obtener_historial_cliente(user_id)` -> dict
      - Consulta transacciones del cliente y devuelve los `productos` y `tiendas` conteniendo IDs únicos vistos en el historial.

   - `recomendar_productos(user_id, limit=30, k=10)` -> list[dict]
      - Obtiene productos (con `cargar_productos`) y determina productos de referencia usando las preferencias del usuario o su historial.
      - Vectoriza la columna `features` con `TfidfVectorizer`, construye un modelo KNN con distancia coseno y busca vecinos similares a los productos de referencia.
      - Devuelve una lista de diccionarios con `id` de los productos recomendados (ordenados por similitud) y limitada por `limit`.

   - `recomendar_tiendas(user_id, limit=15, k=10)` -> list[dict]
      - Similar al recomendador de productos pero trabaja a nivel de tiendas: identifica tiendas base relacionadas con los productos de referencia y busca otras tiendas similares utilizando TF-IDF sobre `nombre`, `barrio`, `municipio_venta`.
      - Devuelve una lista de diccionarios con `id` de las tiendas recomendadas.

   Si necesitas que el script haga salida más amigable (por ejemplo, mostrar nombre y barrio en lugar de sólo IDs), puedo añadir opciones para que devuelva más campos en lugar de solo `id`.
 
   ### TF-IDF + KNN — detalles importantes

   Las funciones `recomendar_productos` y `recomendar_tiendas` usan una canalización basada en TF-IDF seguida de un buscador KNN para identificar ítems similares. A continuación se explican los pasos y decisiones de diseño:

   - Construcción de features:
      - Para productos se concatena texto de campos relevantes (`nombre`, `descripcion`, `categoria_id`, `material_id`, `tecnica_id`, `municipio_venta`, `color`) en una columna `features` que actúa como documento representativo de cada producto.
      - Para tiendas se usa una concatenación similar de `nombre`, `barrio` y `municipio_venta`.

   - Vectorización TF-IDF:
      - Se utiliza `TfidfVectorizer` de scikit-learn para transformar la columna `features` en una matriz dispersa TF-IDF. Esto captura la importancia relativa de tokens entre documentos (productos/tiendas).

   - Búsqueda con KNN (NearestNeighbors):
      - Se crea un modelo `NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=...)` sobre la matriz TF-IDF.
      - Atención: scikit-learn implementa distancia de coseno, donde valores más bajos indican mayor similitud. En el código convertimos distancia → similitud con `similitud = 1 - distancia`.
      - Cuando el usuario tiene múltiples productos de referencia, el proceso busca vecinos para cada vector de referencia y obtiene distancias e índices con forma (n_referencias, n_neighbors). El código promedia las distancias sobre las referencias y luego convierte a similitud para obtener un ranking global.
      - Se usa `np.unique` sobre los índices resultantes para evitar duplicados cuando distintos productos de referencia devuelven el mismo vecino.

   - Parámetros clave:
      - `k` en las firmas (`recomendar_productos(..., k=10)`) determina cuántos vecinos locales buscar por cada item de referencia (tamaño del vecindario por referencia).
      - `limit` controla cuántos resultados finales devolver al usuario (después de filtrar y ordenar por similitud).
      - Internamente el modelo construye `n_neighbors=min(k, len(df))` para no pedir más vecinos que registros disponibles.

   - Exclusión y ordenamiento:
      - Después de obtener candidatos, el sistema excluye los productos o tiendas que ya aparecen como referencias (evita recomendar ítems ya vistos).
      - Los candidatos se ordenan por la similitud promedio descendente y se corta la lista final con `head(limit)`.

   - Casos límite y comportamiento:
      - Si el usuario no tiene preferencias ni historial, las funciones retornan `[]` (lista vacía).
      - Si ningún `product_id` de entrada existe en el DataFrame de productos, también se retorna `[]`.
      - Si la base de datos es muy grande, el uso de `algorithm='brute'` con TF-IDF puede ser costoso; para producción se recomienda precomputar la matriz TF-IDF y usar un índice de búsqueda aproximado (Annoy, Faiss, nmslib) o una estrategia por bloques.

   - Notas de rendimiento:
      - TF-IDF + KNN funciona bien para datasets pequeños/medianos y es sencillo de implementar y entender.
      - Para escalabilidad: cachear TF-IDF, persistir matrices o vectores, usar búsqueda aproximada, o reducir dimensionalidad (LSA) antes del KNN.

   Si quieres, puedo añadir un pequeño diagrama o ejemplo numérico (toy example) que muestre cómo se promedian las distancias y cómo quedan las similitudes finales.
## Estructura del Proyecto

- `app.py`: Servidor Flask y definición de endpoints
- `recommender.py`: Lógica principal del sistema de recomendaciones
- `config.py`: Configuración de la base de datos y variables de entorno
- `requirements.txt`: Lista de dependencias del proyecto

## Funcionamiento

El sistema utiliza técnicas de procesamiento de lenguaje natural para analizar las características de los productos, incluyendo:
- Nombre del producto
- Descripción
- Categoría
- Material
- Técnica de elaboración
- Ubicación
- Color

Basándose en estos datos, el sistema calcula la similitud entre productos y genera recomendaciones personalizadas para cada usuario, paralelamente toma cada producto y busca la tienda que le corresponde y usando la misma tecnica de procesamiento de lenguaje natural analiza las caracteriticas de:

 - Nombre
 - Barrio
 - Municipio de venta

Y asi mismo como en productos basándose en estos datos, el sistema calcula la similitud entre tiendas y genera recomendaciones personalizadas para cada usuario.


## Autores

- **Deimys Camargo** - [deimyscamargo](https://github.com/deimyscamargo)
- **Jesus Castillo** - [Jesusc0](https://github.com/Jesusc0)
- **Luis Martinez** - [Luismartco](https://github.com/Luismartco)