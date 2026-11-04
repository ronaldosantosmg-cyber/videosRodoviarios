# Rodovia Studio 3.23 — reparação de instalação e identidade do código

A exceção antiga de comboio mostrada pelo proprietário não existe no `fleet_policy.py` da 3.22. Duas revisões independentes por agentes de IA localizaram mecanismos que permitiam manter uma instalação/processo antigo apesar de um número de versão novo. Não houve consulta a provedores externos de IA.

## Correções

1. **Mesma versão pode ser reparada.** O atualizador anteriormente arquivava o ZIP de versão igual sem conferir os arquivos instalados. Agora confere os destinos por SHA-256: se houver arquivo ausente ou divergente, reaplica com backup, sem exigir aumentar artificialmente a versão.
2. **Conferência depois da cópia.** Todos os destinos do pacote são conferidos antes de anunciar sucesso. Divergência aciona a restauração transacional existente. O instalador não declara sucesso se um antivírus/disco tiver impedido a gravação.
3. **Cache Python por conteúdo.** Fontes Python alteradas recebem bytecode `CHECKED_HASH`. Mesmo tamanho e carimbo de data não bastam para reaproveitar código antigo. A compilação não executa o código-fonte e acontece na atualização, não por quadro do vídeo.
4. **Sessão certa.** `run.py` só reutiliza servidor com mesma pasta, versão inicial, hash de fonte e prova da política de exportação. Sessão antiga/sem identidade não é silenciosamente usada como nova. Outra instalação identificada utiliza outra porta. Nenhum processo alheio é morto.
5. **Identidade real.** Saúde e logs registram PID, Python, pasta, caminho do módulo, fonte observado no carregamento, código efetivamente carregado e fonte atual no disco. Alterar apenas `VERSAO.json` não muda a versão já carregada registrada no processo.
6. **Diagnóstico visível.** Ajuda e Sobre → Diagnóstico da instalação, ou comando `DIAGNOSTICARINSTALACAO`. O status deixa de afirmar ambiente pronto quando a política não está identificada ou o fonte ficou indisponível/alterado.
7. **Limpeza dirigida.** A higiene da instalação identifica os cinco itens de desenvolvimento conhecidos (`tests`, `requirements-dev.txt`, `executar_testes_visuais.py`, `portao.py`, `TESTAR INTERFACE.cmd`) e os move para quarentena restaurável, com aplicativo fechado. Mantém os mecanismos anteriores para cópias legadas/duplicadas. Arquivos desconhecidos, fontes ativas, projetos, vídeos, recursos e runtime não são removidos por suposição.

A política de exportação permanece a da 3.22: comboio é diagnóstico sem bloqueio; colisões físicas e simulação incompleta continuam bloqueando. O motor físico e o aquecimento não foram alterados.

## Aplicação

Após cancelar a tarefa e aguardar o encerramento, feche o navegador **e o servidor na janela de comando**. Coloque o pacote na pasta de atualizações e execute o atualizador existente. A versão 3.23 é superior à 3.22 para permitir a primeira atualização por um atualizador antigo. Nas próximas reparações, o novo atualizador também reconhece divergência em versão igual.

Abra pelo **ABRIR RODOVIA STUDIO.cmd**. O fonte do iniciador C# também recebeu validação de identidade e mutex por instalação, mas não há executável novo compilado/homologado neste ambiente. Não se declara que um EXE antigo já ganhou essa correção.

Para a limpeza, com o aplicativo fechado, use o comando existente **LIMPAR E VERIFICAR.cmd**: apresenta inventário antes de mover. Os itens ficam em quarentena por pelo menos 30 dias desde a entrada. A atualização não executou limpeza remotamente na máquina do usuário.

## Distribuição e limites

Pacote de produção sem testes de desenvolvimento, com variante **sem HTML** para uma instalação funcional 3.18+. O complemento preserva os HTML existentes e não restaura arquivo colocado em quarentena pelo Defender. Os HTML não foram modificados ou disfarçados; o alerta continua pendente de análise Microsoft/TI.

A identidade da sessão não certifica todo comportamento do simulador. A reparação de implantação não é uma alegação de eliminação física universal de comboios. Consulte [a validação](VALIDACAO_3_23.md).

O nome do complemento passou a `RodoviaStudio_3_23_atualizacao_sem_html.zip`, reconhecido também pelo atualizador antigo. O nome anterior sem “atualizacao” podia ser ignorado na descoberta automática. A interface permite verificar/reparar a mesma versão; o atualizador compara os arquivos antes de decidir reaplicar.
