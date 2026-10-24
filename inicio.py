
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pandas as pd
from openpyxl import Workbook, load_workbook
import os
from zoneinfo import ZoneInfo
app = Flask(__name__)

app.secret_key = "segredo"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///america_lanche.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 👉 cria o db UMA vez só
db = SQLAlchemy(app)

# -------------------------------
# Modelos
# -------------------------------
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(50), nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    complemento = db.Column(db.String(100))
    pagamento = db.Column(db.String(20))
    observacao = db.Column(db.String(200))
    itens = db.Column(db.Text)  # lista de itens em string
    total = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------------
# Criação das tabelas e usuário inicial
# -------------------------------
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(usuario="American.Lc").first():
        novo = Usuario(usuario="American.Lc", senha="AMRIO")
        db.session.add(novo)
        db.session.commit()
        

from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os


from openpyxl import Workbook, load_workbook
from datetime import datetime
from zoneinfo import ZoneInfo
import os

def salvar_em_planilha(nome, telefone, bairro, cidade, complemento, pagamento, observacao, carrinho, total_final):
    arquivo = "pedidos.xlsx"

    # cria planilha se não existir
    if not os.path.exists(arquivo):
        wb = Workbook()
        ws = wb.active
        ws.title = "Pedidos"
        ws.append([
            "Data/Hora", "Nome", "Telefone", "Bairro", "Cidade", "Complemento",
            "Pagamento", "Observação", "Itens", "Adicionais", "Total", "Status"
        ])
        wb.save(arquivo)

    # abre planilha existente
    wb = load_workbook(arquivo)

    # garante que a aba "Pedidos" exista
    if "Pedidos" not in wb.sheetnames:
        ws = wb.create_sheet("Pedidos")
        ws.append([
            "Data/Hora", "Nome", "Telefone", "Bairro", "Cidade", "Complemento",
            "Pagamento", "Observação", "Itens", "Adicionais", "Total", "Status"
        ])
    else:
        ws = wb["Pedidos"]

    # pega data/hora de Brasília automaticamente
    data_hora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

    # adiciona cada item do carrinho separadamente
    for d in carrinho:
        adicionais = ", ".join(d["adicionais"]) if d["adicionais"] else ""
        ws.append([
            data_hora,
            nome,
            telefone,
            bairro,
            cidade,
            complemento,
            pagamento,
            observacao,
            f"{d['item']} x{d['quantidade']} (Subtotal R${d['subtotal']:.2f})",
            adicionais,
            total_final,
            "Recebido"   # status inicial
        ])

    wb.save(arquivo)

# carregar planilha
xls = pd.ExcelFile("static/cardapio.xlsx")

# Cardápio
df_cardapio = pd.read_excel(xls, sheet_name="Cardapio")
df_cardapio.columns = df_cardapio.columns.str.strip().str.lower()
df_cardapio["preco"] = (
    df_cardapio["preco"].astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(",", ".", regex=False)
)
df_cardapio["preco"] = pd.to_numeric(df_cardapio["preco"], errors="coerce").fillna(0).astype(float)
precos_cardapio = dict(zip(df_cardapio["item"], df_cardapio["preco"]))

# Adicionais
df_adicionais = pd.read_excel(xls, sheet_name="Adicionais")
df_adicionais.columns = df_adicionais.columns.str.strip().str.lower()
df_adicionais["preco"] = (
    df_adicionais["preco"].astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(",", ".", regex=False)
)
df_adicionais["preco"] = pd.to_numeric(df_adicionais["preco"], errors="coerce").fillna(0).astype(float)
precos_adicionais = dict(zip(df_adicionais["adicionais"], df_adicionais["preco"]))
import unicodedata
import re




def normalizar_nome(nome):
    nome = str(nome)  # garante que sempre seja string
    nome = ''.join(
        c for c in unicodedata.normalize('NFD', nome)
        if unicodedata.category(c) != 'Mn'
    )
    nome = re.sub(r'[^a-zA-Z0-9]', '', nome).lower()
    return nome

precos_normalizados = {normalizar_nome(k): v for k, v in precos_cardapio.items()}


# cria versão normalizada da planilha
precos_normalizados = {normalizar_nome(k): v for k, v in precos_cardapio.items()}


# -------------------------------
# Controle de status da loja
# -------------------------------
status_manual = None  # pode ser "Aberto", "Fechado" ou None (automático)

def status_loja_automatico():
    hoje = datetime.now().weekday()  # segunda=0 ... domingo=6
    hora = datetime.now().hour
    if hoje in [4, 5, 6] and (18 <= hora < 22):  # sexta, sábado, domingo das 18h às 22h
        return "Aberto"
    return "Fechado"

# -------------------------------
# Rotas de login/logout
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        user = Usuario.query.filter_by(usuario=usuario, senha=senha).first()
        if user:
            session["usuario"] = usuario
            return redirect("/controle")
        else:
            return "Usuário ou senha inválidos"
    return """
        <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
            }
            form {
                max-width: 400px;
                margin: auto;
            }
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
            }
            input[type="submit"] {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #45a049;
            }
        </style>
        <form method="post">
            Usuário: <input type="text" name="usuario"><br>
            Senha: <input type="password" name="senha"><br>
            <input type="submit" value="Entrar">
        </form>
    """

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/login")

# -------------------------------
# Rotas de controle da loja
# -------------------------------
@app.route("/controle")
def controle():
    if "usuario" not in session:
        return redirect("/login")

    # decide status atual
    status_atual = status_manual if status_manual else status_loja_automatico()
    classe = "status-aberto" if status_atual == "Aberto" else "status-fechado"

    modo = "Manual" if status_manual else "Automático"

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Painel de Controle</title>
        <style>
            body {{
                border: 6px solid black;
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
            }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
            a {{ color: #007BFF; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .status-aberto {{ color: green; font-weight: bold; font-size: 24px; }}
            .status-fechado {{ color: red; font-weight: bold; font-size: 24px; }}
            .btn {{ display: inline-block; margin: 10px; padding: 10px 20px;
                   text-decoration: none; color: white; border-radius: 5px; font-weight: bold; }}
            .btn-aberto {{ background-color: green; }}
            .btn-fechado {{ background-color: red; }}
            .btn-auto {{ background-color: orange; }}
            .btn-logout {{ background-color: gray; }}
        </style>
    </head>
    <body>
        <h1>Painel de Controle</h1>

        <h2>Status atual: <span class='{classe}'>{status_atual}</span> ({modo})</h2>

        <a href='/alterar_status/Aberto' class='btn btn-aberto'>Abrir Loja</a>
        <a href='/alterar_status/Fechado' class='btn btn-fechado'>Fechar Loja</a>
        <a href='/alterar_status/auto' class='btn btn-auto'>Voltar para automático</a>
        <br><br>
        <a href='/pedidos' class='btn btn-auto'>Ver Pedidos</a>
        <a href='/logout' class='btn btn-logout'>Sair</a>
    </body>
    </html>
    """
    
@app.route("/alterar_status/<novo_status>")
def alterar_status(novo_status):
    global status_manual
    if "usuario" not in session:
        return redirect("/login")

    if novo_status in ["Aberto", "Fechado"]:
        status_manual = novo_status
    elif novo_status == "auto":
        status_manual = None
    else:
        # Se o parâmetro não for válido, volta para a página inicial
        return redirect("/")

    # Sempre retorna algo válido
    return redirect("/")


if os.path.exists("static/cardapio.xlsx"):
    df = pd.read_excel("static/cardapio.xlsx")
    df.columns = df.columns.str.strip().str.lower()
    precos = dict(zip(df["item"], df["preco"]))
    ingredientes = dict(zip(df["item"], df["ingredientes"])) if "ingredientes" in df.columns else {}
else:
    precos = {}
    ingredientes = {}
# -------------------------------
# Página inicial
# -------------------------------
@app.route("/")
def index():
    if not os.path.exists("static/cardapio.xlsx"):
        return "Arquivo Cardapio.xlsx não encontrado", 500

    df = pd.read_excel("static/cardapio.xlsx")
    df.columns = df.columns.str.strip().str.lower()

    precos = dict(zip(df["item"], df["preco"]))
    ingredientes = dict(zip(df["item"], df["ingredientes"])) if "ingredientes" in df.columns else {}

    status = status_manual if status_manual else status_loja_automatico()

    return render_template("inicio.html", precos=precos, ingredientes=ingredientes, status=status)


# -------------------------------
# Taxas de entrega e finalização
# -------------------------------
taxas_entrega = {
    "Rio América": 2.00, "Centro": 7.00, "Belvedere": 8.00,
    "São Donato": 12.00, "Coxia Rica": 12.00, "Santana": 10.00,
    "Rio Salto": 5.00, "Pirago": 6.00, "Rio Caeté": 7.00,
    "Rio Deserto": 8.00, "Estação": 8.00, "De Vila": 10.00,
    "São Pedro": 12.00, "Nova Itália": 8.00, "Rio Carvão": 8.00,
    "Rio Carvão Baixo": 10.00
}

@app.route("/finalizar", methods=["POST"])
def finalizar():
    carrinho = session.get("carrinho", [])
    if not carrinho:
        return "Carrinho vazio!", 400

    nome = request.form.get("nome", "")
    telefone = request.form.get("telefone", "")
    bairro = request.form.get("bairro", "")
    cidade = request.form.get("cidade", "")
    complemento = request.form.get("complemento", "")
    observacao = request.form.get("observacao", "")
    pagamento = request.form.get("pagamento", "")

    # atualiza adicionais escolhidos
    for dados in carrinho:
        novos_adicionais = []
        for adicional, preco in precos_adicionais.items():
            campo = f"adicional_{dados['item']}_{adicional}"
            qtd = int(request.form.get(campo, 0))
            if qtd > 0:
                novos_adicionais.append(f"{adicional} x{qtd}")
                dados["subtotal"] += preco * qtd
        if novos_adicionais:
            dados["adicionais"].extend(novos_adicionais)

    total = sum([d["subtotal"] for d in carrinho])
    taxa_entrega = taxas_entrega.get(bairro, 0.0)
    total_final = total + taxa_entrega

    # monta mensagem para WhatsApp
    mensagem = "🍔 Pedido finalizado!\n\n"
    mensagem += f"👤 Nome: {nome}\n📞 Telefone: {telefone}\n"
    mensagem += f"📍 Bairro: {bairro}, {cidade}\n🏠 Complemento: {complemento}\n"
    mensagem += "----------------------------\nItens do pedido:\n"

    for dados in carrinho:
        mensagem += f"- {dados['item']} x{dados['quantidade']}\n"
        if dados["adicionais"]:
            mensagem += "   + Adicionais: " + ", ".join(dados["adicionais"]) + "\n"
        mensagem += f"   Total: R${dados['subtotal']:.2f}\n"

    mensagem += f"\n🛒 Total produtos: R${total:.2f}\n"
    mensagem += f"🚚 Taxa de entrega: R${taxa_entrega:.2f}\n"
    mensagem += f"💵 Total final: R${total_final:.2f}\n"
    mensagem += f"💳 Pagamento: {pagamento}\n📝 Observações: {observacao}\n"
    mensagem += "\nObrigado pela compra! 🙏"

    # limpa carrinho
    session.pop("carrinho")

    # envia para WhatsApp
    mensagem_link = mensagem.replace("\n", "%0A")
    numero_whats = "48996598873"
    link = f"https://wa.me/{numero_whats}?text={mensagem_link}"

    # 👉 só salva na planilha DEPOIS do envio
    # aqui você pode usar um botão de confirmação na página de retorno
    salvar_em_planilha(nome, telefone, bairro, cidade, complemento, pagamento, observacao, carrinho, total_final)

    return redirect(link)

@app.template_filter("real")
def format_real(value):
    
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except Exception:
        return value


@app.route("/carrinho", methods=["POST"])
def carrinho():
    carrinho = []

    for campo, valor in request.form.items():
        if campo.startswith("quantidade_"):
            try:
                qtd = int(valor)
            except ValueError:
                qtd = 0

            if qtd > 0:
                nome_item = campo.replace("quantidade_", "").replace("_", " ")
                preco_item = precos.get(nome_item, 0.0)

                # 👉 cria entradas separadas para cada unidade
                for _ in range(qtd):
                    carrinho.append({
                        "item": nome_item,
                        "quantidade": 1,
                        "preco": preco_item,
                        "subtotal": preco_item,
                        "adicionais": []
                    })

    # salva carrinho na sessão
    session["carrinho"] = carrinho

    # pega o total calculado na página inicial
    total = float(request.form.get("total", 0))

    return render_template(
        "carrinho.html",
        carrinho=carrinho,
        adicionais=precos_adicionais,
        total=total
    )


@app.route("/pedidos")
def pedidos():
    if "usuario" not in session:
        return redirect("/login")

    arquivo = "pedidos.xlsx"

    # cria o arquivo se não existir
    if not os.path.exists(arquivo):
        wb = Workbook()
        ws = wb.active
        ws.title = "Pedidos"
        ws.append([
            "Data/Hora", "Nome", "Telefone", "Bairro", "Cidade", "Complemento",
            "Pagamento", "Observação", "Itens", "Adicionais", "Total", "Status"
        ])
        wb.save(arquivo)

    wb = load_workbook(arquivo)
    ws = wb["Pedidos"]

    hoje = datetime.now().strftime("%d/%m/%Y")  # só mostra pedidos do dia atual

    # agrupar pedidos por cliente
    pedidos_por_cliente = {}
    linha = 2
    for row in ws.iter_rows(min_row=2, values_only=True):
        data_hora = str(row[0])
        if data_hora.startswith(hoje):
            nome = row[1]
            telefone = row[2]
            chave = f"{nome} ({telefone})"
            if chave not in pedidos_por_cliente:
                pedidos_por_cliente[chave] = []
            pedidos_por_cliente[chave].append((linha, row))
        linha += 1

    # montar HTML
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Pedidos por Cliente</title>
        <meta http-equiv="refresh" content="5"> <!-- Atualiza sozinho a cada 5s -->
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { margin-bottom: 20px; }
            h2 { margin-top: 30px; color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .btn { padding: 4px 8px; margin: 2px; border: none; cursor: pointer; }
            .pronto { background-color: #4CAF50; color: white; }
            .entregue { background-color: #2196F3; color: white; }
            .imprimir { background-color: orange; color: white; }
            .limpar { background-color: red; color: white; }
        </style>
        <script>
            function imprimirCliente(clienteId) {
                var conteudo = document.getElementById(clienteId).innerHTML;
                var janela = window.open('', '', 'width=800,height=600');
                janela.document.write('<html><head><title>Imprimir</title></head><body>');
                janela.document.write(conteudo);
                janela.document.write('</body></html>');
                janela.document.close();
                janela.print();
            }
        </script>
    </head>
    <body>
        <h1>Pedidos de Hoje por Cliente</h1>
    """

    for cliente, pedidos in pedidos_por_cliente.items():
        cliente_id = cliente.replace(" ", "_").replace("(", "").replace(")", "")
        html += f"<div id='{cliente_id}'>"
        html += f"<h2>{cliente}</h2>"
        html += "<table><tr><th>Data/Hora</th><th>Bairro</th><th>Cidade</th><th>Complemento</th><th>Pagamento</th><th>Observação</th><th>Itens</th><th>Adicionais</th><th>Total</th><th>Status</th><th>Ações</th></tr>"
        for linha, pedido in pedidos:
            if len(pedido) == 12:
                data_hora, nome, telefone, bairro, cidade, complemento, pagamento, observacao, itens, adicionais, total, status = pedido
            elif len(pedido) == 11:
                data_hora, nome, telefone, bairro, cidade, complemento, pagamento, observacao, itens, adicionais, total = pedido
                status = "Recebido"  # valor padrão para pedidos antigos
            else:
                continue

            cor = "green" if status == "Pronto" else "blue" if status == "Entregue" else "black"
            html += "<tr>"
            html += f"<td>{data_hora}</td><td>{bairro}</td><td>{cidade}</td><td>{complemento}</td><td>{pagamento}</td><td>{observacao}</td><td>{itens}</td><td>{adicionais}</td><td>R${float(total):.2f}</td><td style='color:{cor};font-weight:bold'>{status}</td>"
            html += f"""
                <td>
                    <a href='/pedido/{linha}/status/Pronto'><button class='btn pronto'>Pronto</button></a>
                    <a href='/pedido/{linha}/status/Entregue'><button class='btn entregue'>Entregue</button></a>
                </td>
            """
            html += "</tr>"
        html += "</table>"
        html += f"<button class='btn imprimir' onclick=\"imprimirCliente('{cliente_id}')\">Imprimir {cliente}</button>"
        html += "</div>"

    html += "<br><a href='/controle'>Voltar</a>"
    html += "<br><a href='/limpar_pedidos'><button class='btn limpar'>Limpar todos os pedidos</button></a>"
    html += "</body></html>"

    return html




@app.route("/pedido/<int:linha>/status/<novo_status>")
def atualizar_status(linha, novo_status):
    arquivo = "pedidos.xlsx"
    wb = load_workbook(arquivo)
    ws = wb["Pedidos"]
    ws.cell(row=linha, column=12, value=novo_status)  # coluna 12 = Status
    wb.save(arquivo)
    return redirect("/pedidos")


@app.route("/limpar_pedidos")
def limpar_pedidos():
    if "usuario" not in session:
        return redirect("/login")

    arquivo = "pedidos.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Pedidos"
    ws.append([
        "Data/Hora", "Nome", "Telefone", "Bairro", "Cidade", "Complemento",
        "Pagamento", "Observação", "Itens", "Adicionais", "Total", "Status"
    ])
    wb.save(arquivo)
    return redirect("/pedidos")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)