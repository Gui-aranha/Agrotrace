-- dados.sql
-- Projeto AgroTrace
-- Dados iniciais de teste
-- 3 tuplas por tabela, seguindo a ordem das chaves estrangeiras.

BEGIN;

-- Opcional: permite rodar este arquivo mais de uma vez durante testes.
TRUNCATE TABLE
    medicao,
    sensor,
    transacao,
    produto,
    colheita,
    residuo_insumo,
    aplica_insumo,
    insumo_recomendado,
    combate_praga,
    utiliza_graos,
    lote_insumo,
    lote_graos,
    operacao,
    talhao,
    consumidor,
    praga,
    insumo,
    fornecedor,
    grao,
    maquina,
    operador,
    agronomo,
    propriedade
RESTART IDENTITY CASCADE;

-- ============================================================
-- Entidades principais
-- ============================================================

INSERT INTO propriedade (nome, localizacao, area_total) VALUES
    ('Fazenda Santa Clara', 'São Carlos - SP', 150.75),
    ('Sítio Boa Vista', 'Araraquara - SP', 82.30),
    ('Fazenda Horizonte Verde', 'Ribeirão Preto - SP', 230.00);

INSERT INTO agronomo (cpf, crea, nome, especialidade) VALUES
    ('11122233344', 'CREA-SP-1001', 'Ana Silva', 'Fitotecnia'),
    ('22233344455', 'CREA-SP-1002', 'Bruno Costa', 'Manejo de Pragas'),
    ('33344455566', 'CREA-SP-1003', 'Carla Mendes', 'Agricultura de Precisão');

INSERT INTO operador (cpf, nro_registro, nome, habilitacao) VALUES
    ('44455566677', 'OP-001', 'Diego Martins', 'Máquinas agrícolas'),
    ('55566677788', 'OP-002', 'Elisa Rocha', 'Pulverização agrícola'),
    ('66677788899', 'OP-003', 'Felipe Andrade', 'Colheitadeiras');

INSERT INTO maquina (nro_serie, nome, modelo, fabricante, especialidade) VALUES
    ('TRAT-001', 'Trator 1', 'MF 4707', 'Massey Ferguson', 'Preparo e plantio'),
    ('PULV-002', 'Pulverizador 1', 'Uniport 3030', 'Jacto', 'Aplicação de insumos'),
    ('COLH-003', 'Colheitadeira 1', 'S790', 'John Deere', 'Colheita');

INSERT INTO grao (nome, tipo) VALUES
    ('Soja', 'Oleaginosa'),
    ('Milho', 'Cereal'),
    ('Trigo', 'Cereal');

INSERT INTO fornecedor (cnpj, nome, certificacao1, certificacao2, certificacao3) VALUES
    ('11222333000144', 'AgroSeeds Brasil', 'MAPA', 'ISO 9001', 'GlobalG.A.P.'),
    ('22333444000155', 'NutriCampo Insumos', 'MAPA', 'ISO 14001', 'Boas Práticas Agrícolas'),
    ('33444555000166', 'BioProtec Agro', 'MAPA', 'Orgânico Brasil', 'ISO 9001');

INSERT INTO insumo (nome, categoria, classe_toxicidade) VALUES
    ('Fertilizante NPK 04-14-08', 'Fertilizante', 'Classe V'),
    ('Fungicida Triazol', 'Fungicida', 'Classe III'),
    ('Bioinseticida Bt', 'Bioinseticida', 'Classe IV');

INSERT INTO praga (nome) VALUES
    ('Lagarta-do-cartucho'),
    ('Ferrugem-asiática'),
    ('Percevejo-marrom');

INSERT INTO consumidor (cnpj, nome, telefone1, telefone2, email1, email2) VALUES
    ('44555666000177', 'Cooperativa Sul', '(16) 3000-1001', '(16) 3000-1002', 'compras@coopsul.com', 'logistica@coopsul.com'),
    ('55666777000188', 'Indústria Alimentos BR', '(11) 4000-2001', NULL, 'compras@alimentosbr.com', 'qualidade@alimentosbr.com'),
    ('66777888000199', 'Mercado Verde Atacado', '(19) 5000-3001', '(19) 5000-3002', 'comercial@mercadoverde.com', NULL);

-- ============================================================
-- Estrutura produtiva
-- ============================================================

INSERT INTO talhao (
    propriedade_nome,
    propriedade_localizacao,
    nro_talhao,
    area,
    tipo_solo,
    cpf_agronomo
) VALUES
    ('Fazenda Santa Clara', 'São Carlos - SP', 1, 50.00, 'Latossolo Vermelho', '11122233344'),
    ('Sítio Boa Vista', 'Araraquara - SP', 1, 30.00, 'Argissolo Vermelho-Amarelo', '22233344455'),
    ('Fazenda Horizonte Verde', 'Ribeirão Preto - SP', 2, 75.00, 'Latossolo Roxo', '33344455566');

-- ============================================================
-- Operações agrícolas
-- ============================================================

INSERT INTO operacao (
    id_operacao,
    cpf_operador,
    nro_serie_maquina,
    data_hora_inicio,
    propriedade_nome,
    propriedade_localizacao,
    nro_talhao,
    data_hora_fim,
    metodo,
    atividade
) VALUES
    (1, '44455566677', 'TRAT-001', '2026-01-10 07:00:00', 'Fazenda Santa Clara', 'São Carlos - SP', 1, '2026-01-10 11:30:00', 'Mecanizado', 'Ciclo produtivo da soja'),
    (2, '55566677788', 'PULV-002', '2026-01-12 08:00:00', 'Sítio Boa Vista', 'Araraquara - SP', 1, '2026-01-12 10:15:00', 'Pulverização controlada', 'Ciclo produtivo do milho'),
    (3, '66677788899', 'COLH-003', '2026-04-02 06:30:00', 'Fazenda Horizonte Verde', 'Ribeirão Preto - SP', 2, '2026-04-02 14:00:00', 'Colheita mecanizada', 'Ciclo produtivo do trigo');

-- ============================================================
-- Grãos e plantio
-- ============================================================

INSERT INTO lote_graos (
    id_lote_grao,
    cnpj_fornecedor,
    nome_grao,
    nro_lote,
    validade,
    quantidade
) VALUES
    (1, '11222333000144', 'Soja', 'LGS-2026-001', '2026-12-31', 1000.00),
    (2, '11222333000144', 'Milho', 'LGM-2026-001', '2026-11-30', 850.00),
    (3, '11222333000144', 'Trigo', 'LGT-2026-001', '2026-10-15', 500.00),
    (4, '33444555000166', 'Trigo', 'LGT-2026-002', '2026-10-31', 700.00);

INSERT INTO utiliza_graos (id_operacao_plantio, id_lote_grao, quantidade_por_hectare) VALUES
    (1, 1, 60.00),
    (2, 2, 55.00),
    (3, 3, 80.00);

-- ============================================================
-- Insumos, recomendações e combate a pragas
-- ============================================================

INSERT INTO lote_insumo (
    id_lote_insumo,
    cnpj_fornecedor,
    nome_insumo,
    nro_lote,
    validade,
    quantidade
) VALUES
    (1, '22333444000155', 'Fertilizante NPK 04-14-08', 'LINPK-2026-001', '2027-01-31', 1200.00),
    (2, '22333444000155', 'Fungicida Triazol', 'LIFUN-2026-001', '2026-09-30', 300.00),
    (3, '33444555000166', 'Bioinseticida Bt', 'LIBIO-2026-001', '2026-08-31', 250.00);

INSERT INTO combate_praga (nome_praga, id_operacao) VALUES
    ('Lagarta-do-cartucho', 2),
    ('Ferrugem-asiática', 1),
    ('Percevejo-marrom', 3);

INSERT INTO insumo_recomendado (praga_nome, insumo_nome, dosagem_recomendada) VALUES
    ('Lagarta-do-cartucho', 'Bioinseticida Bt', 1.50),
    ('Ferrugem-asiática', 'Fungicida Triazol', 0.80),
    ('Percevejo-marrom', 'Bioinseticida Bt', 1.20);

INSERT INTO aplica_insumo (id_operacao, id_lote_insumo) VALUES
    (1, 1),
    (2, 2),
    (3, 3);

INSERT INTO residuo_insumo (id_lote_insumo, id_operacao, material_descarte, quantidade) VALUES
    (1, 1, 'Embalagem de fertilizante', 2.00),
    (2, 2, 'Embalagem de fungicida', 1.00),
    (3, 3, 'Embalagem de bioinsumo', 1.00);

-- ============================================================
-- Colheita, produto e transação
-- ============================================================

INSERT INTO colheita (
    id_operacao,
    quantidade_colhida_por_hectare,
    quantidade_descartada
) VALUES
    (1, 3200.00, 100.00),
    (2, 4500.00, 150.00),
    (3, 2800.00, 80.00);

INSERT INTO produto (id_operacao, lote_produto, preco, quantidade) VALUES
    (1, 'PROD-SOJA-001', 120.50, 1500.00),
    (2, 'PROD-MILHO-001', 85.00, 1800.00),
    (3, 'PROD-TRIGO-001', 95.30, 1200.00);

INSERT INTO transacao (
    id_operacao,
    lote_produto,
    cnpj_consumidor,
    data_compra,
    valor_compra,
    quantidade_comprada
) VALUES
    (1, 'PROD-SOJA-001', '44555666000177', '2026-04-05 10:30:00', 60250.00, 500.00),
    (2, 'PROD-MILHO-001', '55666777000188', '2026-04-06 14:00:00', 76500.00, 900.00),
    (3, 'PROD-TRIGO-001', '66777888000199', '2026-04-07 09:45:00', 47650.00, 500.00);

-- ============================================================
-- Sensores e medições
-- ============================================================

INSERT INTO sensor (
    nro_serie,
    propriedade_nome,
    propriedade_localizacao,
    nro_talhao,
    modelo,
    nome,
    tipo_medicao
) VALUES
    ('SENS-001', 'Fazenda Santa Clara', 'São Carlos - SP', 1, 'SoilX-100', 'Sensor Umidade 1', 'Umidade do Solo'),
    ('SENS-002', 'Sítio Boa Vista', 'Araraquara - SP', 1, 'TempAgro-200', 'Sensor Temperatura 1', 'Temperatura'),
    ('SENS-003', 'Fazenda Horizonte Verde', 'Ribeirão Preto - SP', 2, 'pHField-300', 'Sensor pH 1', 'pH do Solo');

INSERT INTO medicao (nro_serie, data_hora, valor) VALUES
    ('SENS-001', '2026-01-10 12:00:00', 31.2500),
    ('SENS-002', '2026-01-12 12:00:00', 27.8000),
    ('SENS-003', '2026-04-02 15:00:00', 6.3500);

-- Atualiza as sequências das colunas identity após inserção manual de IDs.
SELECT setval(pg_get_serial_sequence('operacao', 'id_operacao'), COALESCE((SELECT MAX(id_operacao) FROM operacao), 1));
SELECT setval(pg_get_serial_sequence('lote_graos', 'id_lote_grao'), COALESCE((SELECT MAX(id_lote_grao) FROM lote_graos), 1));
SELECT setval(pg_get_serial_sequence('lote_insumo', 'id_lote_insumo'), COALESCE((SELECT MAX(id_lote_insumo) FROM lote_insumo), 1));

COMMIT;
