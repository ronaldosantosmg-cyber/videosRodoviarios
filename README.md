# Rodovia Studio 3.6

Editor e gerador de vídeos rodoviários a partir de DXF, com KML/KMZ e imagens como referências opcionais. A base principal agora é o **Rodovia Studio 3.6**, baseado na atualização 3.5 fornecida pelo proprietário. Consulte [as correções e medições da 3.6](ATUALIZACAO_3_6.md).

## Abrir no Windows

1. Extraia este repositório para uma pasta curta, como `C:\RodoviaStudio`.
2. Instale **Python 3.12 x64**, disponível pelo comando `py -3.12`.
3. Abra `ABRIR RODOVIA STUDIO.cmd` ou `ABRIR_INTERFACE.bat`. A preparação instala as dependências em um ambiente local, sem administrador.
4. A interface abre no navegador em `http://127.0.0.1:8765`. Mantenha o processo aberto durante a geração.

O código fonte e o ZIP do workflow não incluem Python portátil ou executável compilado. Ambos exigem Python 3.12; não geram o antigo aplicativo Tkinter.

## Desenvolvimento

```bash
python3.12 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
python -m pip install -r suporte/sistema/requirements-dev.txt
python suporte/sistema/run.py
```

`RODOVIA_DATA` e `RODOVIA_VIDEOS` permitem escolher as pastas de dados e vídeos. Sem essas variáveis, a instalação usa `projetos/` e `videos/`. Bancos, entradas CAD, logs, caches e vídeos locais não são versionados.

## Estrutura

- `suporte/sistema/app/`: backend FastAPI, interface web, geometria, tráfego e renderização.
- `suporte/sistema/assets/`: fontes, marca e texturas.
- `suporte/sistema/tests/`: testes originais do Studio.
- `suporte/documentacao/`: documentação histórica recebida.
- `scripts/` e `tests/`: empacotamento e validação da integração.
- `proveniencia/`: hashes dos arquivos de origem importados.
- `legado/`: aplicativo anterior, fora da inicialização e do build principal.
- `atualizacoes/`: pacotes de atualização.

## Validação e distribuição

```bash
python scripts/empacotar_studio.py --output /tmp/RodoviaStudio_3_6_atualizacao.zip
python -m pytest -q tests
```

A CI executa integração e regressões selecionadas; não equivale à suíte completa. Para executar todos os testes Studio: `cd suporte/sistema` e `python -m pytest tests`. Testes de navegador exigem `python -m playwright install chromium`. O portão original está em `suporte/sistema/portao.py`.

O workflow Windows gera um ZIP de atualização 3.6 com manifesto e hashes, validado pelo atualizador. O pacote não contém bancos ou projetos do usuário. Os tempos em [ATUALIZACAO_3_5.md](ATUALIZACAO_3_5.md) são medições históricas da origem, não garantias para outros computadores. Windows/WebView2 e o empreendimento completo precisam de validação no ambiente de destino.
