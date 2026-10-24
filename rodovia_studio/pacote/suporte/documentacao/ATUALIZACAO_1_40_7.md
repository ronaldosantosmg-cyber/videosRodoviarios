# Rodovia Studio 1.40.7 — Base de imagens, temporários e testes visuais ampliados

## Imagens ECW/MrSID

- A conversão validada para GeoTIFF é registrada em `projetos/_base_imagens/<sha256>/`.
- Ao receber novamente o mesmo arquivo-fonte, o SHA-256 identifica a conversão já existente e evita nova conversão.
- O projeto continua usando `imagem_local/<arquivo>_convertido.tif`, preservando o formato dos projetos anteriores.
- Quando o sistema de arquivos permite, o arquivo do projeto é um hardlink para a base, evitando duplicar arquivos de vários GB; caso contrário, usa cópia compatível.
- A base persistente não é tratada como cache regenerável e não é apagada por “Limpar memória” sem seleção explícita.

## Higiene de processamento

- Intermediários de ortomosaico/conversão usam `projetos/_temp/<sessão>/`.
- O encerramento normal elimina temporários da sessão e resíduos de processamento de projetos.
- Na próxima abertura, resíduos de sessões anteriores são removidos, cobrindo encerramentos abruptos.
- Projetos, configuração, DXF/DWG/KMZ, vídeos finais e a base persistente de GeoTIFFs não são apagados por essa limpeza.

## Testes visuais ampliados

Além dos testes da 1.40.6, a suíte valida:
- permanência do logo em layouts e modo Projeto;
- ordem visual de imagens (Topo/▲/▼/Fundo);
- regeneração repetida sem alterar escala/offset do viewport;
- painéis sem sobreposição em 1024×768;
- comando inválido sem travar a interface;
- hit-test em pixels para objetos sobrepostos;
- 50 ciclos de painéis + regeneração sem deriva nem erros de console.

## KMZ/KML

O KMZ/KML permanece como input opcional técnico. Atualmente pode:
- fornecer o eixo quando o DXF não contém eixo utilizável;
- conferir georreferenciamento/alinhamento DXF × KMZ;
- fornecer pontos/POIs;
- aparecer como vetor de referência no editor;
- participar da análise que alimenta o renderizador.

Portanto, não deve ser descartado globalmente. Em projetos com DXF completo e georreferenciamento confirmado, ele pode ser opcional, mas continua útil como fonte independente de conferência.
