# IA local 3B — integração em preparação

## Estado real

A integração de mini prompts, transporte, gestão do processo e revisão de respostas está implementada para testes. Não há pesos GGUF nem motor llama-server neste pacote de código. Não houve validação de inferência, português, acerto de correções ou desempenho de um modelo real em 8 GB. Não é uma entrega do modelo 3B pronto para uso.

O download oficial de modelos em huggingface.co retornou HTTP 403 na política de rede do ambiente. O rascunho de acesso a huggingface.co, cdn-lfs.huggingface.co e cas-bridge.xethub.hf.co foi salvo pelo configurador do ambiente, mas exige revisão, salvamento e publicação antes de ser aplicado. Nenhum endereço alternativo foi usado para contornar a política.

## Candidato selecionado

SmolLM3-3B Instruct, em GGUF Q4_K_M. A documentação oficial em https://github.com/huggingface/smollm confirma português e modo sem raciocínio estendido. A integração envia /no_think e enable_thinking=false para limitar contexto/latência. Isso não demonstra acerto ou desempenho. Os arquivos quantizados, licença aplicável, tamanho e checksums do modelo ainda precisam ser conferidos na distribuição.

## Integração

Projeto → IA local 3B (ou comando IA3B):

1. Escolha Arquivos, Fluxo selecionado, Estaqueamento, Texturas, Vídeo ou Diagnóstico geral.
2. Informe o pedido; texturas aceitam até oito nomes de camadas, um por linha. Sem seleção explícita, a consulta usa até três camadas.
3. Prepare e confira o mini prompt. Campos reconhecíveis de credenciais e caminhos são reduzidos; nomes e coordenadas podem continuar identificando o empreendimento.
4. Consulte o provedor, quando disponível.
5. Revise a resposta nas ferramentas existentes: correção validada de fluxo, revisão de camadas/texturas, vídeo, configuração ou proteção de dados.
6. Confirme e revalide no motor. A resposta não muda código, arquivos ou geometrias por si.

O sentido crescente do estaqueamento é a referência de esquerda/direita. A mensagem inclui inversão do eixo, configuração e regra dos vetores normais. Não se presume que a ordem dos vértices indique o sentido crescente; a interpretação ainda precisa da configuração correta e validação pelo motor.

## Perfil inicial para 8 GB

- GGUF 3B quantizado Q4_K_M, CPU, até quatro threads.
- Contexto de 2048 tokens, lote 128 e uma consulta por vez; saída de até 512 tokens.
- Pelo menos 3,5 GiB de memória disponível antes de iniciar. Esse é um limite inicial conservador, não garantia contra pressão de memória.
- Processo local encerrado após cada consulta ou cancelamento. Sem modelo persistente residente durante o vídeo.
- Início de cálculo/alteração de arquivos recusado durante consulta; IA recusada durante cálculo/vídeo pendente ou ativo. Pan/zoom continua no navegador.
- 120 s de prazo para inicialização e 180 s para resposta local. Descarregamento e timeout devem ser medidos com o modelo selecionado e o PC final.

Estimativa de disco adicional: aproximadamente 2–3 GB para pesos/modelo e dependências do provedor, ainda não medida. Os ZIPs históricos de atualização não contêm pesos. Não existe novo pacote final aprovado desta integração enquanto faltar validação com o modelo real.

## Pacote local a homologar

Fora da pasta do programa e dos ZIPs de atualização: <instalação>/modelos_ia/. No desenvolvimento: <dados>/_modelos_ia/.

Estrutura prevista:

- modelo.gguf
- runtime/llama-server.exe (Windows), DLLs necessárias; runtime/llama-server no teste Linux
- modelo.json com parameters_billions: 3, quantization: Q4_K_M e files mapeando cada caminho relativo para SHA-256.

Todos os arquivos necessários precisam constar no manifesto; links e caminhos externos são recusados. O manifesto detecta alteração/incompletude, mas não autentica o publicador. Candidato de runtime: llama.cpp b11669. Os arquivos oficiais Linux/Windows foram obtidos; a CLI Linux respondeu --help com as opções necessárias. Hashes e tamanhos foram registrados em evidencias/ia3b_preparacao. Isso não é teste de inferência ou da CPU Windows. Pesos, licença aplicável e compatibilidade final ainda exigem homologação. Não usar executáveis aleatórios ou arquivos retirados da quarentena.

## API online opcional

Compatibilidade prevista com chat completions JSON. Desativada enquanto não configurada pelo responsável pelo ambiente. Configuração em variáveis do processo, fora dos projetos e logs:

- RODOVIA_IA_ONLINE_URL: URL HTTPS completa do endpoint de chat completions.
- RODOVIA_IA_ONLINE_MODEL: identificador do modelo.
- RODOVIA_IA_ONLINE_KEY: credencial opcional; nunca gravada nos projetos.

A interface informa o domínio, apresenta o mini prompt e exige autorização explícita de envio para cada consulta online. Não segue redirecionamentos e não envia o desenho ou a imagem inteira. O provedor recebe o contexto mostrado; sua política de retenção deve ser considerada pelo usuário. Cancelamento online pode aguardar o encerramento/timeout da conexão. Não houve teste com provedor online real nesta preparação.

## Limites

Não é ajuste dos pesos nem autoaprendizado. São propostas e registros locais para revisão. Os testes com servidor HTTP de teste demonstram contrato, autenticação local e encerramento do processo; não demonstram a qualidade de um LLM. Esquema JSON e validação de escopo rejeitam ações/camadas desconhecidas; as regras físicas, revisão, confirmação e desfazer do motor continuam obrigatórias.
