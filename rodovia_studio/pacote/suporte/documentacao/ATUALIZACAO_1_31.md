# Rodovia Studio 1.31 — reorganização do código (sem funções novas)

Versão de manutenção. O aplicativo deve se comportar como a 1.30; o que mudou foi a organização interna. A meta é que
correções e funções novas fiquem mais rápidas e com menos risco de uma mudança desfazer outra.

## O que mudou por dentro

### Interface (navegador)
- **Antes:** um arquivo só, `app.js` (≈ 2.270 linhas longas, ≈ 420 kB), em que cada versão acrescentava blocos no fim que
  “embrulhavam” funções anteriores sem registro.
- **Agora:** **37 arquivos por assunto** em `app/js/` (`00_nucleo.js` … `99_registros.js`). O navegador continua recebendo um
  script só, montado na ordem dos números; cada parte começa com `// ==== arquivo: NN_assunto.js ====` para localizar erros.
- **Pontos de extensão com registro:** os 83 embrulhos antigos viraram `estender('função', …, 'rótulo')`, com a **mesma
  ordem e o mesmo efeito**. A lista de extensões por função aparece em **Ajuda › Sobre › Estrutura da interface**.
- **Registros:** `ferramenta()`, `comando()`, `itemFaixa()` e `itemArquivo()`. Uma ferramenta nova declara clique, Enter,
  Esc, opções e ícone num lugar só. As funções da 1.30 (rotas, trecho da rota, pincel, camadas, abrir/renomear/modelos)
  já usam os registros; ferramentas ou comandos com nome repetido dão erro na hora.
- **Estilos:** saíram do `index.html` para `app/estilo.css`, com as cores principais em variáveis (`:root`). Isso prepara
  um tema claro completo.
- **Correção encontrada pela verificação automática (ESLint):** a função `polyLen` estava declarada duas vezes (a 1.30
  acrescentou uma cópia idêntica). Sem efeito visível; removida.

### Servidor
- **Antes:** `server.py` com ≈ 1.100 linhas e todas as rotas.
- **Agora:** `server.py` só cria o aplicativo, o despachante de tarefas, a segurança e o tratamento de erros (≈ 70 linhas).
  As rotas ficam em `app/rotas/<assunto>.py`: páginas, projetos, modelos, editor, tarefas, arquivos, web, suporte e
  camadas; o que é comum (fila de tarefas, configuração, arquivos) em `comum.py`.
- **Mesmas rotas:** as 109 rotas da 1.30 continuam com o mesmo endereço e método, e a ordem relativa das que poderiam
  se confundir foi mantida (conferido por script).

### Documentação para manutenção
- **ARQUITETURA.md:** onde fica cada coisa e como acrescentar ferramenta, comando, item da faixa, rota ou extensão.

## Rede de proteção
- **Novo teste de estrutura (`test_v131.py`):** confere
  - os módulos da interface e o script montado;
  - nomes globais repetidos entre arquivos;
  - extensões só de funções existentes e nenhum embrulho antigo;
  - ESLint sem erros (variável indefinida, redeclaração, chave repetida, código inalcançável);
  - nenhum nome indefinido no Python (verificador próprio, `tests/nomes_indefinidos.py`);
  - nenhuma rota da 1.30 perdida;
  - CSS externo com variáveis;
  - na tela: ferramentas, comandos, faixa e menus registrados apontam para funções, sem nomes repetidos, e a página abre
    sem erros.

## Medido neste ambiente
- **Testes automáticos:** **263 passaram** (257 da 1.30 + 6 novos de estrutura).
  - Um teste antigo (`test_v17_speed`) passou a substituir o arquivo de referência em `app/rotas/tarefas.py`, onde a rota está agora.
- **Vídeo TH57:** quadros 14, 40 e 96 s e vista do trevo **idênticos à 1.30**, pixel a pixel. O motor de vídeo não foi tocado.
- **Tela:** capturas da 1.30 e da 1.31 nos mesmos passos (abrir projeto, rota, grupos do painel, gerenciador de camadas) comparadas pixel a pixel.
  - Iguais, exceto as datas dos projetos, uma mensagem de estado e a posição de rolagem da coluna esquerda.
  - Alinhada a rolagem, a coluna é igual (diferem só alguns pixels sob o cabeçalho fixo).
  - O CSS externo com variáveis desenha igual.
- **API:** as 109 rotas da 1.30 existem com o mesmo método e endereço, e a ordem das que poderiam se confundir foi mantida.
- **Tamanhos:**
  - `server.py` caiu de ≈ 1.100 para 69 linhas;
  - o maior arquivo de rotas tem 291 linhas;
  - a interface tem 37 arquivos.

## Não verificado / limitações
- **Arquivo antigo:** o atualizador não apaga arquivos. Por isso o `app/app.js` antigo é trocado por um aviso de 2 linhas (“não é mais usado”).
- **Windows:** não testado no seu computador.
- **Extensões antigas:** continuam sendo extensões em cadeia (agora registradas e listáveis), não registros. As funções
  novas e as da 1.30 já usam registros; migrar as antigas uma a uma é trabalho para versões seguintes, sempre com os
  mesmos testes.
- **Tema claro completo:** ainda não feito; a 1.31 só deixa as cores em variáveis.
