import os

import psycopg2


def conectar():
    """
    Cria e retorna uma conexão com o banco de dados PostgreSQL do AgroTrace.

    Os parâmetros de conexão são lidos a partir de variáveis de ambiente,
    permitindo que a aplicação funcione tanto dentro dos contêineres Docker
    quanto em execuções locais. Caso alguma variável não esteja definida,
    são usados valores padrão compatíveis com o ambiente do projeto.
    """

    # Usa a biblioteca psycopg2 para conectar a aplicação Python ao PostgreSQL.
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "agrotrace"),
        user=os.getenv("DB_USER", "agro_user"),
        password=os.getenv("DB_PASSWORD", "agro_pass"),
    )


def listar_propriedades():
    """
    Lista todas as propriedades rurais cadastradas na base de dados.

    A função executa uma consulta simples sobre a tabela propriedade,
    retornando o nome e a localização de cada propriedade cadastrada.
    Como não há entrada do usuário nessa consulta, não há parâmetros externos
    a serem tratados no comando SQL.

    Essa funcionalidade serve como uma consulta auxiliar para que o usuário
    visualize rapidamente quais propriedades existem no sistema.
    """

    # Inicialização das variáveis de conexão e cursor.
    # Elas começam como None para permitir fechamento seguro no bloco finally.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa uma consulta simples, sem entrada externa do usuário.
        cursor.execute(
            """
            SELECT nome, localizacao
            FROM propriedade
            ORDER BY nome;
        """
        )

        # Recupera todos os resultados retornados pela consulta.
        propriedades = cursor.fetchall()

        print("\n=== Propriedades cadastradas ===")

        # Caso nenhuma propriedade seja encontrada, informa o usuário.
        if not propriedades:
            print("Nenhuma propriedade encontrada.")
        else:
            # Exibe as propriedades cadastradas em formato resumido.
            for nome, localizacao in propriedades:
                print(f"{nome} | {localizacao}")

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao listar propriedades.")
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


def consultar_ultima_medicao_sensores():
    """
    Consulta a última medição registrada para cada sensor cadastrado no sistema.

    A função executa a Consulta 2 do arquivo consultas.sql. O objetivo é apresentar
    um painel de telemetria com todos os sensores cadastrados, mostrando a medição
    mais recente de cada um quando ela existir.

    A consulta utiliza uma subconsulta agregada para encontrar a maior data/hora de
    medição de cada sensor. Em seguida, usa LEFT JOIN para manter sensores sem
    histórico de medições no resultado, identificando-os como sensores sem leitura.
    """

    # Inicialização das variáveis de conexão e cursor.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa a consulta da última medição de cada sensor.
        # A subconsulta "ult" encontra a data/hora mais recente por sensor.
        # O LEFT JOIN garante que sensores sem medições também sejam exibidos.
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

        # Recupera todos os resultados retornados pela consulta.
        resultados = cursor.fetchall()

        print("\n" + "=" * 80)
        print(" " * 19 + "PAINEL DE TELEMETRIA: ÚLTIMA MEDIÇÃO POR SENSOR")
        print("=" * 80)

        # Caso não existam sensores cadastrados, informa o usuário.
        if not resultados:
            print("Nenhum sensor cadastrado no sistema.")
        else:
            # Exibe cada sensor junto com sua última leitura, quando existir.
            for registro in resultados:
                nro_serie, nome, tipo_medicao, data_hora, valor = registro

                print(f"SENSOR: {nome} | Nº Série: {nro_serie}")
                print(f"  Tipo de Medição: {tipo_medicao}")

                if data_hora:
                    print(f"  Última Leitura : {valor} | Coletado em: {data_hora}")
                else:
                    print(
                        "  Última Leitura : [SEM HISTÓRICO] "
                        "Nenhuma medição registrada para este sensor."
                    )
                print("-" * 80)

        print("=" * 80)

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao consultar a telemetria dos sensores.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def nota_fiscal():
    """
    Gera um relatório de notas fiscais a partir das transações registradas.

    A função executa a Consulta 3 do arquivo consultas.sql. O objetivo é reunir,
    em uma única visualização, dados do consumidor, da transação, do produto comprado
    e da origem produtiva associada à colheita que gerou o produto.

    A consulta realiza junções entre transação, consumidor, produto, colheita e
    operação. Dessa forma, permite exibir informações comerciais e dados de
    rastreabilidade, como propriedade, localização e talhão de origem.
    """

    # Inicialização das variáveis de conexão e cursor.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa a consulta de emissão de notas fiscais.
        # Os JOINs conectam a compra ao consumidor, ao produto e à operação de origem.
        cursor.execute(
            """
            SELECT
                tr.id_operacao AS id_nota,
                TO_CHAR(tr.data_compra, 'DD/MM/YYYY HH24:MI') AS data_compra,
                c.cnpj AS cnpj_consumidor,
                c.nome AS nome_consumidor,
                c.email1 AS email_consumidor,
                c.telefone1 AS telefone_consumidor,
                p.lote_produto,
                p.preco AS preco_unitario,
                tr.quantidade_comprada,
                tr.valor_compra AS valor_total,
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
            """
        )

        # Recupera todos os resultados retornados pela consulta.
        notas_fiscais = cursor.fetchall()

        # Caso não existam transações, informa o usuário.
        if not notas_fiscais:
            print("Nenhuma transação encontrada para gerar notas fiscais.")
            return

        print("\n" + "=" * 50)
        print(" " * 13 + "EMISSÃO DE NOTAS FISCAIS")
        print("=" * 50)

        # Exibe cada transação em formato semelhante a uma nota fiscal.
        for nota in notas_fiscais:
            (
                id_nota,
                data_compra,
                cnpj,
                nome,
                email,
                telefone,
                lote,
                preco,
                qtd,
                valor_total,
                prop_nome,
                prop_loc,
                nro_talhao,
            ) = nota

            print(f"NOTA FISCAL Nº: {id_nota} | Emissão: {data_compra}")
            print(f"CONSUMIDOR: {nome}")
            print(f"CNPJ: {cnpj} | Contato: {email} / {telefone}")
            print("--------------------------------------------------")
            print(f"PRODUTO (Lote): {lote}")
            print(f"ORIGEM RASTREADA: {prop_nome} - {prop_loc} (Talhão {nro_talhao})")
            print(f"QUANTIDADE: {qtd} kg  x  PREÇO UNIT: R$ {preco}")
            print(f"VALOR TOTAL DA NOTA: R$ {valor_total}")
            print("=" * 50)

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao emitir as notas fiscais.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def operacoes_acima_da_media():
    """
    Lista operações concluídas cuja duração ficou acima da média global.

    A função executa a Consulta 4 do arquivo consultas.sql. O objetivo é auxiliar
    a análise de eficiência operacional, identificando operações agrícolas que levaram
    mais tempo do que a duração média das operações concluídas no sistema.

    A consulta calcula a duração de cada operação em horas e usa uma subconsulta
    não correlacionada para obter a média global de duração. Em seguida, retorna
    apenas as operações com duração superior a essa média.
    """

    # Inicialização das variáveis de conexão e cursor.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa a consulta de operações acima da média.
        # A subconsulta calcula a duração média das operações concluídas.
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

        # Recupera todos os resultados retornados pela consulta.
        resultados = cursor.fetchall()

        print("\n" + "=" * 85)
        print(" " * 18 + "RELATÓRIO DE EFICIÊNCIA: OPERAÇÕES ACIMA DA MÉDIA GLOBAL")
        print("=" * 85)

        # Caso nenhuma operação satisfaça o critério, informa o usuário.
        if not resultados:
            print("Nenhuma operação concluída ficou acima da média.")
        else:
            # Exibe as operações ordenadas pela duração, da maior para a menor.
            for registro in resultados:
                (
                    id_op,
                    inicio,
                    fim,
                    operador,
                    maquina,
                    propriedade,
                    localizacao,
                    talhao,
                    duracao,
                ) = registro

                print(f"OPERAÇÃO Nº: {id_op} | DURAÇÃO: {duracao} horas")
                print(f"  Período : De {inicio} até {fim}")
                print(f"  Local   : {propriedade} ({localizacao}) - Talhão {talhao}")
                print(f"  Recursos: Operador: {operador} | Equipamento: {maquina}")
                print("-" * 85)

        print("=" * 85)

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao analisar as operações.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def todos_graos():
    """
    Lista fornecedores que vendem todos os tipos de grãos cadastrados no sistema.

    A função executa a Consulta 5 do arquivo consultas.sql, que implementa uma
    divisão relacional por meio de duas subconsultas NOT EXISTS encadeadas.

    A lógica da consulta é: retornar fornecedores para os quais não existe nenhum
    grão cadastrado que não esteja presente em algum lote vendido por esse fornecedor.
    Em outras palavras, o fornecedor é listado apenas se vender todos os grãos do
    catálogo do sistema.
    """

    # Inicialização das variáveis de conexão e cursor.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa a consulta de divisão relacional.
        # O primeiro NOT EXISTS garante que não exista grão sem lote correspondente
        # vendido pelo fornecedor avaliado.
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

        # Recupera todos os resultados retornados pela consulta.
        resultados = cursor.fetchall()

        print("\n" + "=" * 60)
        print(" FORNECEDORES QUE VENDEM TODOS OS GRÃOS DO SISTEMA")
        print("=" * 60)

        # Caso nenhum fornecedor satisfaça a divisão relacional, informa o usuário.
        if not resultados:
            print("Nenhum fornecedor vende todos os tipos de grãos atualmente.")
        else:
            # Exibe os fornecedores encontrados.
            for cnpj, nome in resultados:
                print(f"Fornecedor: {nome} | CNPJ: {cnpj}")

        print("=" * 60)

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao executar a consulta de fornecedores.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
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
    """
    Consulta propriedades rurais com área total maior ou igual a um valor informado.

    A função solicita ao usuário uma área mínima e valida se o valor digitado pode
    ser convertido para número. Em seguida, executa uma consulta parametrizada sobre
    a tabela propriedade, retornando nome, localização e área total das propriedades
    que atendem ao critério informado.

    O uso de parâmetros no cursor.execute() evita a concatenação direta da entrada
    do usuário no comando SQL, reduzindo o risco de SQL Injection.
    """

    print("\n=== Consulta de propriedades por área mínima ===")

    # Entrada de dados do usuário.
    area_texto = input("Área mínima: ").strip()

    # Conversão da área mínima para número decimal.
    # O try/except trata entradas inválidas, como texto no lugar de número.
    try:
        area_minima = float(area_texto)
    except ValueError:
        print("Área inválida. Digite um número.")
        return

    # Validação simples para evitar consultas com área negativa.
    if area_minima < 0:
        print("Área inválida. Digite um valor maior ou igual a zero.")
        return

    # Inicialização das variáveis de conexão e cursor.
    conexao = None
    cursor = None

    try:
        # Abre conexão com o banco de dados.
        conexao = conectar()

        # Cria o cursor usado para executar comandos SQL.
        cursor = conexao.cursor()

        # Executa a consulta usando parâmetro (%s).
        # Isso evita SQL Injection porque o valor informado pelo usuário é tratado
        # como dado, e não como parte do comando SQL.
        cursor.execute(
            """
            SELECT nome, localizacao, area_total
            FROM propriedade
            WHERE area_total >= %s
            ORDER BY area_total DESC;
        """,
            (area_minima,),
        )

        # Recupera todos os resultados retornados pela consulta.
        resultados = cursor.fetchall()

        print(f"\n=== Propriedades com área >= {area_minima} ===")

        # Caso nenhuma propriedade seja encontrada, informa o usuário.
        if not resultados:
            print("Nenhuma propriedade encontrada.")
        else:
            # Exibe as propriedades encontradas em formato resumido.
            for nome, localizacao, area_total in resultados:
                print(f"{nome} | {localizacao} | {area_total} ha")

    except Exception as erro:
        # Em caso de erro, exibe uma mensagem amigável sem encerrar o programa.
        print("Erro ao consultar propriedades por área.")
        print(erro)

    finally:
        # Fecha o cursor, se ele tiver sido criado.
        if cursor:
            cursor.close()

        # Fecha a conexão com o banco, se ela tiver sido aberta.
        if conexao:
            conexao.close()


def menu():
    """
    Exibe o menu principal da aplicação AgroTrace Mini.

    A função mantém um laço de repetição que apresenta as opções disponíveis ao
    usuário e chama a função correspondente à opção escolhida. O menu é voltado ao
    uso em linha de comando e permite demonstrar funcionalidades de cadastro e
    consulta conectadas ao banco de dados.
    """

    while True:
        # Exibe as opções disponíveis para o usuário final.
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

        # Lê a opção escolhida pelo usuário.
        opcao = input("Escolha uma opção: ")

        # Direciona a execução para a funcionalidade correspondente.
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