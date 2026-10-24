# Validação do auxiliar de gravação pelo navegador

Oito testes em Chromium passaram: gravação dos bytes conferidos após seleção da pasta; recusa de SHA-256 divergente antes de criar arquivo; preservação de ZIP existente; recusa de pasta incorreta; cancelamento; rejeição de metadados inválidos; revogação de permissão de escrita; alternativa manual em navegador sem API.

O ZIP usado nos testes é o artefato 1.42.2 real. O canal estável foi comparado ao SHA-256 do arquivo. O servidor público raw.githubusercontent.com respondeu HTTP 200, 2.441.334 bytes e Access-Control-Allow-Origin: *, permitindo consulta pelo navegador.

Os testes usam a página real servida em localhost (contexto seguro) e simulam o diálogo de pasta e seu identificador de arquivo, sem alegar permissão real sobre o PC do usuário. A política do Chromium neste ambiente de nuvem bloqueia navegação file://; por isso a abertura direta do HTML local e a concessão interativa de acesso pelo Windows não foram validadas aqui. O Edge/Chrome do usuário pode impor políticas próprias; o link manual permanece disponível quando a API é bloqueada.

O aplicativo e o ZIP 1.42.2 não foram modificados. O gerador de futuras entregas passa a atualizar canal_estavel.json após validar e gerar o pacote. Nenhum arquivo local é enviado ao assistente nem ao GitHub pela página.
