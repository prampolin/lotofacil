#!/bin/bash
echo "➡️  Encerrando os processos..."

# Como o nosso script de baixar resultados (download_results.py) executa 
# e termina em poucos segundos, ele não fica rodando em segundo plano.
# O comando abaixo mata qualquer processo python do scraper caso ficasse travado:
pkill -f "python scraper/download_results.py"

echo "✅ Processos encerrados!"
