import os

import psycopg2


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "agrotrace"),
        user=os.getenv("DB_USER", "agro_user"),
        password=os.getenv("DB_PASSWORD", "agro_pass"),
    )


def listar_propriedades():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute( # ao não usar f-strings já se protege de SQL injection
        """
        SELECT id_propriedade, nome, localizacao, area_total
        FROM propriedade
        ORDER BY id_propriedade;
    """)

    propriedades = cursor.fetchall()

    print("\n=== Propriedades cadastradas ===")

    if not propriedades:
        print("Nenhuma propriedade encontrada.")
    else:
        for id_propriedade, nome, localizacao, area_total in propriedades:
            print(f"{id_propriedade} - {nome} | {localizacao} | {area_total} ha")

    cursor.close()
    conexao.close()


def cadastrar_propriedade():
    nome = input("Nome da propriedade: ")
    localizacao = input("Localização: ")

    try:
        area_total = float(input("Área total: "))
    except ValueError: # caso não passe no check e cause um erro
        print("Área inválida. Digite um número.")
        return

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute( # ao não usar f-strings já se protege de SQL injection
            """
            INSERT INTO propriedade (nome, localizacao, area_total)
            VALUES (%s, %s, %s);
        """,
            (nome, localizacao, area_total),
        )

        conexao.commit() 
        print("Propriedade cadastrada com sucesso!")

    except Exception as erro:
        conexao.rollback() # transação é desfeita se interrompida no meio
        print("Erro ao cadastrar propriedade:")
        print(erro)

    cursor.close()
    conexao.close()


def consultar_por_area():
    try:
        area_minima = float(input("Área mínima: "))
    except ValueError:
        print("Área inválida. Digite um número.")
        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT nome, localizacao, area_total
        FROM propriedade
        WHERE area_total >= %s
        ORDER BY area_total DESC;
    """,
        (area_minima,),
    )

    resultados = cursor.fetchall()

    print(f"\n=== Propriedades com área >= {area_minima} ===")

    if not resultados:
        print("Nenhuma propriedade encontrada.")
    else:
        for nome, localizacao, area_total in resultados:
            print(f"{nome} | {localizacao} | {area_total} ha")

    cursor.close()
    conexao.close()


def menu():
    while True:
        print("\n=== AgroTrace Mini ===")
        print("1 - Listar propriedades")
        print("2 - Cadastrar propriedade")
        print("3 - Consultar por área mínima")
        print("4 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            listar_propriedades()
        elif opcao == "2":
            cadastrar_propriedade()
        elif opcao == "3":
            consultar_por_area()
        elif opcao == "4":
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
