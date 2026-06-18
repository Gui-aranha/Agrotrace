CREATE TABLE propriedade (
    id_propriedade SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    localizacao VARCHAR(150) NOT NULL,
    area_total NUMERIC(10,2) NOT NULL CHECK (area_total > 0)
);
