
from flask import Flask, render_template, request, redirect, url_for, session
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from openpyxl import load_workbook





app = Flask(__name__) 

loja_coords = (-28.511882260275637, -49.367838494165454)

import pandas as pd
 





df = pd.read_excel("cardapio.xlsx") 


precos = dict(zip(df["item"], df["preco"]))



from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route("/")
def index():
    df = pd.read_excel("Cardapio.csv")  # ou read_csv
    precos = dict(zip(df["item"], df["preco"]))
    return render_template("inicio.html", precos=precos)


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
    taxa_entrega = taxas_entrega.get(bairro, 0)  # pega taxa fixa ou 0 se não existir
    total_final = total + taxa_entrega
    return taxa_entrega, total_final



@app.route("/finalizar", methods=["POST"])
def finalizar():
    complemento = request.form.get("complemento")
    bairro = request.form.get("bairro")
    total_str = request.form.get("total", "0")
    nome = request.form.get("nome")
    telefone = request.form.get("telefone")
    cidade = request.form.get("cidade")
    pagamento = request.form.get("pagamento")

    try:
        total = float(total_str)
    except ValueError:
        total = 0.0

    taxa_entrega, total_final = calcular_taxa(bairro, total)

    

    mensagem = f"Pedido finalizado!\n\n"
    mensagem += f"Nome: {nome}\n"
    mensagem += f"Telefone: {telefone}\n"
    mensagem += f"Bairro: {bairro}, Urussanga, SC\n"
    mensagem += f"\ncomplemento:{complemento}\n"
    mensagem += f"----------------------------\n"
    mensagem += f"Total produtos: R${total:.2f}\n"
    mensagem += f"Taxa de entrega: R${taxa_entrega:.2f}\n"
    mensagem += f"Total final: R${total_final:.2f}\n"
    mensagem += f"Pagamento: {pagamento}\n"
    mensagem += "\nObrigado pela compra!"

    numero = "48996598873"
    link_whatsapp = f"https://wa.me/{numero}?text={mensagem.replace(' ', '%20').replace('\n', '%0A')}"
    return redirect(link_whatsapp)

if __name__ == "__main__":
    app.run(debug=True)



