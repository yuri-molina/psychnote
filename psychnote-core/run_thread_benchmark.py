import json
import urllib.request
import urllib.error
import time
import random

def run_benchmark():
    print("=== INICIANDO BENCHMARK DE ESTRUTURA DE THREADS (OLLAMA) ===")
    print("Mapeando a latência do modelo llama3:8b-instruct-q4_K_M\n")
    
    url = "http://localhost:11434/api/generate"
    model = "llama3:8b-instruct-q4_K_M"
    
    # Lista de threads para avaliar
    threads_to_test = [2, 4, 6, 8, 10, 12, 14]
    results = {}
    
    # Prompt base grande (~500 tokens) para forçar o prefill
    # Usamos repetição de texto clínico para simular um prontuário médico
    base_text = (
        "Paciente masculino, 45 anos, com histórico de 10 anos de depressão recorrente. "
        "Apresenta-se com aparência descuidada, higiene pessoal precária. Humor depressivo acentuado, anedonia total. "
        "Relata fadiga extrema e lentificação psicomotora. Pensamento de conteúdo pessimista, com sentimentos de inutilidade. "
        "Admite pensamentos recorrentes sobre a finitude da vida, afirmando que nada funciona e talvez não haja mais o que fazer aqui. "
        "Nega planos imediatos, mas a ideação é persistente e estruturada. Declínio funcional significativo nos últimos 3 meses, "
        "afastado do trabalho, isolamento social completo, sono fragmentado, perda de peso de 5kg no último mês. "
    ) * 4  # Repete para aumentar o tamanho do prompt (~500 tokens)
    
    for t in threads_to_test:
        print(f"[*] Testando com num_thread = {t}...")
        
        # Injeta um token randômico no meio do prompt para quebrar o cache de prompt do Ollama
        # e forçar uma reavaliação (prefill) real a cada execução.
        salt = random.randint(100000, 999999)
        prompt = f"Nota Clínica ID {salt}: {base_text}\nResuma a avaliação de risco clínico em apenas 20 palavras."
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_thread": t,
                "temperature": 0,
                "num_predict": 30  # Limita a geração para focar no prefill e testar decode rápido
            }
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            start_wall = time.time()
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
            end_wall = time.time()
            
            # Extração dos dados de tempo do Ollama (retornados em nanossegundos)
            p_eval_count = resp_data.get("prompt_eval_count", 0)
            p_eval_ns = resp_data.get("prompt_eval_duration", 0)
            eval_count = resp_data.get("eval_count", 0)
            eval_ns = resp_data.get("eval_duration", 0)
            
            # Conversão para segundos e métricas de tokens por segundo
            p_eval_s = p_eval_ns / 1e9 if p_eval_ns else (end_wall - start_wall) # Fallback
            eval_s = eval_ns / 1e9 if eval_ns else 0
            
            prefill_tps = p_eval_count / p_eval_s if p_eval_s > 0 else 0
            decode_tps = eval_count / eval_s if eval_s > 0 else 0
            
            results[t] = {
                "prefill_s": p_eval_s,
                "prefill_tps": prefill_tps,
                "decode_s": eval_s,
                "decode_tps": decode_tps,
                "total_wall_s": end_wall - start_wall,
                "prompt_tokens": p_eval_count,
                "gen_tokens": eval_count
            }
            
            print(f"    [+] Prefill: {prefill_tps:.2f} t/s ({p_eval_s:.2f}s para {p_eval_count} tokens)")
            print(f"    [+] Decode:  {decode_tps:.2f} t/s ({eval_s:.2f}s para {eval_count} tokens)")
            print(f"    [+] Tempo Total: {end_wall - start_wall:.2f}s")
            
        except urllib.error.URLError as e:
            print(f"    [-] Erro ao conectar ao Ollama: {e}")
        except Exception as e:
            print(f"    [-] Erro inesperado: {e}")
            
    # Imprime tabela consolidada
    print("\n" + "="*80)
    print("=== RELATÓRIO COMPARATIVO DE THREADS (DESEMPENHO CPU) ===")
    print("="*80)
    print(f"{'Threads':<10}{'Prefill Speed (t/s)':<22}{'Decode Speed (t/s)':<22}{'Total Time (s)':<15}")
    print("-"*80)
    for t, data in results.items():
        print(f"{t:<10}{data['prefill_tps']:<22.2f}{data['decode_tps']:<22.2f}{data['total_wall_s']:<15.2f}")
    print("="*80)
    print("DICA: Analise qual contagem de threads maximiza a velocidade do prefill (ingestão) e do decode (geração).")

if __name__ == "__main__":
    run_benchmark()
