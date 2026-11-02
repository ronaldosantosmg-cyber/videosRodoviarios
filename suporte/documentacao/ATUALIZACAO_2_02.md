# Rodovia Studio 2.02 (sobre a 2.01)

**Estado: gerado SEM a validação completa.** O `validar_entrega.py` não passou neste ambiente (109 falhas no gate; 56 sem navegador falham igual na branch original). Nada foi validado no Windows/WebView2.

## Por que existe
O pacote "2.42.38" (numeração errada) foi instalado e o atualizador só aplica versão MAIOR que a instalada; por isso 2.00 e 2.01 foram arquivados em `atualizacoes/aplicadas` sem serem aplicados. A versão instalada foi corrigida para 1.42.38 (sua linhagem real) e esta 2.02 passa a ser aplicável. A série segue 2.02, 2.03...

## Feito
- Atualizador: quando um pacote tem versão menor que a instalada, a mensagem agora diz que ele NÃO foi aplicado, por quê, e que para voltar de versão se usa "RESTAURAR VERSAO ANTERIOR".
- Inclui tudo da 2.00 e 2.01: Retirar imagem no painel de camadas; seleção sem roubo por texturas; limpeza sem travar e reinício de análises; caminhos e nomes longos; motivo por segmento sem rota e corte de 256 rotas preservando o eixo principal (cálculo das rotas inalterado).

## Medido
- Teste novo do atualizador (`test_v14238_atualizacao`) passa. Os demais testes novos da série passam; falhas vizinhas já existiam na branch original.

## Não verificado
- Gate completo; Windows/WebView2; projetos reais; tela cintilando e dificuldade de selecionar o eixo; alterações locais da 1.42.37.
