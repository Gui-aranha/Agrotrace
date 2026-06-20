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


def relatorio_detalhado_propriedades():
    """
    Consulta 1 no consultas.sql
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
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
            ORDER BY p.nome;
            """
        )

        resultados = cursor.fetchall()

        print("\n" + "="*80)
        print(" "*22 + "RELATÓRIO DETALHADO DAS PROPRIEDADES")
        print("="*80)

        if not resultados:
            print("Nenhuma propriedade cadastrada no sistema.")
        else:
            for registro in resultados:
                (nome, localizacao, area_total, qtd_talhoes, 
                 area_talhoes, graos, insumos) = registro
                
                print(f"PROPRIEDADE: {nome} ({localizacao})")
                print(f"  Área Total: {area_total} ha | Qtd Talhões: {qtd_talhoes} | Área dos Talhões: {area_talhoes} ha")
                print(f"  Grãos já plantados: {graos}")
                print(f"  Insumos aplicados : {insumos}")
                print("-" * 80)
                
        print("="*80)

    except Exception as e:
        print(f"Erro ao gerar o relatório: {e}")
    finally:
        cursor.close()
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
         # ao não usar f-strings já se protege de SQL injection
        cursor.execute( 
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
        print("1 - Cadastrar propriedade")
        print("2 - Consultar por área mínima")
        print("3 - Listar propriedades")
        print("4 - Gerar relatório detalhado das propriedades")
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
            relatorio_detalhado_propriedades()
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
