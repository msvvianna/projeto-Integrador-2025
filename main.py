import app
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
from fastapi.staticfiles import StaticFiles
from fastapi import Response
import json
from typing import Optional

from starlette.responses import JSONResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def conectar_banco():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="Allstar3",
        database="estoque",
        port=3306

    )

def criar_tabelas():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Cria o banco de dados se não existir
    cursor.execute("CREATE DATABASE IF NOT EXISTS estoque")
    cursor.execute("USE estoque")

    # Cria a tabela usuario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL
        )
    """)

    # Cria a tabela produto
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vonixx_extractus INT(10),
            vonixx_bactran INT(10),
            vonixx_sanitizante INT(10),
            vonixx_sintra INT(10)
        )
    """)

    # Cria a tabela agendamento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamento (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cliente VARCHAR(255) NOT NULL,
            endereco VARCHAR(255) NOT NULL,
            telefone VARCHAR(20) NOT NULL,
            data_agendamento VARCHAR(255) NOT NULL,
            vonixx_extractus INT(10),
            vonixx_bactran INT(10),
            vonixx_sanitizante INT(10),
            vonixx_sintra INT(10),
            status VARCHAR(20) DEFAULT 'pendente'
        )
    """)

    # Verifica se a tabela usuario está vazia e insere dados se necessário
    cursor.execute("SELECT COUNT(*) FROM usuario")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuario (nome, senha) VALUES ('Admin', 123)")

    # Verifica se a tabela produto está vazia e insere dados se necessário
    cursor.execute("SELECT COUNT(*) FROM produto")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO produto (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra) VALUES (1500, 1500, 1500, 1500)")

    conexao.commit()
    cursor.close()
    conexao.close()

criar_tabelas() # Cria as tabelas e insere dados ao iniciar a aplicação

def obter_usuario(usuario_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM usuario WHERE id = %s"
    val = (usuario_id,)
    cursor.execute(sql, val)
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

def obter_agendamento(agendamento_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM agendamento WHERE id = %s"
    val = (agendamento_id,)
    cursor.execute(sql, val)
    agendamento = cursor.fetchone()
    cursor.close()
    conexao.close()
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return agendamento

def obter_produto(produto_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM produto WHERE id = %s"
    val = (produto_id,)
    cursor.execute(sql, val)
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

def verificar_autenticacao(usuario_id: int = Cookie(None)):
    return usuario_id is not None

# Pagina principal
@app.get("/", response_class=HTMLResponse)
async def pagina_principal(request: Request, response: Response):
    usuario_id = request.cookies.get("usuario_id")
    if not usuario_id:
        return RedirectResponse(url="/login", status_code=303)

    usuario = obter_usuario(int(usuario_id))  # Obtenha o usuário do banco de dados

    if not usuario:
        response.delete_cookie("usuario_id")  # Remova o cookie se o usuário não for encontrado
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("pagina_principal.html", {"request": request, "usuario": usuario})

# Login e usuários
@app.get("/login", response_class=HTMLResponse)
async def ler_login(request: Request, error_message: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})

@app.post("/login")
async def login(nome: str = Form(...), senha: str = Form(...), response: Response = None):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM usuario WHERE nome = %s AND senha = %s"
    val = (nome, senha)
    cursor.execute(sql, val)
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()

    if usuario:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="usuario_id", value=str(usuario['id']))
        return response
    else:
        return RedirectResponse(url="/login?error_message=Credenciais inválidas", status_code=303)

@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="usuario_id")  # Remove o cookie ao fazer logout
    return RedirectResponse(url="/login", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM usuario"
    cursor.execute(sql)
    usuarios = cursor.fetchall()
    cursor.close()
    conexao.close()
    return templates.TemplateResponse("dashboard.html", {"request": request, "usuarios": usuarios})

@app.get("/cadastro", response_class=HTMLResponse)
async def ler_cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.post("/cadastrar")
async def cadastrar(nome: str = Form(...), senha: str = Form(...)):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = "INSERT INTO usuario (nome, senha) VALUES (%s, %s)"
    val = (nome, senha)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/usuarios/{usuario_id}/editar", response_class=HTMLResponse)
async def editar_usuario_form(request: Request, usuario: dict = Depends(obter_usuario)):
    return templates.TemplateResponse("editar_usuario.html", {"request": request, "usuario": usuario})

@app.post("/usuarios/{usuario_id}/editar")
async def editar_usuario(usuario_id: int, nome: str = Form(...), senha: str = Form(...)):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = "UPDATE usuario SET nome = %s, senha = %s WHERE id = %s"
    val = (nome, senha, usuario_id)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/usuarios/{usuario_id}/excluir")
async def excluir_usuario(usuario_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = "DELETE FROM usuario WHERE id = %s"
    val = (usuario_id,)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/dashboard", status_code=303)

# Agendamentos

@app.get("/agendamentos", response_class=HTMLResponse)
async def listar_agendamentos(request: Request):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    # Busca todos os agendamentos
    cursor.execute("SELECT * FROM agendamento")
    agendamentos = cursor.fetchall()

    cursor.close()
    conexao.close()

    return templates.TemplateResponse("agendamentos_lista.html", {"request": request, "agendamentos": agendamentos})

@app.get("/agendamentos/novo", response_class=HTMLResponse)
async def agendamento_form(request: Request):
    return templates.TemplateResponse("agendamento_form.html", {"request": request})

@app.post("/agendamentos/novo")
async def criar_agendamento(
    cliente: str = Form(...),
    endereco: str = Form(...),
    telefone: str = Form(...),
    data_agendamento: str = Form(...),
    vonixx_extractus: int = Form(0),  # Valor padrão 0 se não fornecido
    vonixx_bactran: int = Form(0),
    vonixx_sanitizante: int = Form(0),
    vonixx_sintra: int = Form(0)
):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Obter estoque atual dos produtos
    cursor.execute("SELECT * FROM produto WHERE id = 1") # Assumindo que há apenas 1 registro na tabela produto
    produto = cursor.fetchone()

    if produto:
        # Verificar estoque suficiente
        if (produto[1] >= vonixx_extractus and
            produto[2] >= vonixx_bactran and
            produto[3] >= vonixx_sanitizante and
            produto[4] >= vonixx_sintra):

            # Subtrair produtos do estoque
            novo_extractus = produto[1] - vonixx_extractus
            novo_bactran = produto[2] - vonixx_bactran
            novo_sanitizante = produto[3] - vonixx_sanitizante
            novo_sintra = produto[4] - vonixx_sintra

            cursor.execute("""
                UPDATE produto
                SET vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
                WHERE id = 1
            """, (novo_extractus, novo_bactran, novo_sanitizante, novo_sintra))

            # Inserir agendamento
            sql = """
                INSERT INTO agendamento (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
            cursor.execute(sql, val)

            conexao.commit()
            cursor.close()
            conexao.close()
            return RedirectResponse(url="/agendamentos", status_code=303)
        else:
            cursor.close()
            conexao.close()
            raise HTTPException(status_code=400, detail="Estoque insuficiente para os produtos selecionados.")
    else:
        cursor.close()
        conexao.close()
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

@app.get("/agendamentos/{agendamento_id}/editar", response_class=HTMLResponse)
async def agendamento_editar_form(request: Request, agendamento: dict = Depends(obter_agendamento)):
    return templates.TemplateResponse("agendamento_editar.html", {"request": request, "agendamento": agendamento})

@app.post("/agendamentos/{agendamento_id}/editar")
async def atualizar_agendamento(
    agendamento_id: int,
    cliente: str = Form(...),
    endereco: str = Form(...),
    telefone: str = Form(...),
    data_agendamento: str = Form(...),
    vonixx_extractus: int = Form(None),
    vonixx_bactran: int = Form(None),
    vonixx_sanitizante: int = Form(None),
    vonixx_sintra: int = Form(None)
):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = """
        UPDATE agendamento
        SET cliente = %s, endereco = %s, telefone = %s, data_agendamento = %s, vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
        WHERE id = %s
    """
    val = (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra, agendamento_id)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/agendamentos", status_code=303)

@app.post("/agendamentos/finalizar/{id}")
async def finalizar_agendamento(id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Verifica se o agendamento existe
    cursor.execute("SELECT * FROM agendamento WHERE id = %s", (id,))
    agendamento = cursor.fetchone()

    if agendamento:
        # Atualiza o status do agendamento para "concluído"
        sql = "UPDATE agendamento SET status = 'concluído' WHERE id = %s"
        val = (id,)
        cursor.execute(sql, val)

        conexao.commit()
        cursor.close()
        conexao.close()

        return RedirectResponse(url="/agendamentos", status_code=303)
    else:
        cursor.close()
        conexao.close()
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")


# Produtos
@app.get("/produtos", response_class=HTMLResponse)
async def listar_produtos(request: Request):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    sql = "SELECT * FROM produto"
    cursor.execute(sql)
    produtos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return templates.TemplateResponse("produtos_lista.html", {"request": request,  "produtos": produtos})

@app.get("/produtos/novo", response_class=HTMLResponse)
async def produto_form(request: Request):
    return templates.TemplateResponse("produto_form.html", {"request": request})

@app.post("/produtos/novo")
async def criar_produto(
    vonixx_extractus: int = Form(None),
    vonixx_bactran: int = Form(None),
    vonixx_sanitizante: int = Form(None),
    vonixx_sintra: int = Form(None)
):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = """
        INSERT INTO produto (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
        VALUES (%s, %s, %s, %s)
    """
    val = (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/{produto_id}/editar", response_class=HTMLResponse)
async def produto_editar_form(request: Request, produto: dict = Depends(obter_produto)):
    return templates.TemplateResponse("produto_editar.html", {"request": request, "produto": produto})

@app.post("/produtos/{produto_id}/editar")
async def atualizar_produto(
    produto_id: int,
    vonixx_extractus: int = Form(None),
    vonixx_bactran: int = Form(None),
    vonixx_sanitizante: int = Form(None),
    vonixx_sintra: int = Form(None)
):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = """
        UPDATE produto
        SET vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
        WHERE id = %s
    """
    val = (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra, produto_id)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/{produto_id}/finalizar")
async def finalizar_produto(produto_id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    sql = "DELETE FROM produto WHERE id = %s"
    val = (produto_id,)
    cursor.execute(sql, val)
    conexao.commit()
    cursor.close()
    conexao.close()
    return RedirectResponse(url="/produtos", status_code=303)


@app.get("/relatorios", response_class=HTMLResponse)
async def pagina_relatorios(request: Request):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    # Dados para gráfico de agendamentos
    cursor.execute("SELECT DATE_FORMAT(data_agendamento, '%Y-%m-%d') AS mes, COUNT(*) AS quantidade FROM agendamento GROUP BY mes")
    agendamentos = cursor.fetchall()
    agendamentos_meses = [a['mes'] for a in agendamentos]
    agendamentos_quantidades = [int(a['quantidade']) for a in agendamentos]  # Convertendo para int

    # Dados para gráfico de produtos utilizados
    cursor.execute("SELECT SUM(vonixx_extractus) AS extractus, SUM(vonixx_bactran) AS bactran, SUM(vonixx_sanitizante) AS sanitizante, SUM(vonixx_sintra) AS sintra FROM agendamento")
    produtos_utilizados = cursor.fetchone() or {}
    produtos_utilizados = {k: int(v) if v is not None else 0 for k, v in produtos_utilizados.items()}  # Convertendo para int

    # Dados para gráfico de estoque de produtos
    cursor.execute("SELECT vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra FROM produto")
    estoque_produtos = cursor.fetchone() or {}
    estoque_produtos = {k: int(v) if v is not None else 0 for k, v in estoque_produtos.items()}  # Convertendo para int

    cursor.close()
    conexao.close()

    return templates.TemplateResponse("relatorios.html", {
        "request": request,
        "agendamentos_meses": agendamentos_meses,
        "agendamentos_quantidades": agendamentos_quantidades,
        "produtos_utilizados": produtos_utilizados,
        "estoque_produtos": estoque_produtos
    })

# API para Agendamentos
@app.get("/api/agendamentos/")
async def listar_agendamentos_api(
    status: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None)
):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    sql = "SELECT * FROM agendamento WHERE 1=1"  # Inicia com uma condição sempre verdadeira

    params = []

    if status:
        sql += " AND status = %s"
        params.append(status)
    if data_inicio:
        sql += " AND data_agendamento >= %s"
        params.append(data_inicio)
    if data_fim:
        sql += " AND data_agendamento <= %s"
        params.append(data_fim)

    cursor.execute(sql, params)
    agendamentos = cursor.fetchall()

    cursor.close()
    conexao.close()

    return JSONResponse(content=agendamentos)

@app.get("/api/agendamentos/{agendamento_id}")
async def obter_agendamento_api(agendamento_id: int):
    agendamento = obter_agendamento(agendamento_id)
    return JSONResponse(content=agendamento)
