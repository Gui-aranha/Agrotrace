# AgroTrace Mini

Protótipo simplificado do sistema AgroTrace para a disciplina de Bases de Dados.

## Requisitos

- Docker
- Docker Compose

## Como executar

```bash
docker compose up -d --build
docker compose run --rm app 
```

## Como acessar o banco pelo terminal

```bash
docker exec -it agrotrace_postgres psql -U agro_user -d agrotrace
```

## Teste
