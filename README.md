# AgroTrace 5.0

## Requisitos

- Docker
- Docker Compose

## Como executar

```bash
docker compose up -d --build
docker compose run --rm app 
```

## Como recriar o banco do zero

```bash
docker compose down -v
docker compose up -d --build
```

## Como acessar o banco pelo terminal

```bash
docker exec -it agrotrace_postgres psql -U agro_user -d agrotrace
```
## Como rodar em outro computador

```bash
git clone https://github.com/Gui-aranha/agrotrace.git
cd agrotrace
docker compose up -d --build
docker compose run --rm app
```
