"""Leitura única e robusta de DXF (padrão recomendado pela documentação do ezdxf):
1) leitura normal; 2) se falhar por estrutura/codificação, modo de recuperação (recover) com auditoria;
3) mensagens claras em português; DWG é reconhecido e recusado com orientação (o Rodovia Studio trabalha só com DXF)."""
import logging
from pathlib import Path
import ezdxf
from ezdxf import recover

log = logging.getLogger('rodovia.dxf')


def _assinatura(caminho):
    try:
        with open(caminho, 'rb') as f: return f.read(8)
    except OSError as e: raise ValueError(f'Não foi possível abrir o arquivo: {e}') from e


def ler(caminho, avisos=None):
    """Devolve o Drawing. Acrescenta em `avisos` (lista) o que foi recuperado/corrigido. Levanta ValueError em português."""
    caminho = Path(caminho)
    if not caminho.is_file(): raise ValueError('Arquivo DXF não encontrado.')
    if caminho.stat().st_size == 0: raise ValueError('O arquivo DXF está vazio (0 bytes).')
    sig = _assinatura(caminho)
    if sig[:2] == b'AC' and sig[2:6].isdigit():
        raise ValueError('Este arquivo é DWG. O Rodovia Studio lê somente DXF: no CAD, use "Salvar como" e escolha DXF.')
    try:
        doc = ezdxf.readfile(str(caminho))
        return doc
    except (ezdxf.DXFError, UnicodeDecodeError, ValueError, KeyError, IndexError, TypeError, AttributeError) as primeiro:
        log.warning('leitura normal falhou (%s); tentando recuperação', primeiro)
        try:
            doc, auditor = recover.readfile(str(caminho))
        except (ezdxf.DXFError, OSError, UnicodeDecodeError, ValueError, KeyError, IndexError, TypeError, AttributeError) as segundo:
            raise ValueError('DXF ilegível mesmo em modo de recuperação: ' + str(segundo)[:160]) from segundo
        corrigidos = len(getattr(auditor, 'fixes', []) or [])
        restantes = len(getattr(auditor, 'errors', []) or [])
        if avisos is not None:
            avisos.append(f'O DXF tinha falhas de estrutura e foi lido em modo de recuperação '
                          f'({corrigidos} correção(ões) automática(s), {restantes} problema(s) restante(s)). Confira o resultado.')
        log.warning('DXF recuperado: %s correções, %s erros restantes', corrigidos, restantes)
        return doc
    except OSError as e:
        raise ValueError(f'Não foi possível ler o DXF: {e}') from e
