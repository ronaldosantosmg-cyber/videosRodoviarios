# Rodovia Studio 2.07

**Estado: NÃO validada pelo gate nem em Windows/WebView2 (gate dispensado pelo usuário). Os testes novos de geometria foram escritos mas NÃO executados: o ambiente de montagem não tinha shapely/pytest. Nada em `main`.** Cumulativa sobre a 2.06.

## Novo
- **Fluxo sem pavimento (opcional, desligado por padrão):** em Tráfego, marque “🚧 Ocultar o fluxo onde faltar pavimento”. Para fluxos do eixo nativo, um vazio de pavimento (canteiro, semáforo com faixa de pedestre, obra) de até 150 m não corta mais o fluxo: os veículos somem 5 m antes e reaparecem quando o pavimento volta. Só vale se houver pavimento depois do vazio. Funciona na prévia e no 3D. Desmarcado, o comportamento é o da 2.06.
- **Ícones** decorativos (aria-hidden, sem mudar o nome acessível) em menus, itens de menu e botões (`92_icones_menus.js`).
- **Conferência antes do vídeo** (comando `CONFERIR`, botão 🚦 em Vídeo › Gerar): semáforo 🟢🟡🔴 reunindo os relatórios de layers, hachuras e eixos, e a lista de materiais/texturas que o vídeo usará.

## Ainda não feito
Separação de logs, medições antes/depois, aceitação com MP4/instalador/rollback, auditoria do caminho 3D, migração de todos os formulários para Aplicar.

## Instalação
Feche o app, rode `ATUALIZAR RODOVIA STUDIO.cmd`. Rollback: `RESTAURAR VERSAO ANTERIOR.cmd`. Projetos, vídeos, DXF/KMZ e cache GeoTIFF não são tocados.
