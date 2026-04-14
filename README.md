# Gestor de Inventario para Tienda de Electrónicos

Proyecto web desarrollado con **Flask** y **SQLite** para administrar el inventario de una tienda de productos electrónicos.

## Funcionalidades

- Registro de productos.
- Edición de productos existentes.
- Eliminación de productos.
- Consulta de detalle por producto.
- Búsqueda por nombre, categoría o marca.
- Cálculo de precio con IVA (19%).
- Cálculo del valor total por producto y del inventario general.
- Persistencia local con SQLite.

## Estructura del proyecto

```bash
inventario_electronicos/
│── app.py
│── requirements.txt
│── README.md
│── data/
│   └── inventario.db   # se crea automáticamente al ejecutar
│── static/
│   └── styles.css
└── templates/
    ├── base.html
    ├── index.html
    ├── form.html
    └── detail.html
```

## Requisitos

- Python 3.10 o superior
- pip

## Instalación y ejecución

1. Crear entorno virtual:

```bash
python -m venv venv
```

2. Activar entorno virtual:

### En Windows
```bash
venv\Scripts\activate
```

### En Linux o macOS
```bash
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:

```bash
python app.py
```

5. Abrir en el navegador:

```bash
http://127.0.0.1:5000
```

## Observaciones

- La base de datos se crea automáticamente en `data/inventario.db`.
- Puede cambiar la tasa de IVA desde la constante `IVA_RATE` en `app.py`.
- Para producción, cambie la `SECRET_KEY`.

## Posibles mejoras

- Autenticación de usuarios.
- Carga masiva desde CSV o Excel.
- Reportes de inventario.
- Alertas de stock bajo.
- API REST para integración con frontend moderno.
