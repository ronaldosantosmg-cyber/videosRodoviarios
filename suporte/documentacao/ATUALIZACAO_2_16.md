# Rodovia Studio 2.16

**Estado: NÃO validada pelo gate completo nem em Windows/WebView2.** Cumulativa sobre a 2.15.

## Substituir o DXF/KMZ a pedido do usuário
Problema: o envio de um novo DXF era recusado enquanto o motor tinha uma tarefa (cálculo, prévia, vídeo) ou a IA ativa, no cliente (“Envio aguardando…”) e no servidor (409 “Aguarde a tarefa atual”), e uma tarefa travada impedia a troca indefinidamente. Além disso, no Windows a troca do arquivo podia falhar se algo o estivesse segurando.
- Interface: ao enviar um arquivo com o motor ocupado, abre uma confirmação “Interromper e substituir”. Se o usuário aceita, a tarefa é cancelada e o arquivo é trocado; se recusa, nada muda.
- Servidor: `POST /api/projects/{id}/files?force=1` (só por pedido explícito) cancela a consulta de IA e as tarefas do projeto, espera o supervisor encerrar o processo do motor (até 40 s) e só então troca. Se o motor não encerrar, devolve erro claro e o projeto não é tocado. Sem `force`, a proteção continua a mesma.
- A troca do arquivo (`os.replace`) tenta de novo por até ~12 s quando o Windows reporta arquivo em uso, e falha com mensagem clara sem alterar nada.
- O DXF/KMZ anteriores continuam no histórico da importação (recuperável); projetos, vídeos e cache não são apagados.

Testes executados (3, servidor real com TestClient): recusa sem pedido; troca com o motor soltando a tarefa; erro claro e projeto intacto se o motor não encerrar; retentativa quando o arquivo está em uso. NÃO verificado: Windows/WebView2, processo real de cálculo segurando o arquivo.
