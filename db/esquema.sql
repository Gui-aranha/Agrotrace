-- esquema.sql
-- Projeto AgroTrace
-- Modelo relacional corrigido
-- PostgreSQL

BEGIN;

-- ============================================================
-- Limpeza das tabelas
-- A ordem abaixo permite recriar o banco durante os testes.
-- ============================================================

DROP TABLE IF EXISTS medicao CASCADE;
DROP TABLE IF EXISTS sensor CASCADE;
DROP TABLE IF EXISTS transacao CASCADE;
DROP TABLE IF EXISTS produto CASCADE;
DROP TABLE IF EXISTS colheita CASCADE;
DROP TABLE IF EXISTS residuo_insumo CASCADE;
DROP TABLE IF EXISTS aplica_insumo CASCADE;
DROP TABLE IF EXISTS insumo_recomendado CASCADE;
DROP TABLE IF EXISTS combate_praga CASCADE;
DROP TABLE IF EXISTS utiliza_graos CASCADE;
DROP TABLE IF EXISTS lote_insumo CASCADE;
DROP TABLE IF EXISTS lote_graos CASCADE;
DROP TABLE IF EXISTS operacao CASCADE;
DROP TABLE IF EXISTS talhao CASCADE;
DROP TABLE IF EXISTS consumidor CASCADE;
DROP TABLE IF EXISTS praga CASCADE;
DROP TABLE IF EXISTS insumo CASCADE;
DROP TABLE IF EXISTS fornecedor CASCADE;
DROP TABLE IF EXISTS grao CASCADE;
DROP TABLE IF EXISTS maquina CASCADE;
DROP TABLE IF EXISTS operador CASCADE;
DROP TABLE IF EXISTS agronomo CASCADE;
DROP TABLE IF EXISTS propriedade CASCADE;

-- ============================================================
-- Entidades principais
-- ============================================================

CREATE TABLE propriedade (
    nome              VARCHAR(100) NOT NULL,
    localizacao       VARCHAR(150) NOT NULL,
    area_total        NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_propriedade
        PRIMARY KEY (nome, localizacao),

    CONSTRAINT ck_propriedade_area_total
        CHECK (area_total > 0)
);

CREATE TABLE agronomo (
    cpf               CHAR(11) NOT NULL,
    crea              VARCHAR(30) NOT NULL,
    nome              VARCHAR(100) NOT NULL,
    especialidade     VARCHAR(100),

    CONSTRAINT pk_agronomo
        PRIMARY KEY (cpf),

    CONSTRAINT uq_agronomo_crea
        UNIQUE (crea),

    CONSTRAINT ck_agronomo_cpf
        CHECK (cpf ~ '^[0-9]{11}$')
);

CREATE TABLE operador (
    cpf               CHAR(11) NOT NULL,
    nro_registro      VARCHAR(30) NOT NULL,
    nome              VARCHAR(100) NOT NULL,
    habilitacao       VARCHAR(80),

    CONSTRAINT pk_operador
        PRIMARY KEY (cpf),

    CONSTRAINT uq_operador_nro_registro
        UNIQUE (nro_registro),

    CONSTRAINT ck_operador_cpf
        CHECK (cpf ~ '^[0-9]{11}$')
);

CREATE TABLE maquina (
    nro_serie         VARCHAR(50) NOT NULL,
    nome              VARCHAR(100) NOT NULL,
    modelo            VARCHAR(100),
    fabricante        VARCHAR(100),
    especialidade     VARCHAR(100),

    CONSTRAINT pk_maquina
        PRIMARY KEY (nro_serie)
);

CREATE TABLE grao (
    nome              VARCHAR(100) NOT NULL,
    tipo              VARCHAR(100),

    CONSTRAINT pk_grao
        PRIMARY KEY (nome)
);

CREATE TABLE fornecedor (
    cnpj              CHAR(14) NOT NULL,
    nome              VARCHAR(100) NOT NULL,
    certificacao1     VARCHAR(100) NOT NULL,
    certificacao2     VARCHAR(100) NOT NULL,
    certificacao3     VARCHAR(100),

    CONSTRAINT pk_fornecedor
        PRIMARY KEY (cnpj),

    CONSTRAINT ck_fornecedor_cnpj
        CHECK (cnpj ~ '^[0-9]{14}$')
);

CREATE TABLE insumo (
    nome                  VARCHAR(100) NOT NULL,
    categoria             VARCHAR(100),
    classe_toxicidade     VARCHAR(80),

    CONSTRAINT pk_insumo
        PRIMARY KEY (nome)
);

CREATE TABLE praga (
    nome                  VARCHAR(100) NOT NULL,

    CONSTRAINT pk_praga
        PRIMARY KEY (nome)
);

CREATE TABLE consumidor (
    cnpj              CHAR(14) NOT NULL,
    nome              VARCHAR(100) NOT NULL,
    telefone1         VARCHAR(20),
    telefone2         VARCHAR(20),
    email1            VARCHAR(100),
    email2            VARCHAR(100),

    CONSTRAINT pk_consumidor
        PRIMARY KEY (cnpj),

    CONSTRAINT ck_consumidor_cnpj
        CHECK (cnpj ~ '^[0-9]{14}$')
);

-- ============================================================
-- Estrutura produtiva
-- ============================================================

CREATE TABLE talhao (
    propriedade_nome          VARCHAR(100) NOT NULL,
    propriedade_localizacao   VARCHAR(150) NOT NULL,
    nro_talhao                INTEGER NOT NULL,
    area                      NUMERIC(12,2) NOT NULL,
    tipo_solo                 VARCHAR(100),
    cpf_agronomo              CHAR(11) NOT NULL,

    CONSTRAINT pk_talhao
        PRIMARY KEY (propriedade_nome, propriedade_localizacao, nro_talhao),

    CONSTRAINT fk_talhao_propriedade
        FOREIGN KEY (propriedade_nome, propriedade_localizacao)
        REFERENCES propriedade (nome, localizacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_talhao_agronomo
        FOREIGN KEY (cpf_agronomo)
        REFERENCES agronomo (cpf)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_talhao_area
        CHECK (area > 0),

    CONSTRAINT ck_talhao_nro
        CHECK (nro_talhao > 0)
);

-- ============================================================
-- Operações agrícolas
-- ============================================================

CREATE TABLE operacao (
    id_operacao               INTEGER GENERATED BY DEFAULT AS IDENTITY,
    cpf_operador              CHAR(11) NOT NULL,
    nro_serie_maquina         VARCHAR(50) NOT NULL,
    data_hora_inicio          TIMESTAMP NOT NULL,
    propriedade_nome          VARCHAR(100) NOT NULL,
    propriedade_localizacao   VARCHAR(150) NOT NULL,
    nro_talhao                INTEGER NOT NULL,
    data_hora_fim             TIMESTAMP,
    metodo                    VARCHAR(100),
    atividade                 VARCHAR(100) NOT NULL,

    CONSTRAINT pk_operacao
        PRIMARY KEY (id_operacao),

    CONSTRAINT fk_operacao_operador
        FOREIGN KEY (cpf_operador)
        REFERENCES operador (cpf)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_operacao_maquina
        FOREIGN KEY (nro_serie_maquina)
        REFERENCES maquina (nro_serie)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_operacao_talhao
        FOREIGN KEY (propriedade_nome, propriedade_localizacao, nro_talhao)
        REFERENCES talhao (propriedade_nome, propriedade_localizacao, nro_talhao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_operacao_datas
        CHECK (data_hora_fim IS NULL OR data_hora_fim >= data_hora_inicio)
);

-- ============================================================
-- Grãos e plantio
-- ============================================================

CREATE TABLE lote_graos (
    id_lote_grao       INTEGER GENERATED BY DEFAULT AS IDENTITY,
    cnpj_fornecedor    CHAR(14) NOT NULL,
    nome_grao          VARCHAR(100) NOT NULL,
    nro_lote           VARCHAR(50) NOT NULL,
    validade           DATE,
    quantidade         NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_lote_graos
        PRIMARY KEY (id_lote_grao),

    CONSTRAINT uq_lote_graos_fornecedor_lote
        UNIQUE (cnpj_fornecedor, nome_grao, nro_lote),

    CONSTRAINT fk_lote_graos_fornecedor
        FOREIGN KEY (cnpj_fornecedor)
        REFERENCES fornecedor (cnpj)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_lote_graos_grao
        FOREIGN KEY (nome_grao)
        REFERENCES grao (nome)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_lote_graos_quantidade
        CHECK (quantidade >= 0)
);

CREATE TABLE utiliza_graos (
    id_operacao_plantio       INTEGER NOT NULL,
    id_lote_grao              INTEGER NOT NULL,
    quantidade_por_hectare    NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_utiliza_graos
        PRIMARY KEY (id_operacao_plantio, id_lote_grao),

    CONSTRAINT fk_utiliza_graos_operacao
        FOREIGN KEY (id_operacao_plantio)
        REFERENCES operacao (id_operacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_utiliza_graos_lote_graos
        FOREIGN KEY (id_lote_grao)
        REFERENCES lote_graos (id_lote_grao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_utiliza_graos_quantidade
        CHECK (quantidade_por_hectare > 0)
);

-- ============================================================
-- Insumos, recomendações e combate a pragas
-- ============================================================

CREATE TABLE lote_insumo (
    id_lote_insumo     INTEGER GENERATED BY DEFAULT AS IDENTITY,
    cnpj_fornecedor    CHAR(14) NOT NULL,
    nome_insumo        VARCHAR(100) NOT NULL,
    nro_lote           VARCHAR(50) NOT NULL,
    validade           DATE,
    quantidade         NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_lote_insumo
        PRIMARY KEY (id_lote_insumo),

    CONSTRAINT uq_lote_insumo_fornecedor_lote
        UNIQUE (cnpj_fornecedor, nome_insumo, nro_lote),

    CONSTRAINT fk_lote_insumo_fornecedor
        FOREIGN KEY (cnpj_fornecedor)
        REFERENCES fornecedor (cnpj)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_lote_insumo_insumo
        FOREIGN KEY (nome_insumo)
        REFERENCES insumo (nome)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_lote_insumo_quantidade
        CHECK (quantidade >= 0)
);

CREATE TABLE combate_praga (
    nome_praga     VARCHAR(100) NOT NULL,
    id_operacao    INTEGER NOT NULL,

    CONSTRAINT pk_combate_praga
        PRIMARY KEY (nome_praga, id_operacao),

    CONSTRAINT fk_combate_praga_praga
        FOREIGN KEY (nome_praga)
        REFERENCES praga (nome)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_combate_praga_operacao
        FOREIGN KEY (id_operacao)
        REFERENCES operacao (id_operacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE insumo_recomendado (
    praga_nome           VARCHAR(100) NOT NULL,
    insumo_nome          VARCHAR(100) NOT NULL,
    dosagem_recomendada  NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_insumo_recomendado
        PRIMARY KEY (praga_nome, insumo_nome),

    CONSTRAINT fk_insumo_recomendado_praga
        FOREIGN KEY (praga_nome)
        REFERENCES praga (nome)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_insumo_recomendado_insumo
        FOREIGN KEY (insumo_nome)
        REFERENCES insumo (nome)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_insumo_recomendado_quantidade
        CHECK (dosagem_recomendada > 0)
);

CREATE TABLE aplica_insumo (
    id_operacao        INTEGER NOT NULL,
    id_lote_insumo     INTEGER NOT NULL,

    CONSTRAINT pk_aplica_insumo
        PRIMARY KEY (id_operacao, id_lote_insumo),

    CONSTRAINT fk_aplica_insumo_operacao
        FOREIGN KEY (id_operacao)
        REFERENCES operacao (id_operacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_aplica_insumo_lote_insumo
        FOREIGN KEY (id_lote_insumo)
        REFERENCES lote_insumo (id_lote_insumo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE residuo_insumo (
    id_lote_insumo      INTEGER NOT NULL,
    id_operacao         INTEGER NOT NULL,
    material_descarte   VARCHAR(100) NOT NULL,
    quantidade          NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_residuo_insumo
        PRIMARY KEY (id_lote_insumo, id_operacao, material_descarte),

    CONSTRAINT fk_residuo_insumo_aplica_insumo
        FOREIGN KEY (id_operacao, id_lote_insumo)
        REFERENCES aplica_insumo (id_operacao, id_lote_insumo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_residuo_insumo_quantidade
        CHECK (quantidade >= 0)
);

-- ============================================================
-- Colheita, produto e transação
-- ============================================================

CREATE TABLE colheita (
    id_operacao                         INTEGER NOT NULL,
    quantidade_colhida_por_hectare      NUMERIC(12,2) NOT NULL,
    quantidade_descartada               NUMERIC(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT pk_colheita
        PRIMARY KEY (id_operacao),

    CONSTRAINT fk_colheita_operacao
        FOREIGN KEY (id_operacao)
        REFERENCES operacao (id_operacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_colheita_quantidade_colhida
        CHECK (quantidade_colhida_por_hectare >= 0),

    CONSTRAINT ck_colheita_quantidade_descartada
        CHECK (quantidade_descartada >= 0)
);

CREATE TABLE produto (
    id_operacao       INTEGER NOT NULL,
    lote_produto      VARCHAR(50) NOT NULL,
    preco             NUMERIC(12,2) NOT NULL,
    quantidade        NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_produto
        PRIMARY KEY (id_operacao, lote_produto),

    CONSTRAINT fk_produto_colheita
        FOREIGN KEY (id_operacao)
        REFERENCES colheita (id_operacao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_produto_preco
        CHECK (preco >= 0),

    CONSTRAINT ck_produto_quantidade
        CHECK (quantidade >= 0)
);

CREATE TABLE transacao (
    id_operacao             INTEGER NOT NULL,
    lote_produto            VARCHAR(50) NOT NULL,
    cnpj_consumidor         CHAR(14) NOT NULL,
    data_compra             TIMESTAMP NOT NULL,
    valor_compra            NUMERIC(12,2) NOT NULL,
    quantidade_comprada     NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_transacao
        PRIMARY KEY (id_operacao, lote_produto, cnpj_consumidor, data_compra),

    CONSTRAINT fk_transacao_produto
        FOREIGN KEY (id_operacao, lote_produto)
        REFERENCES produto (id_operacao, lote_produto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_transacao_consumidor
        FOREIGN KEY (cnpj_consumidor)
        REFERENCES consumidor (cnpj)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_transacao_valor_compra
        CHECK (valor_compra >= 0),

    CONSTRAINT ck_transacao_quantidade_comprada
        CHECK (quantidade_comprada > 0)
);

-- ============================================================
-- Sensores e medições
-- ============================================================

CREATE TABLE sensor (
    nro_serie                  VARCHAR(50) NOT NULL,
    propriedade_nome           VARCHAR(100) NOT NULL,
    propriedade_localizacao    VARCHAR(150) NOT NULL,
    nro_talhao                 INTEGER NOT NULL,
    modelo                     VARCHAR(100),
    nome                       VARCHAR(100) NOT NULL,
    tipo_medicao               VARCHAR(100) NOT NULL,

    CONSTRAINT pk_sensor
        PRIMARY KEY (nro_serie),

    CONSTRAINT fk_sensor_talhao
        FOREIGN KEY (propriedade_nome, propriedade_localizacao, nro_talhao)
        REFERENCES talhao (propriedade_nome, propriedade_localizacao, nro_talhao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE medicao (
    nro_serie       VARCHAR(50) NOT NULL,
    data_hora       TIMESTAMP NOT NULL,
    valor           NUMERIC(12,4) NOT NULL,

    CONSTRAINT pk_medicao
        PRIMARY KEY (nro_serie, data_hora),

    CONSTRAINT fk_medicao_sensor
        FOREIGN KEY (nro_serie)
        REFERENCES sensor (nro_serie)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- ============================================================
-- Observações de implementação
-- ============================================================
-- 1. As tabelas utiliza_graos, aplica_insumo e colheita referenciam operacao.
--    Porém, a validação de que a atividade da operação corresponde ao tipo correto
--    de uso (plantio, aplicação de insumo ou colheita) deve ser feita na aplicação
--    ou por triggers.
--
-- 2. Os nomes foram padronizados sem acentos e sem espaços para facilitar o uso
--    no PostgreSQL e na aplicação.
--
-- 3. CPF e CNPJ foram armazenados como texto de tamanho fixo para preservar
--    zeros à esquerda.

COMMIT;
