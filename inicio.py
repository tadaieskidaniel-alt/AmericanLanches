
from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

loja_coords = (-28.511882260275637, -49.367838494165454)

senha = "1234"

@app.route("/validar_senha", methods=["POST"])
def validar_senha():
    data = request.get_json()
    if data.get("senha") == senha:
        return jsonify({"autorizado": True})
    return jsonify({"autorizado": False})

@app.route("/alterar_status/<novo_status>")
def alterar_status(novo_status):
    global status_manual
    if novo_status in ["Aberto", "Fechado"]:
        status_manual = novo_status
    return redirect("/")


@app.route("/")
def index():
    if not os.path.exists("static/cardapio.xlsx"):
        return "Arquivo Cardapio.xlsx não encontrado", 500
    df = pd.read_excel("static/cardapio.xlsx")
    precos = dict(zip(df["item"], df["preco"]))
    ingredientes = dict(zip(df["item"], df["ingredientes"]))
    return render_template("inicio.html", precos=precos, ingredientes=ingredientes, )
    status = status_loja()
    return render_template("inicio.html", status=status_loja())


taxas_entrega = {
    "Rio América": 2.00,
    "Centro": 7.00,
    "Belvedere": 8.00,
    "São Donato": 12.00,
    "Coxia Rica": 12.00,
    "Santana": 10.00,
    "Rio Salto": 5.00,
    "Pirago": 6.00,
    "Rio Caeté": 7.00,
    "Rio Deserto": 8.00,
    "Estação": 8.00,
    "De Vila": 10.00,
    "São Pedro": 12.00,
    "Nova Itália": 8.00,
    "Rio Carvão": 8.00,
    "Rio Carvão Baixo": 10.00
}

def calcular_taxa(bairro, total):
    taxa_entrega = taxas_entrega.get(bairro, 0)
    total_final = total + taxa_entrega
    return taxa_entrega, total_final

@app.route("/finalizar", methods=["POST"])
def finalizar():
    complemento = request.form.get("complemento")
    bairro = request.form.get("bairro")
    total_str = request.form.get("total_input", "0.00")


    nome = request.form.get("nome")
    telefone = request.form.get("telefone")
    cidade = request.form.get("cidade")
    observacão = request.form.get("observação")
    pagamento = request.form.get("pagamento")
    adicionais= request.form.getlist("adicionais")

    

    try:
        total = float(total_str)
    except ValueError:
        total = 0.0

    taxa_entrega, total_final = calcular_taxa(bairro, total)
    
    mensagem = f"Pedido finalizado!\n\n"
    mensagem += f"Nome: {nome}\n"
    mensagem += f"Telefone: {telefone}\n"
    mensagem += f"Bairro: {bairro}, Urussanga, SC\n"
    mensagem += f"Complemento: {complemento}\n"
    mensagem += f"----------------------------\n"

    adicionais = [
        "quantidade_Calabresa", "quantidade_Bacon", "quantidade_Hambúrguer Extra",
        "quantidade_Frango", "quantidade_Anel de Cebola", "quantidade_Picles",
        "quantidade_Batata Frita Extra", "quantidade_Ovinho Conserva",
        "quantidade_Acebolado", "quantidade_Cheddar", "quantidade_Coração",
        "quantidade_Maionese caseira"
    ]
    mensagem += "Itens do pedido:\n"
    for campo, valor in request.form.items():
     if campo.startswith("quantidade_") and campo not in adicionais:
        qtd = int(valor)
        if qtd > 0:
            nome_item = campo.replace("quantidade_", "")
            mensagem += f"- {nome_item} x{qtd}\n"

    mensagem += "\nAdicionais:\n"
    for campo in adicionais:
        qtd = int(request.form.get(campo, 0))
        if qtd > 0:
         nome_item = campo.replace("quantidade_", "")
         mensagem += f"- {nome_item} x{qtd}\n"

    mensagem += f"Total produtos: R${total:.2f}\n"
    mensagem += f"Taxa de entrega: R${taxa_entrega:.2f}\n"
    mensagem += f"Total final: R${total_final:.2f}\n"
    mensagem += f"Pagamento: {pagamento}\n"
    mensagem += f'observações: {observacão}\n'
    mensagem += "\nObrigado pela compra!"

    # Converter quebras de linha para %0A
    mensagem_link = mensagem.replace("\n", "%0A")

    # Número do WhatsApp (formato internacional)
    numero_whats = "48996598873"

    # Montar link
    link = f"https://wa.me/{numero_whats}?text={mensagem_link}"

    # Redirecionar para WhatsApp
    return redirect(link)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

