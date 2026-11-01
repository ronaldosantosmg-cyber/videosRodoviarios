# Continuidade 2.63

Base: os três ZIPs enviados pelo usuário, aplicados na ordem 2.60 → 2.61 → 2.62. Integridade CRC e hashes declarados conferidos. Registro em origem-2.62.json. A antiga revisão 2.02 do GitHub não foi tratada como a mais recente. As notas abaixo distinguem conteúdo recebido de trabalho novo.

## Evolução recebida desde a revisão anterior do GitHub

- 2.60: cache com assinatura específica da leitura geométrica; máscaras regionais, índice espacial e verificações vetorizadas; otimizações de água. As medições TH57 das notas originais não foram reproduzidas nesta máquina.
- 2.61: correção da chave terrain na legenda e verificações de seleção/câmera nulas.
- 2.62: preservação do enquadramento ao redimensionar e proteção contra clique/arrasto acidental após alteração do layout.
- As três versões recebidas declaram validação incompleta; não herdam a aprovação de testes da 2.02. A reconstrução de rotas dessa base difere da antiga 2.02. Não foi transplantado um motor antigo sobre os fluxos que o usuário informou estarem funcionando.

## Alterações novas

- Pavimento: opção de apresentação exige que a carroceria inteira caiba na superfície pavimentada cadastrada. Aplicada no renderizador 2D/vídeo e nos dados 3D, inclusive cortando trilhas para impedir interpolação pelo intervalo sem pavimento. Não apaga rotas nem substitui o cálculo microscópico. Pavimento ausente ou incorretamente classificado exige corrigir o cadastro; não se inventa asfalto para liberar veículos.
- Sinalização: realce opcional da pintura, preservando desgaste/opacidade manuais. No WebGL, fitas com largura em metros substituem linhas de um pixel quando a opção está ativa. Não é uma certificação de projeto de sinalização.
- Seções: dividir uma seção em dois trechos, preparar intervalo seguinte e salvar edição pendente ao confirmar. Reutilização de eixo já vinculado evita duplicação acidental.
- PER: Excel/CSV existentes ganham prévia de localização pelo estaqueamento calibrado. Obras fora do eixo não são coladas à extremidade. Intervalos parcialmente abrangidos são indicados, mantendo os km originais. Coordenadas manuais são preservadas. Sem estaqueamento configurado, orienta configurar em vez de inventar localização.
- Importação rejeita quilômetros negativos/não finitos e sinaliza percentual/coordenadas não finitas. Alterações PER não invalidam a leitura do DXF.

## Limites

A revisão não contém novo modelo de IA, catálogo fotográfico completo, instalação Windows assinada nem reconstrução universal de rotas. Há validação Linux/Chromium e testes de vídeo; Windows nativo, projetos reais extensos e carga prolongada precisam de homologação específica. Preservar arquivos originais, projetos, vídeos e GeoTIFF persistentes.
