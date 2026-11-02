# Rodovia Studio 2.64

Continua a 2.63, preservando os fluxos, nós, seções e o filtro de apresentação sobre pavimento.

## Apresentação

Em **Cena → Materiais e texturas**:
- **Ultra realista — detalhe atual** identifica o perfil detalhado existente. Agora o microdetalhe usa escalas físicas fixas e transições suaves de resolução para reduzir cintilação ao variar o zoom.
- **Realista — menor microdetalhe** reduz a intensidade de relevo e ruído e simplifica a textura 3D. Use quando o detalhe excessivo prejudicar a leitura da pista e dos taludes.
- **Contornos técnicos na apresentação artística** controla as linhas amarelas de domínio. Desmarcado evita essas referências sobre a maquete; o modo Técnico continua mostrando os contornos. O desenho e os cálculos são preservados.

Aterros/terreno recebem aparência verde e cortes recebem pigmentação avermelhada. Cores manuais continuam prioritárias. O relevo dos taludes deixa de ser descartado no mosaico principal. O detalhe DXF passa a recuperar o estaqueamento dos pixels que não existiam no mosaico grosseiro, evitando ocultar partes legítimas da geometria durante a apresentação progressiva.

Não apaga entidades DXF para esconder linhas. Referências explicitamente cadastradas e a classificação correta de corte/aterro continuam dependendo do projeto. A gravação recebida foi analisada; sem a configuração exata do TH57 não se afirma reprodução integral desse projeto.

## Atualizar

Feche o programa. Coloque um único ZIP em `atualizacoes/` da instalação e use o atualizador. O pacote leve exige 2.63; use o completo em uma base anterior. Não sobrescreva projetos, vídeos ou imagens originais. Há snapshot e rollback.

## Validação

O GATE padrão cobre riscos desta revisão com testes de estabilidade de textura, materiais, preservação do desenho, salvamento/descarte, tráfego, vídeo e atualização. Mudanças detectadas fora do escopo visual elevam a regressão; `--amplo` continua disponível. Prazo excedido ou qualquer teste obrigatório reprovado bloqueia o pacote. Os relatórios indicam escopo e duração reais; não se trata de homologação universal do legado ou Windows nativo.
