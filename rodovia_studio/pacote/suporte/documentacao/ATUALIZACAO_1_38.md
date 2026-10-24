# Rodovia Studio 1.38 — correção do instalador do leitor ECW

## O erro
- **O que aparecia:** ao clicar **Instalar leitor ECW interno**, a mensagem “A instalação do leitor ECW falhou” vinha com linhas do pip como `pyproject_hooks\_impl.py … get_requires_for_build_wheel`.
- **Causa:**
  - o pip não conseguiu baixar o GDAL **pronto para Windows** do índice Geospatial Wheels (provavelmente bloqueado pela rede ou pelo proxy da empresa);
  - então pegou o **código-fonte** do GDAL no PyPI e tentou **compilá-lo**, o que não é possível no Python portátil (sem compilador e sem as bibliotecas do GDAL).

## O que mudou
- **Nunca compila:** o instalador só aceita pacotes prontos (`--only-binary`). Se não houver pacote pronto, ele passa para a próxima forma em vez de tentar compilar.
- **Proxy do Windows:** o pip não lê sozinho o proxy configurado no Windows; agora o instalador passa esse proxy para o pip.
- **Download direto (nova tentativa automática):** se o pip falhar, o programa baixa os 2 arquivos diretamente, com o proxy e os certificados do Windows (que costumam funcionar na rede da empresa):
  1. **GDAL 3.11.4** para o Python do aplicativo (3.12, 64 bits): `gdal-3.11.4-cp312-cp312-win_amd64.whl`, do GitHub de Christoph Gohlke (geospatial-wheels, versão v2025.10.25);
  2. **plugin ECW 3.11.3**: `gdal_ecw-3.11.3-py3-none-win_amd64.whl`, do PyPI.
  - Os arquivos ficam guardados em `sistema\programa\pacotes_ecw` e são instalados de lá, sem internet. Numa reinstalação, já são usados direto.
- **Mensagem clara:** se tudo falhar, a mensagem diz o motivo em português (por exemplo “sem acesso ao servidor”, “tentou compilar do código-fonte”, “certificado recusado”) e mostra:
  - os 2 endereços para baixar no navegador;
  - a pasta onde copiá-los.
  - O rastreamento interno do pip não aparece mais. A tentativa completa fica em `sistema\programa\pacotes_ecw_log.txt`.

## O que fazer agora
1. Aplique a atualização e clique de novo em **Instalar leitor ECW interno (uma vez)**.
2. Se falhar de novo, siga a mensagem: baixe no navegador os 2 arquivos:
   - https://github.com/cgohlke/geospatial-wheels/releases/download/v2025.10.25/gdal-3.11.4-cp312-cp312-win_amd64.whl
   - https://pypi.org/project/gdal-ecw/#files (arquivo `gdal_ecw-3.11.3-py3-none-win_amd64.whl`)
3. Copie os 2 para `Rodovia_Studio\sistema\programa\pacotes_ecw` (crie a pasta se não existir) e clique em Instalar de novo.
- Se o driver ECW não carregar depois de instalado (“Can't load requested DLL”), falta o **Microsoft Visual C++ 2015-2022 (x64)**, que a TI instala.

## Medido neste ambiente
- **Testes automáticos:** **311** passaram (306 da 1.37 + 5 novos). Os novos testes cobrem:
  - pip chamado sempre com `--only-binary`;
  - a falha de compilação do seu erro (mesmo texto do pip) leva ao download direto dos 2 arquivos certos (GDAL cp312 win_amd64 do GitHub, plugin win_amd64 do PyPI), guardados em `pacotes_ecw` e instalados sem internet;
  - sem rede: mensagem em português com o motivo, os 2 endereços e a pasta, sem o rastreamento do pip; registro gravado;
  - proxy do Windows passado ao pip;
  - endereço do GDAL pela versão do Python.
- **Endereços conferidos na internet (23/10/2026):** a página de versões do geospatial-wheels lista `gdal-3.11.4-cp312-cp312-win_amd64.whl` na versão v2025.10.25; o PyPI lista `gdal_ecw-3.11.3-py3-none-win_amd64.whl`.
- **Download:** a função de download foi testada aqui com um servidor local.
- **Vídeo TH57 (projeto existente):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.37, pixel a pixel.
- **Atualização simulada da 1.37 para a 1.38:** aplicada pelo atualizador da 1.37, com 9 arquivos novos ou alterados; versão passou a 1.38.0 (esquema continua 29).

## Não verificado / limitações
- **Windows e rede da empresa:** a instalação real não foi feita aqui (este ambiente não tem acesso ao GitHub nem ao PyPI). Não sei se a rede da NOVA 381 libera github.com e files.pythonhosted.org; se não liberar, use o passo 2 acima.
- **Compatibilidade:** o GDAL 3.11.4 com o plugin ECW 3.11.3 (mesma série 3.11) não foi testado aqui com um ECW real.

## Próximas partes (estilo Twinmotion)
- **1.39:** vista inclinada sobre o terreno (MDT).
- **Depois:** modo 3D.
