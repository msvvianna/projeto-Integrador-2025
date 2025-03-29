import secrets
from importlib import metadata
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie, Query, security
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse, RedirectResponse, UJSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Response
from starlette import status
from starlette.responses import JSONResponse
import mysql.connector
from typing import Optional, Dict, Any

app = FastAPI(
    title="FastAPI",
    version=metadata.version("FastAPI"),
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
    default_response_class=UJSONResponse,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Database:
    def __init__(self, host="db", user="root", password="Allstar3", database="estoque", port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

    def __enter__(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

def execute_query(query: str, params: tuple = ()) -> Any:
    with Database() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()

def execute_update(query: str, params: tuple = ()) -> None:
    with Database() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def criar_tabelas():
    execute_update("CREATE DATABASE IF NOT EXISTS estoque")
    execute_update("USE estoque")
    execute_update("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL
        )
    """)
    execute_update("""
        CREATE TABLE IF NOT EXISTS produto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vonixx_extractus INT(10),
            vonixx_bactran INT(10),
            vonixx_sanitizante INT(10),
            vonixx_sintra INT(10)
        )
    """)
    execute_update("""
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
    if not execute_query("SELECT COUNT(*) FROM usuario")[0]['COUNT(*)']:
        execute_update("INSERT INTO usuario (nome, senha) VALUES ('Admin', '123')")
    if not execute_query("SELECT COUNT(*) FROM produto")[0]['COUNT(*)']:
        execute_update("INSERT INTO produto (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra) VALUES (1500, 1500, 1500, 1500)")

criar_tabelas()

def obter_usuario(usuario_id: int) -> Dict[str, Any]:
    usuario = execute_query("SELECT * FROM usuario WHERE id = %s", (usuario_id,))
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario[0]

def obter_agendamento(agendamento_id: int) -> Dict[str, Any]:
    agendamento = execute_query("SELECT * FROM agendamento WHERE id = %s", (agendamento_id,))
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return agendamento[0]

def obter_produto(produto_id: int) -> Dict[str, Any]:
    produto = execute_query("SELECT * FROM produto WHERE id = %s", (produto_id,))
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto[0]

def verificar_autenticacao(usuario_id: int = Cookie(None)):
    return usuario_id is not None

http_basic = HTTPBasic() # Instancia HTTPBasic

def verificar_usuario_logado(credentials: HTTPBasicCredentials = Depends(http_basic)) -> str:
    usuario = execute_query("SELECT * FROM usuario WHERE nome = %s", (credentials.username,))
    if usuario:
        usuario = usuario[0]
        senha_correta = secrets.compare_digest(credentials.password, usuario['senha'])
        if senha_correta:
            return credentials.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nome ou senha incorreto!",
        headers={"WWW-Authenticate": "Basic"},
    )

@app.get("/", response_class=HTMLResponse)
async def pagina_principal(request: Request, response: Response):
    usuario_id = request.cookies.get("usuario_id")
    if not usuario_id:
        return RedirectResponse(url="/login", status_code=303)

    usuario = obter_usuario(int(usuario_id))
    return templates.TemplateResponse("pagina_principal.html", {"request": request, "usuario": usuario})

@app.get("/login", response_class=HTMLResponse)
async def ler_login(request: Request, error_message: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})

@app.post("/login")
async def login(nome: str = Form(...), senha: str = Form(...), response: Response = None):
    usuario = execute_query("SELECT * FROM usuario WHERE nome = %s AND senha = %s", (nome, senha))
    if usuario:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="usuario_id", value=str(usuario[0]['id']))
        return response
    else:
        return RedirectResponse(url="/login?error_message=Credenciais inválidas", status_code=303)

@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="usuario_id")
    return RedirectResponse(url="/login", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    usuarios = execute_query("SELECT * FROM usuario")
    return templates.TemplateResponse("dashboard.html", {"request": request, "usuarios": usuarios})

@app.get("/cadastro", response_class=HTMLResponse)
async def ler_cadastro(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.post("/cadastrar")
async def cadastrar(nome: str = Form(...), senha: str = Form(...)):
    execute_update("INSERT INTO usuario (nome, senha) VALUES (%s, %s)", (nome, senha))
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/usuarios/{usuario_id}/editar", response_class=HTMLResponse)
async def editar_usuario_form(request: Request, usuario: dict = Depends(obter_usuario)):
    return templates.TemplateResponse("editar_usuario.html", {"request": request, "usuario": usuario})

@app.post("/usuarios/{usuario_id}/editar")
async def editar_usuario(usuario_id: int, nome: str = Form(...), senha: str = Form(...)):
    execute_update("UPDATE usuario SET nome = %s, senha = %s WHERE id = %s", (nome, senha, usuario_id))
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/usuarios/{usuario_id}/excluir")
async def excluir_usuario(usuario_id: int):
    execute_update("DELETE FROM usuario WHERE id = %s", (usuario_id,))
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/agendamentos", response_class=HTMLResponse)
async def listar_agendamentos(request: Request):
    agendamentos = execute_query("SELECT * FROM agendamento")
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
    vonixx_extractus: int = Form(0),
    vonixx_bactran: int = Form(0),
    vonixx_sanitizante: int = Form(0),
    vonixx_sintra: int = Form(0)
):
    produto = execute_query("SELECT * FROM produto WHERE id = 1")
    if produto:
        produto = produto[0]
        if (produto['vonixx_extractus'] >= vonixx_extractus and
            produto['vonixx_bactran'] >= vonixx_bactran and
            produto['vonixx_sanitizante'] >= vonixx_sanitizante and
            produto['vonixx_sintra'] >= vonixx_sintra):

            novo_extractus = produto['vonixx_extractus'] - vonixx_extractus
            novo_bactran = produto['vonixx_bactran'] - vonixx_bactran
            novo_sanitizante = produto['vonixx_sanitizante'] - vonixx_sanitizante
            novo_sintra = produto['vonixx_sintra'] - vonixx_sintra

            execute_update("""
                UPDATE produto
                SET vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
                WHERE id = 1
            """, (novo_extractus, novo_bactran, novo_sanitizante, novo_sintra))

            execute_update("""
                INSERT INTO agendamento (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra))

            return RedirectResponse(url="/agendamentos", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Estoque insuficiente para os produtos selecionados.")
    else:
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
    execute_update("""
        UPDATE agendamento
        SET cliente = %s, endereco = %s, telefone = %s, data_agendamento = %s, vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
        WHERE id = %s
    """, (cliente, endereco, telefone, data_agendamento, vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra, agendamento_id))
    return RedirectResponse(url="/agendamentos", status_code=303)

@app.post("/agendamentos/finalizar/{id}")
async def finalizar_agendamento(id: int):
    agendamento = execute_query("SELECT * FROM agendamento WHERE id = %s", (id,))
    if agendamento:
        execute_update("UPDATE agendamento SET status = 'concluído' WHERE id = %s", (id,))
        return RedirectResponse(url="/agendamentos", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

@app.get("/produtos", response_class=HTMLResponse)
async def listar_produtos(request: Request):
    produtos = execute_query("SELECT * FROM produto")
    return templates.TemplateResponse("produtos_lista.html", {"request": request, "produtos": produtos})

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
    execute_update("""
        INSERT INTO produto (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra)
        VALUES (%s, %s, %s, %s)
    """, (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra))
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
    execute_update("""
        UPDATE produto
        SET vonixx_extractus = %s, vonixx_bactran = %s, vonixx_sanitizante = %s, vonixx_sintra = %s
        WHERE id = %s
    """, (vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra, produto_id))
    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/produtos/{produto_id}/finalizar")
async def finalizar_produto(produto_id: int):
    execute_update("DELETE FROM produto WHERE id = %s", (produto_id,))
    return RedirectResponse(url="/produtos", status_code=303)

@app.get("/relatorios", response_class=HTMLResponse)
async def pagina_relatorios(request: Request):
    agendamentos = execute_query("SELECT DATE_FORMAT(data_agendamento, '%Y-%m-%d') AS mes, COUNT(*) AS quantidade FROM agendamento GROUP BY mes")
    agendamentos_meses = [a['mes'] for a in agendamentos]
    agendamentos_quantidades = [int(a['quantidade']) for a in agendamentos]

    produtos_utilizados = execute_query("SELECT SUM(vonixx_extractus) AS extractus, SUM(vonixx_bactran) AS bactran, SUM(vonixx_sanitizante) AS sanitizante, SUM(vonixx_sintra) AS sintra FROM agendamento")
    produtos_utilizados = {k: int(v) if v is not None else 0 for k, v in produtos_utilizados[0].items()}

    estoque_produtos = execute_query("SELECT vonixx_extractus, vonixx_bactran, vonixx_sanitizante, vonixx_sintra FROM produto")
    estoque_produtos = {k: int(v) if v is not None else 0 for k, v in estoque_produtos[0].items()}

    return templates.TemplateResponse("relatorios.html", {
        "request": request,
        "agendamentos_meses": agendamentos_meses,
        "agendamentos_quantidades": agendamentos_quantidades,
        "produtos_utilizados": produtos_utilizados,
        "estoque_produtos": estoque_produtos
    })

@app.get("/api/agendamentos/")
async def listar_agendamentos_api(
    status: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None)
):
    sql = "SELECT * FROM agendamento WHERE 1=1"
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

    agendamentos = execute_query(sql, tuple(params))
    return JSONResponse(content=agendamentos)

@app.get("/api/agendamentos/{agendamento_id}")
async def obter_agendamento_api(agendamento_id: int):
    agendamento = obter_agendamento(agendamento_id)
    return JSONResponse(content=agendamento)

@app.get("/docs", response_class=HTMLResponse)
async def get_docs(username: str = Depends(verificar_usuario_logado)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="docs")

@app.get("/redoc", response_class=HTMLResponse)
async def get_redoc(username: str = Depends(verificar_usuario_logado)) -> HTMLResponse:
    return get_redoc_html(openapi_url="/api/openapi.json", title="redoc")
