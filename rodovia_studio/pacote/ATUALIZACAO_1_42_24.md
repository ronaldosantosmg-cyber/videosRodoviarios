# Rodovia Studio 1.42.24

## Uso

Projeto → Analisar layers e eixos / IA abre o assistente; Ajuda → Diagnóstico dos logs / IA abre os registros.

- Logs e melhorias: agrupa erros retidos, apresenta hipóteses, orientação local e tempos observados. Não garante causa exata sem reprodução.
- Layers, texturas e eixos: Normal conserva o reconhecimento existente; IA local compara nomes com tipos de entidade; Manual permite ajustar. Escolha camadas e use Aplicar textura ou Aplicar Eixo. Confira a prévia e confirme. Aplicar Eixo associa a camada; sentido, origem e seção continuam em Tráfego.
- Perfis reutilizáveis: Salvar atualiza o perfil aberto; Salvar como cria outro; Importar/Exportar transfere JSON. Salvar perfil não aplica nem calcula o projeto.
- Tarefas difíceis / outra IA: descreva a tarefa e exporte o prompt. Confira os dados antes de compartilhar com outra IA. Importe a resposta JSON conforme o esquema incluído. Sugestões entram desmarcadas; não executam código nem alteram o projeto automaticamente.

## Área gráfica e barras

Atualizar, modo e progresso ficam na linha do SNAP/ORTO. X/Y acompanham o mouse durante o movimento; CRS, km e afastamento ficam no detalhe por hover/foco. Informações duplicadas foram recolhidas. Mais ferramentas expande na própria linha e tem seta para recolher; Vídeo recebeu atalhos funcionais. Os parâmetros de apresentação permanecem dentro de sua expansão, com rótulos e controles dimensionados.

## Proteções e limites

A assistência funciona localmente, sem instalação ou serviço de IA adicional. Usa regras e evidências, não um modelo neural. Os registros são os disponíveis no projeto; mensagens antigas ou incompletas podem exigir reprodução. A correlação não reconhece semanticamente uma imagem aérea.

Respostas e perfis são validados; IDs de outro projeto, fonte/configuração alterada, classes desconhecidas e materiais incompatíveis são rejeitados. Substituir uma classificação existente exige opção explícita e revisão. DXF original, sentidos, seções, desligamentos manuais e demais configurações são preservados. Camadas com hachuras não viram eixo pelo assistente; use seleção individual em Tráfego. Limite: 2.000 camadas por análise, 500 regras por perfil, importação de 2 MiB.

Materiais explícitos por hachura prevalecem sobre o perfil da camada. Materiais de pavimento concreto/asfalto são encaminhados ao motor existente. Abrir/salvar projeto/prévia/vídeo mantêm a política de atualização completa da revisão 1.42.23; confirmações de formulários respeitam o modo Manual/Automático.

## Atualização

Copie o ZIP para atualizacoes/ da instalação e use a atualização do próprio aplicativo. Guarde snapshot e projetos. Não extraia sobre projetos/ ou videos/. O atualizador preserva dados e disponibiliza rollback.

Os ensaios desta revisão e suas limitações ficam em suporte/documentacao/validacao_1_42_24. Validação Linux/Chromium/Mono não equivale à validação nativa Windows/WebView2 ou carga prolongada.
