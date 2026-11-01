# Auditoria da revisão 1.42.5

As evidências desta revisão ficam no repositório em rodovia_studio/evidencias/1.42.5 e na documentação do pacote. O gerador só aceita todos os testes obrigatórios aprovados, sem ignorados; inclui testes funcionais de rede, atualização/rollback, interface Chromium e WebGL real com SwiftShader, exportação MP4 completa e splash Mono/Xvfb.

A avaliação para uso intenso continua em 6,5/10: faltam execução nativa Windows/WebView2 e drivers de GPU, ensaios prolongados com muitos projetos, 4K em hardware representativo e validação técnica dos níveis/cotas de OAE. Uma prévia 3D funcional não comprova equivalência a simuladores profissionais nem conformidade CONTRAN. Usar em piloto controlado e preservar snapshots.

Limpeza conservadora: remove do ZIP os testes de desenvolvimento e relatórios históricos de atualização; mantém fontes, dependências locais/licenças, migrações, ficha técnica e rollback. Na instalação anterior, apenas testes cujo hash coincida com o manifesto arquivado são movidos ao snapshot recuperável. Não há exclusão geral de arquivos por extensão/nome ou de dados de projeto.

O DXF fornecido é validado separadamente, sem publicá-lo. Seu mapeamento automático não substitui o projeto salvo e a confirmação do CRS. O relatório th53_limites.json informa o cenário efetivamente exercitado; não se presume cobertura de todos os dispositivos mostrados nas imagens.
