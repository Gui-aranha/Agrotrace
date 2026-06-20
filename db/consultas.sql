-- ==============================================================================
-- consultas.sql
-- Consultas de média e alta complexidade para o AgroTrace 5.0
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- CONSULTA 0: Listagem de todas as propriedades
-- Justificativa: Lista todas as propriedades por nome e localização, serve para a
-- visualização simples das propriedades cadastradas, sem querer ver todas as
-- informações de cada uma
-- ------------------------------------------------------------------------------
SELECT nome, localizacao
FROM propriedade
ORDER BY nome;
-- ------------------------------------------------------------------------------
-- CONSULTA 1: Relatório detalhado das propriedades
-- Justificativa: Fornece uma visão geral combinando o tamanho da propriedade, 
-- quantidade de talhões, todos os tipos de grãos já plantados e insumos químicos 
-- aplicados
-- ------------------------------------------------------------------------------
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


-- ------------------------------------------------------------------------------
-- CONSULTA 2: Última medição de cada sensor
-- Justificativa: É uma boa consulta aninhada e útil para rastreabilidade. Mostra
-- para cada sensor a medição mais recente
-- ------------------------------------------------------------------------------
SELECT
    s.nro_serie,
    s.nome,
    s.tipo_medicao,
    lm.data_hora,
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


-- ------------------------------------------------------------------------------
-- CONSULTA 3: Nota fiscal / relatório de transação
-- Justificativa: Realizar a rastreabilidade da comercialização dos produtos para
-- a confecção de notas fiscais. É a razão do banco de dados colher
-- as informações do cliente. Mostra quem comprou, quando comprou,
-- qual lote foi vendido, preço do produto, quantidade comprada,
-- valor total e de qual propriedade/talhão veio a produção.
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- CONSULTA 4: Operações com duração acima da média
-- Justificativa: Lista operações concluídas cuja duração ficou acima da 
--  média das operações concluídas registradas no sistema. auxiliando análises de 
-- eficiência operacional.
-- ------------------------------------------------------------------------------
SELECT
    o.id_operacao,
    o.data_hora_inicio,
    o.data_hora_fim,
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

-- ------------------------------------------------------------------------------
-- CONSULTA 5: Fornecedores com todos os grãos (DIVISÃO RELACIONAL)
-- Justificativa: Identificar fornecedores que possuem todos os tipos de grãos do
-- sistema para venda, é feito a partir dos lotes cadastrados.
-- ------------------------------------------------------------------------------

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