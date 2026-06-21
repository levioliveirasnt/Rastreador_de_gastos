import csv
import click
import os
from datetime import datetime
from rich.table import Table
from rich.console import Console

console = Console()
CATEGORIAS = {
    "1": "Alimentação",
    "2": "Transporte",
    "3": "Moradia",
    "4": "Saúde",
    "5": "Outros"
}

@click.group()
def cli():
    """Rastreador de Gastos"""
    pass

def validar_data(texto):
    if texto == '':
        return texto
    try:
        datetime.strptime(texto, "%d/%m/%Y")
        return texto 
    except ValueError:
        raise click.BadParameter("Formato inválido! Use estritamente o formato DD/MM/YYYY (ex: 20/06/2026).")

def validar_mes_ano(texto):
    if texto == 'all' or texto == '':
        return texto
    try:
        datetime.strptime(texto, "%m/%Y")
        return texto
    except ValueError:
        raise click.BadParameter("Formato inválido! Use estritamente o formato MM/YYYY (ex: 06/2026).")

@cli.command(help="Adicionar uma nova despesa.")
def add():
    data = click.prompt("Digite a data (DD/MM/YYYY)", value_proc=validar_data)
    description = click.prompt("Digite uma breve descrição")
    value = click.prompt("Digite um valor", type=float)

    menu_categorias = (
        "\nEscolha a categoria:\n"
        "1. Alimentação\n"
        "2. Transporte\n"
        "3. Moradia\n"
        "4. Saúde\n"
        "5. Outros\n\n"
        "Digite o número correspondente"
    )
    category = click.prompt(menu_categorias, type=click.IntRange(1, 5))
    proximo_id = 1

    if os.path.exists("expenses.csv"):
        with open("expenses.csv", "r", encoding="utf-8") as arquivo:
            linhas = list(csv.DictReader(arquivo))
            if linhas:
                proximo_id = int(linhas[-1]["ID"]) + 1

    arquivo_existe = os.path.exists("expenses.csv")
    with open("expenses.csv", 'a', encoding="utf-8", newline='') as arquivo:
        dados = csv.DictWriter(arquivo, fieldnames=["ID", "Data", "Descrição", "Valor", "Categoria"])
        if not arquivo_existe:
            dados.writeheader()
        dados.writerow({
            "ID": proximo_id,
            "Data": data,
            "Descrição": description,
            "Valor": value,
            "Categoria": str(category)
        })

    click.echo(f"Despesa na categoria {CATEGORIAS[str(category)]} adicionada com sucesso!")

@cli.command(help="Editar uma despesa existente.")
@click.argument('id_despesa', type=str)
def edit(id_despesa):
    if not os.path.exists("expenses.csv"):
        click.echo("Nenhum registro encontrado.")
        return
        
    todas_despesas = []
    despesa_alvo = None

    with open("expenses.csv", 'r', encoding="utf-8") as arquivo:
        dados = csv.DictReader(arquivo)
        for linha in dados:
            if linha['ID'] == id_despesa:
                despesa_alvo = linha
            todas_despesas.append(linha)

    if despesa_alvo is None:
        click.echo(f"Nenhuma despesa encontrada com esse ID!")
        return
    
    data = click.prompt(f"Data atual: {despesa_alvo['Data']}. Nova data (DD/MM/YYYY) ou Enter", default='', show_default=False, value_proc=validar_data)
    if data != '':
        despesa_alvo["Data"] = data
    
    description = click.prompt(f"Descrição atual: {despesa_alvo['Descrição']}. Nova descrição ou Enter", default='', show_default=False)
    if description != '':
        despesa_alvo["Descrição"] = description
    
    value = click.prompt(f"Valor atual: {despesa_alvo['Valor']}. Novo valor ou Enter", default='', show_default=False)
    if value != '':
        despesa_alvo["Valor"] = str(float(value))

    menu_categorias = f"\nCategoria atual: {CATEGORIAS[despesa_alvo['Categoria']]}. Escolha de 1 a 5 ou Enter"
    category = click.prompt(menu_categorias, default='', show_default=False)
    if category != '':
        despesa_alvo["Categoria"] = str(category)

    with open("expenses.csv", "w", encoding="utf-8", newline='') as arquivo:
        dados = csv.DictWriter(arquivo, fieldnames=["ID", "Data", "Descrição", "Valor", "Categoria"])
        dados.writeheader()
        dados.writerows(todas_despesas)

    click.echo(f"Despesa editada com sucesso!")

@cli.command(help="Deletar uma despesa existente.")
@click.argument('id_despesa', type=str)
def delete(id_despesa):
    if not os.path.exists("expenses.csv"):
        return
        
    todas_despesas = []
    found = False

    with open("expenses.csv", 'r', encoding="utf-8") as arquivo:
        dados = csv.DictReader(arquivo)
        for linha in dados:
            if linha['ID'] == id_despesa:
                found = True
                continue
            todas_despesas.append(linha)

    if not found:
        click.echo(f"Nenhuma despesa encontrada com esse ID!")
        return

    with open("expenses.csv", "w", encoding="utf-8", newline='') as arquivo:
        dados = csv.DictWriter(arquivo, fieldnames=["ID", "Data", "Descrição", "Valor", "Categoria"])
        dados.writeheader()
        dados.writerows(todas_despesas)
        
    click.echo(f"Despesa deletada com sucesso!")

@cli.command(name="list", help="Listar todas as despesas registradas.")
@click.option("--category", default='all', help="Filtra as despesas por categoria.")
@click.option("--month-year", default='all', help="Filtra por mês/ano (MM/YYYY).")
def list_expenses(category, month_year):
    if month_year != 'all':
        try:
            datetime.strptime(month_year, "%m/%Y")
        except ValueError:
            click.secho("Erro: Use o formato MM/YYYY (ex: 06/2026).", fg="red")
            return

    if not os.path.exists("expenses.csv"):
        click.echo("Nenhuma despesa registrada.")
        return

    table = Table(title="Lista de despesas", title_justify="left")
    table.add_column("ID", justify="left")
    table.add_column("Data", justify="right")
    table.add_column("Descrição", justify="left")
    table.add_column("Valor", justify="right")
    table.add_column("Categoria", justify="left")

    with open("expenses.csv", "r", encoding="utf-8") as arquivo:
        dados = csv.DictReader(arquivo)
        total = 0.0
        for linha in dados:
            linha_mes_ano = linha["Data"][3:] if len(linha["Data"]) >= 10 else ""

            match_categoria = (category == 'all' or linha["Categoria"] == category)
            match_data = (month_year == 'all' or linha_mes_ano == month_year)

            if match_categoria and match_data:
                valor_float = float(linha["Valor"])
                total += valor_float
                nome_categoria = CATEGORIAS.get(linha["Categoria"], linha["Categoria"])
                table.add_row(linha["ID"], linha["Data"], linha["Descrição"], f"R$ {valor_float:.2f}", nome_categoria)

    table.add_section()
    table.add_row("Total", "", "", f"R$ {total:.2f}", "")
    console.print(table)

@cli.command(help="Exibir o resumo financeiro mensal mapeado.")
@click.argument("month_year", type=str)
def resume(month_year):  
    try:
        datetime.strptime(month_year, "%m/%Y")
    except ValueError:
        click.secho("Erro: Use o formato MM/YYYY (ex: 06/2026).", fg="red")
        return

    if not os.path.exists("expenses.csv"):
        click.echo("Nenhum registro encontrado.")
        return

    # Mapeamento estático para traduzir o ID salvo na string amigável da categoria
    categorias_map = {
        "1": "Alimentação",
        "2": "Transporte",
        "3": "Moradia",
        "4": "Saúde",
        "5": "Outros"
    }

    # Inicializamos o dicionário acumulador com valor zero para cada chave cadastrada
    resumo_categorias = {cat: 0.0 for cat in categorias_map.values()}
    total_geral = 0.0

    with open("expenses.csv", "r", encoding="utf-8") as arquivo:
        dados = csv.DictReader(arquivo)
        for linha in dados:
            # Coleta o fragmento MM/YYYY da string de data DD/MM/YYYY
            linha_mes_ano = linha["Data"][3:] 
            
            if linha_mes_ano == month_year:
                valor = float(linha["Valor"])
                total_geral += valor
                
                # Traduz o código numérico salvando diretamente no acumulador nominal
                nome_categoria = categorias_map.get(linha["Categoria"], "Outros")
                resumo_categorias[nome_categoria] += valor

    if total_geral == 0.0:
        click.secho(f"Nenhum gasto registrado para o período {month_year}.", fg="yellow")
        return

    # Montagem da tabela analítica estruturada com Rich
    table = Table(title=f"Resumo de Gastos — Período: {month_year}")
    table.add_column("Categoria", justify="left", style="cyan")
    table.add_column("Valor Total", justify="right", style="green")
    table.add_column("Participação (%)", justify="right", style="magenta")

    for categoria, valor_parcial in resumo_categorias.items():
        if valor_parcial > 0:
            percentual = (valor_parcial / total_geral) * 100
            table.add_row(categoria, f"R$ {valor_parcial:.2f}", f"{percentual:.1f}%")

    table.add_section()
    table.add_row("Total Geral", f"R$ {total_geral:.2f}", "100.0%")
    console.print(table)

if __name__ == "__main__":
    cli()