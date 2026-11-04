# Correção individual — carregamento da política de exportação

O traceback que lança “Regra de ouro: comboio...” em `fleet_policy.py` é de uma implementação anterior à 3.22. Essa instrução não existe no arquivo publicado na 3.22. Uma cópia antiga no disco ou um processo já aberto pode continuar usando a implementação anterior.

O arquivo `RodoviaStudio_3_22_correcao_comboio.zip` contém somente `fleet_policy.py`, sem HTML, instalador ou executável. Não é um pacote do atualizador; destina-se à substituição manual do arquivo correspondente, com o aplicativo encerrado. A verificação antimalware permanece sujeita ao Defender/TI.

1. Solicite o cancelamento da tarefa e aguarde o encerramento.
2. Encerre completamente o Rodovia Studio, incluindo o servidor Python na janela de comando. Fechar apenas a aba do navegador não encerra o servidor.
3. Faça uma cópia de segurança de `C:\Projetos\Rodovia_Studio\sistema\programa\app\fleet_policy.py`.
4. Após verificação pelo antivírus, extraia o arquivo do ZIP e substitua exatamente esse destino. O nome deve ser `fleet_policy.py`, não `fleet_policy.py.txt`.
5. Reabra o Rodovia Studio e execute Preparar Rodovia Studio antes da geração.

Conferência somente de leitura no PowerShell:

```powershell
Get-FileHash -LiteralPath 'C:\Projetos\Rodovia_Studio\sistema\programa\app\fleet_policy.py' -Algorithm SHA256
```

Hash esperado do arquivo:

```text
b736d57b814fc718e80d869825c6cc7d4ee884c285429171f7a51f0e950db3f2
```

Se o hash for diferente, o destino ainda não é a cópia publicada. Se for igual e uma NOVA execução continuar lançando a antiga mensagem, confira a origem efetiva do processo Python e se existe outra instalação aberta. Não use um erro histórico como evidência de execução nova.

A decisão de exportação foi verificada com o caso informado: percurso 1, estação 135,37 m, instante 202,2 s, folga 8,088 m e 432,1 m até a saída. O checkpoint e a validação final não lançam a exceção por comboio. Isso testa a decisão de exportação, não afirma corrigir a causa física dessa aproximação. Colisões físicas continuam bloqueando.
