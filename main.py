import sys
import datetime
import os
import json

from scraper.download_results import sync_contests, fetch_all_results

SYNC_FILE = "sync_info.json"
RESULTS_FILE = "lotofacil_resultados.json"
EXCEL_FILE = "lotofacil_resultados.xlsx"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_last_sync():
    if os.path.exists(SYNC_FILE):
        try:
            with open(SYNC_FILE, "r") as f:
                data = json.load(f)
                return datetime.datetime.fromisoformat(data["last_sync"])
        except:
            pass
    return None

def update_sync_time():
    with open(SYNC_FILE, "w") as f:
        json.dump({"last_sync": datetime.datetime.now().isoformat()}, f)

def cmd_update():
    print("\n--- ATUALIZAR RESULTADOS E JOGOS SORTEADOS ---")
    print("Iniciando verificação de novos concursos...")
    contests = sync_contests(json_path=RESULTS_FILE, excel_path=EXCEL_FILE)
    if contests and len(contests) > 0:
        update_sync_time()
        last = contests[-1]
        print(f"\n✅ Base de dados e lista de jogos sorteados 100% atualizadas!")
        print(f"   Total de concursos: {len(contests):,}")
        print(f"   Último concurso: #{last['concurso']} ({last.get('data', '')})")
        print(f"   Dezenas: {' '.join(f'{n:02d}' for n in last['dezenas'])}")
        print(f"   Arquivos sincronizados:")
        print(f"     📁 JSON:  {RESULTS_FILE}")
        print(f"     📊 Excel: {EXCEL_FILE}")
    else:
        print("❌ Falha ao atualizar os resultados.")

from ui.movement_table import render_movement_table

from ui.stats_view import menu_estatisticas
from ui.generator_view import run_game_generator

def cmd_view_results():
    print("\n--- TABELA DE MOVIMENTAÇÃO ---")
    render_movement_table(RESULTS_FILE)

def main_menu():
    while True:
        clear_screen()
        print("======================================")
        print("         LOTOFÁCIL ANALYTICS          ")
        print("======================================")
        last_sync = get_last_sync()
        if last_sync:
            print(f"Última atualização: {last_sync.strftime('%d/%m/%Y às %H:%M')}")
        else:
            print("Última atualização: NUNCA")
        
        print("\nEscolha uma opção:")
        print("  0 - Atualizar Base de Dados")
        print("  1 - Tabela de Movimentação (Ciclos & Resultados)")
        print("  2 - Ver Estatísticas Avançadas")
        print("  3 - Gerar Jogos")
        print("  S - Sair")
        
        op = input("\nOpção: ").strip().lower()
        
        clear_screen()
        
        if op == "0":
            cmd_update()
            input("\n[ Pressione ENTER para voltar ao menu ]")
        elif op == "1":
            cmd_view_results()
            input("\n[ Pressione ENTER para voltar ao menu ]")
        elif op == "2":
            menu_estatisticas(RESULTS_FILE)
        elif op == "3":
            run_game_generator(RESULTS_FILE)
        elif op == "s" or op == "sair":
            print("Até logo!\n")
            break
        else:
            print("Opção inválida. Tente novamente.")
            input("\n[ Pressione ENTER para voltar ao menu ]")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nAté logo!\n")
        sys.exit(0)
