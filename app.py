import os

import psycopg2


def conectar():
    # usa a biblioteca psycorpg2 para conectar com o banco de dados via docker
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "agrotrace"),
        user=os.getenv("DB_USER", "agro_user"),
        password=os.getenv("DB_PASSWORD", "agro_pass"),
    )


def cadastrar_propriedade():
    """
    Realiza o cadastro de uma nova propriedade rural na base de dados.

    A função solicita ao usuário os dados básicos da propriedade:
    nome, localização e área total. Antes de inserir no banco, realiza
    validações simples para evitar campos vazios e valores inválidos.

    A inserção é feita dentro de uma transação explícita com nível de
    isolamento READ COMMITTED. Caso a inserção seja bem-sucedida, a
    transação é confirmada com commit. Caso ocorra algum erro, a
    transação é desfeita com rollback.
    """

    print("\n=== Cadastro de Propriedade ===")

    # Entrada de dados do usuário.
    # O método strip() remove espaços em branco no início e no fim da string.
    nome = input("Nome da propriedade: ").strip()
    localizacao = input("Localização: ").strip()
    area_texto = input("Área total: ").strip()

    # Validação de campos obrigatórios.
    # Se algum campo estiver vazio, o cadastro é interrompido.
    if not nome or not localizacao or not area_texto:
        print("Erro: todos os campos são obrigatórios.")
        return

    # Conversão da área total para número decimal.
    # Caso o usuário digite algo que não seja número, o erro é tratado.
    try:
        area_total = float(area_texto)
    except ValueError:
        print("Erro: a área total deve ser um número.")
        return

    # Validação de regra de negócio:
    # a área total da propriedade deve ser maior que zero.
    if area_total <= 0:
        print("Erro: a área total deve ser maior que zero.")
        return

    # Inicialização das variáveis de conexão e cursor.
    # Elas começam como None para que possam ser verificadas no finally.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        # A função conectar() deve retornar uma conexão válida com o PostgreSQL.
        conexao = conectar()

        # Desativa o autocommit para permitir controle transacional manual.
        # Assim, a aplicação decide quando confirmar ou desfazer a transação.
        conexao.autocommit = False

        # Cria o cursor, que será usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Inicia explicitamente uma transação.
        cursor.execute("BEGIN;")

        # Define o nível de isolamento da transação.
        # READ COMMITTED garante que a transação leia apenas dados já confirmados.
        cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED;")

        # Executa a inserção usando parâmetros (%s).
        # Isso evita concatenação direta de strings no SQL e reduz risco de SQL Injection.
        cursor.execute(
            """
            INSERT INTO propriedade (nome, localizacao, area_total)
            VALUES (%s, %s, %s);
        """,
            (nome, localizacao, area_total),
        )

        # Confirma a transação caso todos os comandos tenham sido executados com sucesso.
        conexao.commit()
        print("Propriedade cadastrada com sucesso!")

    except Exception as erro:
        # Caso ocorra qualquer erro durante a transação,
        # desfaz todas as alterações realizadas desde o BEGIN.
        if conexao:
            conexao.rollback()

        print("Erro ao cadastrar propriedade. A transação foi desfeita.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def consultar_relatorio_propriedade():
    """
    Consulta um relatório detalhado de propriedades rurais cadastradas no AgroTrace.

    A função solicita ao usuário parte do nome de uma propriedade e usa essa entrada
    como parâmetro de busca na consulta SQL. A consulta retorna informações gerais da
    propriedade, quantidade de talhões, soma das áreas dos talhões, grãos plantados e
    insumos aplicados.

    A consulta é executada dentro de uma transação explícita com nível de isolamento
    REPEATABLE READ e modo READ ONLY, garantindo uma visão consistente dos dados
    durante a execução da consulta e impedindo alterações no banco nessa transação.

    A entrada do usuário é usada de forma parametrizada no cursor.execute(),
    evitando concatenação direta de strings no SQL e reduzindo risco de SQL Injection.
    """

    print("\n=== Relatório detalhado da propriedade ===")

    termo = input(
        "Digite parte do nome da propriedade ou pressione Enter para listar todas: "
    ).strip()

    if not termo:
        parametro = "%"
    else:
        parametro = f"%{termo}%"

    # Inicialização das variáveis de conexão e cursor.
    # Elas começam como None para permitir fechamento seguro no bloco finally.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        # A função conectar() deve retornar uma conexão válida com o PostgreSQL.
        conexao = conectar()

        # Desativa o autocommit para que a aplicação controle explicitamente
        # o início, confirmação ou reversão da transação.
        conexao.autocommit = False

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Inicia explicitamente uma transação.
        cursor.execute("BEGIN;")

        # Define o nível de isolamento da transação.
        # REPEATABLE READ garante que todas as leituras dentro da transação
        # enxerguem uma visão consistente dos dados.
        #
        # READ ONLY indica que a transação é apenas de consulta e não fará alterações.
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;")

        # Executa a consulta parametrizada.
        # O parâmetro %s é substituído de forma segura pelo valor de "parametro".
        # Isso evita SQL Injection, pois o valor digitado pelo usuário é tratado
        # como dado, e não como parte do comando SQL.
        cursor.execute(
            """
            WITH area_talhoes AS (
                SELECT
                    t.propriedade_nome,
                    t.propriedade_localizacao,
                    COUNT(*) AS qtd_talhoes,
                    SUM(t.area) AS area_total_talhoes
                FROM talhao t
                GROUP BY
                    t.propriedade_nome,
                    t.propriedade_localizacao
            ),

            graos_plantados AS (
                SELECT
                    o.propriedade_nome,
                    o.propriedade_localizacao,
                    STRING_AGG(DISTINCT lg.nome_grao, ', ') AS graos_plantados
                FROM operacao o
                JOIN utiliza_graos ug
                    ON ug.id_operacao_plantio = o.id_operacao
                JOIN lote_graos lg
                    ON lg.id_lote_grao = ug.id_lote_grao
                GROUP BY
                    o.propriedade_nome,
                    o.propriedade_localizacao
            ),

            insumos_aplicados AS (
                SELECT
                    o.propriedade_nome,
                    o.propriedade_localizacao,
                    STRING_AGG(DISTINCT li.nome_insumo, ', ') AS insumos_aplicados
                FROM operacao o
                JOIN aplica_insumo ai
                    ON ai.id_operacao = o.id_operacao
                JOIN lote_insumo li
                    ON li.id_lote_insumo = ai.id_lote_insumo
                GROUP BY
                    o.propriedade_nome,
                    o.propriedade_localizacao
            )

            SELECT
                p.nome,
                p.localizacao,
                p.area_total,
                COALESCE(a.qtd_talhoes, 0) AS qtd_talhoes,
                COALESCE(a.area_total_talhoes, 0) AS area_total_talhoes,
                COALESCE(g.graos_plantados, 'Nenhum') AS graos_plantados,
                COALESCE(i.insumos_aplicados, 'Nenhum') AS insumos_aplicados
            FROM propriedade p

            LEFT JOIN area_talhoes a
                ON a.propriedade_nome = p.nome
               AND a.propriedade_localizacao = p.localizacao

            LEFT JOIN graos_plantados g
                ON g.propriedade_nome = p.nome
               AND g.propriedade_localizacao = p.localizacao

            LEFT JOIN insumos_aplicados i
                ON i.propriedade_nome = p.nome
               AND i.propriedade_localizacao = p.localizacao

            WHERE p.nome ILIKE %s

            ORDER BY p.nome;
        """,
            (parametro,),
        )

        # Recupera todos os resultados retornados pela consulta.
        resultados = cursor.fetchall()

        # Confirma a transação de leitura.
        # Mesmo sendo uma consulta READ ONLY, o commit encerra corretamente a transação.
        conexao.commit()

        # Caso nenhuma propriedade seja encontrada, informa o usuário.
        if not resultados:
            print("Nenhuma propriedade encontrada.")
            return

        # Percorre os resultados e exibe o relatório no terminal.
        for linha in resultados:
            (
                nome,
                localizacao,
                area_total,
                qtd_talhoes,
                area_total_talhoes,
                graos,
                insumos,
            ) = linha

            print("\n----------------------------------------")
            print(f"Propriedade: {nome}")
            print(f"Localização: {localizacao}")
            print(f"Área total da propriedade: {area_total} ha")
            print(f"Quantidade de talhões: {qtd_talhoes}")
            print(f"Área mapeada em talhões: {area_total_talhoes} ha")
            print(f"Grãos plantados: {graos}")
            print(f"Insumos aplicados: {insumos}")
            print("----------------------------------------")

    except Exception as erro:
        # Em caso de erro, desfaz a transação.
        # Isso mantém o padrão transacional da aplicação, mesmo para consultas.
        if conexao:
            conexao.rollback()

        print("Erro ao realizar consulta. A transação foi desfeita.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def menu():
    while True:
        # menu simples
        print("\n=== AgroTrace ===")
        print("1 - Cadastrar propriedade")
        print("2 - Consultar relatório detalhado")
        print("3 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_propriedade()
        elif opcao == "2":
            consultar_relatorio_propriedade()
        elif opcao == "3":
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
