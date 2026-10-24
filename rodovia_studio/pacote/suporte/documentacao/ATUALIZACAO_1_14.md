# Rodovia Studio 1.14 — pronto para outros modelos: camadas sem regras fixas e setas que reorientam o fluxo

## Leitura das camadas sem nada fixo no programa
- **Até a 1.13**, uma regra embutida transformava em “pista existente” qualquer camada de pavimento com EXIST no nome. Agora o tipo de cada camada é **sempre** o que está no mapeamento do projeto. Os projetos antigos foram migrados automaticamente para o mesmo resultado; os quadros do TH57 são idênticos aos da 1.13.
- **Tipos** (camada → tipo), qualquer camada para qualquer tipo:
  - eixo;
  - pista projetada e pista existente;
  - acostamento;
  - **bordo (linha de borda)** — novo;
  - canteiro e barreira;
  - OAE;
  - corte, aterro e **talude** (corte/aterro pela proximidade) — novo;
  - faixa de domínio;
  - **hidrografia** — nova.
- **Bordo**: se o DXF tiver as linhas de bordo, elas viram a sinalização de borda do vídeo e do editor, no lugar das linhas calculadas pelo contorno.
- **Hidrografia do DXF**: rios (linhas) e lagos/represas (polígonos) somam-se à base IBGE/OSM, ou a substituem quando a hidrografia pública está desligada. Recebem a mesma pintura de água.
- **Talude automático**: as hachuras “HATCH_MATERIAL” sem tipo continuam virando talude pela proximidade, mas agora é uma opção que pode ser desligada.
- **Perfis de camadas** (Configuração → Camadas e sentidos):
  - **Padrão**: reconhece os nomes mais comuns (EIXO, PAVIMENTO/HPAV, EXIST, ACOST, BORDO/LBO, OAE/PONTE/VIADUTO, CANTEIRO, NEW JERSEY/BARREIRA/DEFENSA, CORTE, ATERRO, DOMÍNIO/FD, HIDRO/RIO/CÓRREGO/LAGO).
  - **Salvar como perfil**: guarda o mapeamento atual para reutilizar em outros projetos com o mesmo padrão CAD.
  - **Editar regras**: uma regra por linha (`PADRÃO => tipo`), com * e ?, sem diferenciar maiúsculas nem acentos; vale a primeira regra que casar.
  - **Aplicar perfil**: preenche a lista, que continua editável camada a camada.
  - Os perfis ficam guardados em `projetos\_perfis_camadas.json`, de modo que valem para todos os projetos.
- **Ver camada**: a análise gera uma prévia simplificada de **todas** as camadas, inclusive as sem tipo. O botão **Ver** destaca a camada em magenta no editor e aproxima a vista. Com duas janelas, o destaque aparece na janela de visualização.
- **Cores por tipo**: ajusta a cor de cada tipo (pista, acostamento, canteiro, OAE, taludes, domínio…) na prévia e no vídeo.

## Setas que reorientam o fluxo
- **Ferramenta ↻ Girar seta**:
  - clique sobre uma seta de fluxo para **invertê-la**, ou clique e **arraste** para apontá-la;
  - a seta se alinha à faixa, portanto só pode apontar para um dos dois sentidos dela;
  - o **fluxo daquele trecho da via** (até a próxima junção) passa a seguir a seta;
  - o editor mostra a mudança na hora; **⟳ Atualizar fluxos** recalcula a rede, a sinalização e as setas do vídeo.
- A mudança fica salva como uma marcação de sentido (pode ser desfeita, refeita e excluída na lista “Setas de sentido”). O DXF não é alterado.

## Configuração
O esquema passou para a **versão 13**, com migração automática.

## Medido neste ambiente
- **TH57**: com a mesma configuração, os quadros de 14, 40 e 96 s e a vista do trevo são **idênticos aos da 1.13**, pixel a pixel.
- **Testes**: 142 automáticos passaram (7 novos):
  - perfil padrão reconhece todas as camadas do TH57 com o mesmo tipo de antes;
  - curingas e acentos; salvar, listar e excluir perfis; migração da pista existente;
  - **modelo de outra empresa** com camadas L01…L06: sem mapeamento não há eixo; com mapeamento funciona, com hidrografia do DXF pintada de azul e bordos do DXF usados como sinalização;
  - cores por tipo; API de perfis e prévia por camada;
  - editor: girar a seta inverte o sentido do trecho após “Atualizar fluxos”, perfil salvo e aplicado, “Ver” destaca a camada.

## Limitações
- **Girar seta**: muda o sentido do trecho entre junções inteiro. Para sentidos diferentes dentro do mesmo trecho, use também “Sentido” ou “Inverter fluxo”.
- **Camadas de blocos**: entidades dentro de blocos herdam a camada do bloco quando estão na camada 0, como antes.
