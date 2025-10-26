# Sistema de Recomendaciones Craftroute

Este proyecto implementa un sistema de recomendaciones para [Craftroute](https://github.com/Luismartco/Craftroutev2), una plataforma de comercio de artesanías. El sistema proporciona recomendaciones personalizadas de productos y tiendas para los usuarios basándose en técnicas de procesamiento de lenguaje natural y similitud de coseno.

## Características

- API REST desarrollada con Flask.
- Sistema de recomendación basado en contenido.
- Análisis de similitud usando TF-IDF y similitud de coseno.
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

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/Luismartco/RecomendacionesCraftroute.git
cd RecomendacionesCraftroute
```

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar las variables de entorno:
   - Crear un archivo `.env` en la raíz del proyecto
   - Definir las variables de conexión a la base de datos

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