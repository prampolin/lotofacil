# Scraper da Lotofácil

Este script automatiza o download dos resultados da Lotofácil e os converte para um arquivo Excel (`lotofacil_resultados.xlsx`).

## Pré-requisitos

Você precisa ter o Python 3.8+ instalado.

## Como instalar as dependências

No terminal, na raiz do projeto ou dentro da pasta `scraper`, rode:

```bash
pip install -r scraper/requirements.txt
```

## Como executar

Basta executar o script Python:

```bash
python scraper/download_results.py
```

O arquivo `lotofacil_resultados.xlsx` será gerado/atualizado na raiz do seu projeto, contendo os resultados completos até o último sorteio.
