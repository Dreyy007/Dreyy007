from flask import Flask, request, render_template, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "segredo"


# CONEXÃO
def conectar():
    return sqlite3.connect("clinica.db")


# CRIAR TABELAS
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consultas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        medico TEXT,
        data TEXT,
        hora TEXT
    )
    """)

    conn.commit()
    conn.close()


criar_tabelas()


# HOME
@app.route("/")
def home():
    return render_template("home.html")


# LOGIN PAGE
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# REGISTER PAGE
@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


# CADASTRO (SEMPRE PACIENTE)
@app.route("/register", methods=["POST"])
def register():
    data = request.form

    conn = conectar()
    cursor = conn.cursor()

    # Verifica email duplicado
    cursor.execute("SELECT * FROM usuarios WHERE email=?", (data["email"],))
    if cursor.fetchone():
        conn.close()
        flash("Email já cadastrado")
        return redirect("/register")

    senha_hash = generate_password_hash(data["senha"])

    # 👇 FORÇA COMO PACIENTE
    tipo = "paciente"

    cursor.execute("""
        INSERT INTO usuarios (nome, email, senha, tipo)
        VALUES (?, ?, ?, ?)
    """, (data["nome"], data["email"], senha_hash, tipo))

    conn.commit()
    conn.close()

    flash("Conta criada com sucesso!")
    return redirect("/login")


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.form

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email=?", (data["email"],))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[3], data["senha"]):
        session["user_id"] = user[0]
        session["nome"] = user[1]
        session["tipo"] = user[4]
        return redirect("/dashboard")
    else:
        flash("Email ou senha inválidos")
        return redirect("/login")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT medico, data, hora
        FROM consultas
        WHERE usuario_id=?
    """, (session["user_id"],))

    consultas = cursor.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        nome=session["nome"],
        tipo=session["tipo"],
        consultas=consultas
    )


# AGENDAR CONSULTA (SÓ PACIENTE)
@app.route("/agendar", methods=["POST"])
def agendar():
    if "user_id" not in session:
        return redirect("/login")

    # 👇 BLOQUEIO POR TIPO
    if session["tipo"] != "paciente":
        return "Acesso negado"

    data = request.form

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO consultas (usuario_id, medico, data, hora)
        VALUES (?, ?, ?, ?)
    """, (session["user_id"], data["medico"], data["data"], data["hora"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)