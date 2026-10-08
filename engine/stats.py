import collections

# Conjuntos predefinidos para as regras estatísticas
PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23}
BORDER = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
CENTER = {7, 8, 9, 12, 13, 14, 17, 18, 19}
CROSS = {3, 8, 11, 12, 13, 14, 15, 18, 23}

def calc_parity(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        odds = sum(1 for n in c['dezenas'] if n % 2 != 0)
        evens = 15 - odds
        pattern = f"{odds} ímpares / {evens} pares"
        freq[pattern] += 1
    return sort_freq(freq)

def calc_primes(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        count = sum(1 for n in c['dezenas'] if n in PRIMES)
        freq[f"{count} primos"] += 1
    return sort_freq(freq)

def calc_border(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        count = sum(1 for n in c['dezenas'] if n in BORDER)
        freq[f"{count} na moldura"] += 1
    return sort_freq(freq)

def calc_center(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        count = sum(1 for n in c['dezenas'] if n in CENTER)
        freq[f"{count} no miolo"] += 1
    return sort_freq(freq)

def calc_cross(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        count = sum(1 for n in c['dezenas'] if n in CROSS)
        freq[f"{count} na cruz"] += 1
    return sort_freq(freq)
    
def calc_sum(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        soma = sum(c['dezenas'])
        # Agrupa as somas de 10 em 10 para estatística visual
        group_start = (soma // 10) * 10
        group = f"Entre {group_start} e {group_start+9}"
        freq[group] += 1
    return sort_freq(freq)
    
def calc_rows(contests):
    freq = collections.defaultdict(int)
    for c in contests:
        r1 = sum(1 for n in c['dezenas'] if 1 <= n <= 5)
        r2 = sum(1 for n in c['dezenas'] if 6 <= n <= 10)
        r3 = sum(1 for n in c['dezenas'] if 11 <= n <= 15)
        r4 = sum(1 for n in c['dezenas'] if 16 <= n <= 20)
        r5 = sum(1 for n in c['dezenas'] if 21 <= n <= 25)
        pattern = f"{r1}-{r2}-{r3}-{r4}-{r5}"
        freq[pattern] += 1
    return sort_freq(freq)

def calc_repeated(contests):
    freq = collections.defaultdict(int)
    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    for i in range(1, len(sorted_contests)):
        prev = set(sorted_contests[i-1]['dezenas'])
        curr = set(sorted_contests[i]['dezenas'])
        repeated = len(prev.intersection(curr))
        freq[f"{repeated} repetidas"] += 1
        
    for i in range(15, 4, -1):
        k = f"{i} repetidas"
        if k not in freq:
            freq[k] = 0
            
    # Para as repetidas, pode ser mais interessante ordenar pelo número de repetidas (15 até 5) em vez de pela frequência.
    # Mas como sort_freq ordena por frequência, se o usuário quiser ver 15, 14, 13 no topo e eles têm frequência zero,
    # Eles ficariam no fim. Vou ordenar pela quantidade de repetidas (decrescente, 15, 14, 13...) se a string terminar em 'repetidas'.
    # Na verdade, posso só ordenar por frequência, e as menos frequentes aparecerão em baixo. O usuário consegue ver.
    # Porém, se o usuário pediu "Se repetiu 15, depois 14, 13..." talvez ordenado por categoria seja melhor.
    # Vamos criar uma lista ordenada pelos valores (15, 14, 13) para retornar
    
    return sorted(freq.items(), key=lambda x: int(x[0].split()[0]), reverse=True)

def calc_all_time_repeated(contests):
    import collections
    freq = collections.defaultdict(int)
    n = len(contests)
    
    # Pre-convert to sets for speed
    sets = [set(c['dezenas']) for c in contests]
    
    for i in range(n):
        s1 = sets[i]
        for j in range(i + 1, n):
            repeated = len(s1.intersection(sets[j]))
            freq[repeated] += 1
            
    res = {}
    for i in range(15, 4, -1):
        res[f"{i} repetidas"] = freq.get(i, 0)
        
    return sorted(res.items(), key=lambda x: int(x[0].split()[0]), reverse=True)

def calc_group_distribution_repetition(contests):
    """
    Calcula a análise de repetição da distribuição de dezenas por grupos (G1: 01-05 a G5: 21-25)
    entre concursos consecutivos.
    """
    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    total_transitions = len(sorted_contests) - 1
    if total_transitions <= 0:
        return None

    groups = [
        set(range(1, 6)),
        set(range(6, 11)),
        set(range(11, 16)),
        set(range(16, 21)),
        set(range(21, 26))
    ]
    group_labels = ["G1 (01-05)", "G2 (06-10)", "G3 (11-15)", "G4 (16-20)", "G5 (21-25)"]

    def get_signature(dezenas):
        s = set(dezenas)
        return tuple(len(s.intersection(g)) for g in groups)

    signatures = [get_signature(c['dezenas']) for c in sorted_contests]

    matching_counts = collections.Counter()
    group_repeats = [0] * 5
    exact_repeats = 0
    sig_repeats = collections.defaultdict(lambda: {'total': 0, 'repeated': 0})

    for i in range(total_transitions):
        s1 = signatures[i]
        s2 = signatures[i + 1]

        matches = sum(1 for g in range(5) if s1[g] == s2[g])
        matching_counts[matches] += 1

        for g in range(5):
            if s1[g] == s2[g]:
                group_repeats[g] += 1

        sig_repeats[s1]['total'] += 1
        if s1 == s2:
            exact_repeats += 1
            sig_repeats[s1]['repeated'] += 1

    matching_list = []
    for k in range(6):
        cnt = matching_counts[k]
        pct = (cnt / total_transitions) * 100
        matching_list.append((k, cnt, pct))

    group_list = []
    for g in range(5):
        cnt = group_repeats[g]
        pct = (cnt / total_transitions) * 100
        group_list.append((group_labels[g], cnt, pct))

    top_sig_repeats = []
    for sig, data in sig_repeats.items():
        if data['repeated'] > 0:
            pct = (data['repeated'] / data['total']) * 100
            sig_str = "-".join(map(str, sig))
            top_sig_repeats.append((sig_str, data['repeated'], data['total'], pct))

    top_sig_repeats.sort(key=lambda x: (x[1], x[3]), reverse=True)

    return {
        "total_transitions": total_transitions,
        "exact_signature_repeats": exact_repeats,
        "exact_signature_pct": (exact_repeats / total_transitions) * 100,
        "matching_groups": matching_list,
        "group_individuals": group_list,
        "top_repeated_signatures": top_sig_repeats
    }


def sort_freq(freq_dict):
    # Retorna lista de tuplas ordenada do mais frequente pro menos frequente
    return sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)


def calc_consecutive_draws(contests):
    """
    Calcula a maior sequência consecutiva de saídas para cada uma das 25 dezenas,
    bem como a sequência atual, histórico de ocorrências e distribuição global.
    """
    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    total_contests = len(sorted_contests)
    if total_contests == 0:
        return None

    results = {}
    global_streak_dist = collections.defaultdict(int)

    for n in range(1, 26):
        cur_streak = 0
        streak_start = None
        max_streak = 0
        max_occurrences = []
        all_streaks = []
        total_draws = 0
        prev_c_num = None

        for c in sorted_contests:
            c_num = c['concurso']
            drawn = n in c['dezenas']

            # Se houver salto na numeração de concursos durante uma sequência ativa
            if cur_streak > 0 and prev_c_num is not None and c_num != prev_c_num + 1:
                all_streaks.append((cur_streak, streak_start, prev_c_num))
                global_streak_dist[cur_streak] += 1
                if cur_streak > max_streak:
                    max_streak = cur_streak
                    max_occurrences = [(streak_start, prev_c_num)]
                elif cur_streak == max_streak:
                    max_occurrences.append((streak_start, prev_c_num))
                cur_streak = 0
                streak_start = None

            if drawn:
                total_draws += 1
                if cur_streak == 0:
                    streak_start = c_num
                cur_streak += 1
            else:
                if cur_streak > 0:
                    all_streaks.append((cur_streak, streak_start, prev_c_num))
                    global_streak_dist[cur_streak] += 1
                    if cur_streak > max_streak:
                        max_streak = cur_streak
                        max_occurrences = [(streak_start, prev_c_num)]
                    elif cur_streak == max_streak:
                        max_occurrences.append((streak_start, prev_c_num))
                    cur_streak = 0
                    streak_start = None
            prev_c_num = c_num

        # Se a sequência estava ativa no último concurso analisado
        if cur_streak > 0:
            last_c_num = sorted_contests[-1]['concurso']
            all_streaks.append((cur_streak, streak_start, last_c_num))
            global_streak_dist[cur_streak] += 1
            if cur_streak > max_streak:
                max_streak = cur_streak
                max_occurrences = [(streak_start, last_c_num)]
            elif cur_streak == max_streak:
                max_occurrences.append((streak_start, last_c_num))

        avg_streak = (sum(s[0] for s in all_streaks) / len(all_streaks)) if all_streaks else 0.0

        results[n] = {
            'number': n,
            'max_streak': max_streak,
            'max_occurrences': max_occurrences,
            'current_streak': cur_streak,
            'total_draws': total_draws,
            'draw_pct': (total_draws / total_contests) * 100,
            'total_streaks': len(all_streaks),
            'avg_streak': avg_streak,
        }

    ranking = sorted(results.values(), key=lambda x: (x['max_streak'], x['total_draws']), reverse=True)
    overall_record = ranking[0] if ranking else None

    # Distribuição global
    total_streaks_all = sum(global_streak_dist.values())
    distribution_list = []
    for length in sorted(global_streak_dist.keys()):
        cnt = global_streak_dist[length]
        pct = (cnt / total_streaks_all * 100) if total_streaks_all > 0 else 0.0
        distribution_list.append((length, cnt, pct))

    return {
        "total_contests": total_contests,
        "ranking": ranking,
        "results_by_number": results,
        "overall_record": overall_record,
        "global_streak_distribution": distribution_list,
        "total_streaks_all": total_streaks_all
    }


