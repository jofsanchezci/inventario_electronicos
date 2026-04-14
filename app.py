from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "inventario.db"
IVA_RATE = 0.19

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-me"
app.config["DATABASE"] = str(DATABASE)


# -----------------------------
# Database helpers
# -----------------------------
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(app.config["DATABASE"])
    with closing(db.cursor()) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                marca TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK(cantidad >= 0),
                precio REAL NOT NULL CHECK(precio >= 0),
                descripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()
    db.close()


# -----------------------------
# Utility functions
# -----------------------------
def parse_form() -> dict[str, Any]:
    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()
    marca = request.form.get("marca", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    try:
        cantidad = int(request.form.get("cantidad", 0))
    except (TypeError, ValueError):
        cantidad = -1

    try:
        precio = float(request.form.get("precio", 0))
    except (TypeError, ValueError):
        precio = -1

    return {
        "nombre": nombre,
        "categoria": categoria,
        "marca": marca,
        "cantidad": cantidad,
        "precio": precio,
        "descripcion": descripcion,
    }


def validate_product(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data["nombre"]:
        errors.append("El nombre es obligatorio.")
    if not data["categoria"]:
        errors.append("La categoría es obligatoria.")
    if not data["marca"]:
        errors.append("La marca es obligatoria.")
    if data["cantidad"] < 0:
        errors.append("La cantidad debe ser un entero igual o mayor a 0.")
    if data["precio"] < 0:
        errors.append("El precio debe ser un número igual o mayor a 0.")
    return errors


def get_product(product_id: int) -> sqlite3.Row | None:
    db = get_db()
    return db.execute("SELECT * FROM productos WHERE id = ?", (product_id,)).fetchone()


@app.context_processor
def inject_helpers() -> dict[str, Any]:
    return {
        "iva_rate": IVA_RATE,
        "precio_con_iva": lambda precio: round(precio * (1 + IVA_RATE), 2),
        "valor_total": lambda cantidad, precio: round(cantidad * precio, 2),
    }


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index() -> str:
    db = get_db()
    query = request.args.get("q", "").strip()

    if query:
        productos = db.execute(
            """
            SELECT * FROM productos
            WHERE nombre LIKE ? OR categoria LIKE ? OR marca LIKE ?
            ORDER BY id DESC
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        productos = db.execute("SELECT * FROM productos ORDER BY id DESC").fetchall()

    total_items = db.execute("SELECT COALESCE(SUM(cantidad), 0) AS total FROM productos").fetchone()["total"]
    total_inventario = db.execute(
        "SELECT COALESCE(SUM(cantidad * precio), 0) AS total FROM productos"
    ).fetchone()["total"]

    return render_template(
        "index.html",
        productos=productos,
        query=query,
        total_items=total_items,
        total_inventario=round(total_inventario, 2),
    )


@app.route("/crear", methods=["GET", "POST"])
def crear_producto() -> str:
    if request.method == "POST":
        data = parse_form()
        errors = validate_product(data)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("form.html", producto=data, accion="Crear")

        db = get_db()
        db.execute(
            """
            INSERT INTO productos (nombre, categoria, marca, cantidad, precio, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["nombre"],
                data["categoria"],
                data["marca"],
                data["cantidad"],
                data["precio"],
                data["descripcion"],
            ),
        )
        db.commit()
        flash("Producto creado correctamente.", "success")
        return redirect(url_for("index"))

    producto_vacio = {
        "nombre": "",
        "categoria": "",
        "marca": "",
        "cantidad": 0,
        "precio": 0,
        "descripcion": "",
    }
    return render_template("form.html", producto=producto_vacio, accion="Crear")


@app.route("/editar/<int:product_id>", methods=["GET", "POST"])
def editar_producto(product_id: int) -> str:
    producto = get_product(product_id)
    if producto is None:
        flash("El producto solicitado no existe.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data = parse_form()
        errors = validate_product(data)
        if errors:
            for error in errors:
                flash(error, "error")
            producto_data = dict(data)
            producto_data["id"] = product_id
            return render_template("form.html", producto=producto_data, accion="Editar")

        db = get_db()
        db.execute(
            """
            UPDATE productos
            SET nombre = ?, categoria = ?, marca = ?, cantidad = ?, precio = ?, descripcion = ?
            WHERE id = ?
            """,
            (
                data["nombre"],
                data["categoria"],
                data["marca"],
                data["cantidad"],
                data["precio"],
                data["descripcion"],
                product_id,
            ),
        )
        db.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", producto=producto, accion="Editar")


@app.route("/eliminar/<int:product_id>", methods=["POST"])
def eliminar_producto(product_id: int) -> str:
    producto = get_product(product_id)
    if producto is None:
        flash("El producto solicitado no existe.", "error")
    else:
        db = get_db()
        db.execute("DELETE FROM productos WHERE id = ?", (product_id,))
        db.commit()
        flash("Producto eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/detalle/<int:product_id>")
def detalle_producto(product_id: int) -> str:
    producto = get_product(product_id)
    if producto is None:
        flash("El producto solicitado no existe.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", producto=producto)


if __name__ == "__main__":
    os.makedirs(BASE_DIR / "data", exist_ok=True)
    init_db()
    app.run(debug=True)
