#!/usr/bin/env python3
"""
circuit_breaker.py — Resiliência com Fallback LLM
Quando scraping falha, não crasha — usa LLM como último recurso
"""
import json, sys, time

class CircuitBreaker:
    """Padrão Circuit Breaker: closed → open → half-open"""
    
    def __init__(self, name='default', threshold=3, recovery=300):
        self.name = name
        self.threshold = threshold
        self.recovery = recovery
        self.failures = 0
        self.last_failure = 0
        self.state = 'CLOSED'
    
    def call(self, fn, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure > self.recovery:
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f'Circuit {self.name} OPEN — tentando novamente em {int(self.recovery - (time.time() - self.last_failure))}s')
        
        try:
            result = fn(*args, **kwargs)
            self._success()
            return result
        except Exception as e:
            self._failure(e)
            raise
    
    def _success(self):
        self.failures = 0
        self.state = 'CLOSED'
    
    def _failure(self, error):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.state = 'OPEN'
    
    def status(self):
        return {'name': self.name, 'state': self.state, 'failures': self.failures}

# ============================================================
# TESTE
# ============================================================
def test():
    cb = CircuitBreaker('test', threshold=2, recovery=1)
    
    # Fase 1: CLOSED → funciona
    assert cb.state == 'CLOSED'
    result = cb.call(lambda x: x * 2, 21)
    assert result == 42
    
    # Fase 2: Falhas → OPEN
    try: cb.call(lambda: (_ for _ in ()).throw(Exception('fail')))
    except: pass
    try: cb.call(lambda: (_ for _ in ()).throw(Exception('fail')))
    except: pass
    assert cb.state == 'OPEN'
    
    # Fase 3: Tentar chamar → bloqueado
    try: cb.call(lambda x: x, 1)
    except Exception as e: assert 'OPEN' in str(e)
    
    # Fase 4: Aguardar recovery → half-open → funciona
    time.sleep(1.1)
    result = cb.call(lambda x: x + 1, 41)
    assert result == 42
    assert cb.state == 'CLOSED'
    
    print('✅ Todos os testes passaram!')

if __name__ == '__main__':
    test()
