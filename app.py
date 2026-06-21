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



def listar_propriedades():
    """
    Consulta 0 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    # ao não usar f-strings já se protege de SQL injection
    cursor.execute(
        """
        SELECT nome, localizacao
        FROM propriedade
        ORDER BY nome;
    """)

    propriedades = cursor.fetchall()

    print("\n=== Propriedades cadastradas ===")

    if not propriedades:
        print("Nenhuma propriedade encontrada.")
    else:
        for nome, localizacao in propriedades:
            print(f"{nome} | {localizacao}")

    cursor.close()
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


def consultar_ultima_medicao_sensores():
    """
    Consulta 2 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                s.nro_serie,
                s.nome,
                s.tipo_medicao,
                TO_CHAR(lm.data_hora, 'DD/MM/YYYY HH24:MI:SS') AS data_hora_formatada,
                lm.valor
            FROM sensor s
            LEFT JOIN (
                SELECT m1.nro_serie, m1.data_hora, m1.valor
                FROM medicao m1
                JOIN (
                    SELECT nro_serie, MAX(data_hora) AS max_data
                    FROM medicao
                    GROUP BY nro_serie
                ) ult
                  ON ult.nro_serie = m1.nro_serie
                 AND ult.max_data = m1.data_hora
            ) lm
              ON lm.nro_serie = s.nro_serie
            ORDER BY s.nro_serie;
            """
        )

        resultados = cursor.fetchall()

        print("\n" + "="*80)
        print(" "*19 + "PAINEL DE TELEMETRIA: ÚLTIMA MEDIÇÃO POR SENSOR")
        print("="*80)

        if not resultados:
            print("Nenhum sensor cadastrado no sistema.")
        else:
            for registro in resultados:
                nro_serie, nome, tipo_medicao, data_hora, valor = registro
                
                print(f"SENSOR: {nome} | Nº Série: {nro_serie}")
                print(f"  Tipo de Medição: {tipo_medicao}")
                
                if data_hora:
                    print(f"  Última Leitura : {valor} | Coletado em: {data_hora}")
                else:
                    print(f"  Última Leitura : [SEM HISTÓRICO] Nenhuma medição registrada para este sensor.")
                print("-" * 80)
                
        print("="*80)

    except Exception as e:
        print(f"Erro ao consultar a telemetria dos sensores: {e}")
    finally:
        cursor.close()
        conexao.close()


def nota_fiscal():
    """
    Consulta 3 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
        SELECT
            tr.id_operacao                           AS id_nota,
            TO_CHAR(tr.data_compra, 'DD/MM/YYYY HH24:MI') AS data_compra,
            c.cnpj                                   AS cnpj_consumidor,
            c.nome                                   AS nome_consumidor,
            c.email1                                 AS email_consumidor,
            c.telefone1                              AS telefone_consumidor,
            p.lote_produto,
            p.preco                                  AS preco_unitario,
            tr.quantidade_comprada,
            tr.valor_compra                          AS valor_total,
            o.propriedade_nome,
            o.propriedade_localizacao,
            o.nro_talhao
        FROM transacao tr
        JOIN consumidor c
        ON c.cnpj = tr.cnpj_consumidor
        JOIN produto p
        ON p.id_operacao = tr.id_operacao
        AND p.lote_produto = tr.lote_produto
        JOIN colheita co
        ON co.id_operacao = p.id_operacao
        JOIN operacao o
        ON o.id_operacao = co.id_operacao
        ORDER BY tr.data_compra DESC, c.nome;
        """)

        notas_fiscais = cursor.fetchall()

        if not notas_fiscais:
            print("Nenhuma transação encontrada para gerar notas fiscais.")
            return

        print("\n" + "="*50)
        print(" "*13 + "EMISSÃO DE NOTAS FISCAIS")
        print("="*50)

        for nota in notas_fiscais:
            (id_nota, data_compra, cnpj, nome, email, telefone, 
            lote, preco, qtd, valor_total, prop_nome, prop_loc, nro_talhao) = nota
                
            # Imprime a nota fiscal
            print(f"NOTA FISCAL Nº: {id_nota} | Emissão: {data_compra}")
            print(f"CONSUMIDOR: {nome}")
            print(f"CNPJ: {cnpj} | Contato: {email} / {telefone}")
            print(f"--------------------------------------------------")
            print(f"PRODUTO (Lote): {lote}")
            print(f"ORIGEM RASTREADA: {prop_nome} - {prop_loc} (Talhão {nro_talhao})")
            print(f"QUANTIDADE: {qtd} kg  x  PREÇO UNIT: R$ {preco}")
            print(f"VALOR TOTAL DA NOTA: R$ {valor_total}")
            print("="*50)

    except Exception as e:
        print(f"Erro ao emitir as notas fiscais: {e}")
    finally:
        cursor.close()
        conexao.close()


def operacoes_acima_da_media():
    """
    Consulta 4 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                o.id_operacao,
                TO_CHAR(o.data_hora_inicio, 'DD/MM/YYYY HH24:MI') AS inicio,
                TO_CHAR(o.data_hora_fim, 'DD/MM/YYYY HH24:MI') AS fim,
                op.nome AS operador,
                m.nome AS maquina,
                p.nome AS propriedade,
                p.localizacao,
                t.nro_talhao,
                ROUND(EXTRACT(EPOCH FROM (o.data_hora_fim - o.data_hora_inicio)) / 3600.0, 2) AS duracao_horas
            FROM operacao o
            JOIN operador op
              ON op.cpf = o.cpf_operador
            JOIN maquina m
              ON m.nro_serie = o.nro_serie_maquina
            JOIN talhao t
              ON t.propriedade_nome = o.propriedade_nome
             AND t.propriedade_localizacao = o.propriedade_localizacao
             AND t.nro_talhao = o.nro_talhao
            JOIN propriedade p
              ON p.nome = t.propriedade_nome
             AND p.localizacao = t.propriedade_localizacao
            WHERE o.data_hora_fim IS NOT NULL
              AND EXTRACT(EPOCH FROM (o.data_hora_fim - o.data_hora_inicio)) > (
                  SELECT AVG(EXTRACT(EPOCH FROM (o2.data_hora_fim - o2.data_hora_inicio)))
                  FROM operacao o2
                  WHERE o2.data_hora_fim IS NOT NULL
              )
            ORDER BY duracao_horas DESC;
            """
        )

        resultados = cursor.fetchall()

        print("\n" + "="*85)
        print(" "*18 + "RELATÓRIO DE EFICIÊNCIA: OPERAÇÕES ACIMA DA MÉDIA GLOBAL")
        print("="*85)

        if not resultados:
            print("Nenhuma operação concluída ficou acima da média")
        else:
            for registro in resultados:
                (id_op, inicio, fim, operador, maquina, 
                 propriedade, localizacao, talhao, duracao) = registro
                
                print(f"OPERAÇÃO Nº: {id_op} | DURAÇÃO: {duracao} horas")
                print(f"  Período : De {inicio} até {fim}")
                print(f"  Local   : {propriedade} ({localizacao}) - Talhão {talhao}")
                print(f"  Recursos: Operador: {operador} | Equipamento: {maquina}")
                print("-" * 85)
                
        print("="*85)

    except Exception as e:
        print(f"Erro ao analisar as operações: {e}")
    finally:
        cursor.close()
        conexao.close()


def todos_graos():
    """
    Consulta 5 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT f.cnpj, f.nome
            FROM fornecedor f
            WHERE NOT EXISTS (
                SELECT 1
                FROM grao g
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM lote_graos lg
                    WHERE lg.cnpj_fornecedor = f.cnpj
                      AND lg.nome_grao = g.nome
                )
            )
            ORDER BY f.nome;
            """
        )

        resultados = cursor.fetchall()

        print("\n" + "="*60)
        print(" FORNECEDORES QUE VENDEM TODOS OS GRÃOS DO SISTEMA")
        print("="*60)

        if not resultados:
            print("Nenhum fornecedor vende todos os tipos de grãos atualmente.")
        else:
            for cnpj, nome in resultados:               
                print(f"Fornecedor: {nome} | CNPJ: {cnpj}")
        
        print("="*60)

    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
    finally:
        cursor.close()
        conexao.close()


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


def consultar_por_area():
    # usa try/except para tratar erros e não deixar SQLinjection
    try:
        area_minima = float(input("Área mínima: "))
    except ValueError:
        print("Área inválida. Digite um número.")
        return

    # conecta ao banco
    conexao = conectar()
    cursor = conexao.cursor()

    # ao não usar f-strings já se protege de SQL injection
    # seleciona nome, localização e área total com um WHERE restrição
    cursor.execute(
        """
        SELECT nome, localizacao, area_total
        FROM propriedade
        WHERE area_total >= %s
        ORDER BY area_total DESC;
    """,
        (area_minima,),
    )

    # transforma em uma lista para conseguirmos mostrar
    resultados = cursor.fetchall()

    print(f"\n=== Propriedades com área >= {area_minima} ===")

    if not resultados:
        print("Nenhuma propriedade encontrada.")
    else:
        for nome, localizacao, area_total in resultados:
            print(f"{nome} | {localizacao} | {area_total} ha")

    # fecha o banco de dados
    cursor.close()
    conexao.close()


def menu():
    while True:
        # menu simples
        print("\n=== AgroTrace Mini ===")
        print("1 - Cadastrar propriedade")
        print("2 - Consultar por área mínima")
        print("3 - Listar propriedades")
        print("4 - Gerar relatório detalhado de uma ou todas propriedades")
        print("5 - Listar notas fiscais")
        print("6 - Listar fornecedores que vendem todos os grãos")
        print("7 - Listar operações com durações acima da média")
        print("8 - Listar última medição de cada sensor")
        print("9 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_propriedade()
        elif opcao == "2":
            consultar_por_area()
        elif opcao == "3":
            listar_propriedades()
        elif opcao == "4":
            consultar_relatorio_propriedade()
        elif opcao == "5":
            nota_fiscal()
        elif opcao == "6":
            todos_graos()
        elif opcao == "7":
            operacoes_acima_da_media()
        elif opcao == "8":
            consultar_ultima_medicao_sensores()
        elif opcao == "9":
            print("Encerrando...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()