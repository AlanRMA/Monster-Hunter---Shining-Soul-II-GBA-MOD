# Monster Hunter Souls Arena — v0.3: hunts e pergaminhos

Abra `Monster Hunter Souls Arena - v0.3 Hunts.gba` no mGBA. A modificação está
na ROM: não é necessário Lua ou bridge. Para o primeiro teste, inicie a ROM
normalmente e crie um personagem; não carregue savestates de versões antigas.

## Compra e ativação

1. O personagem novo começa no hub, com 1.000 de dinheiro, sem a abertura do livro.
2. Fale com a NPC da lupa e avance a saudação com A.
3. Selecione um pergaminho na prateleira e pressione A. A compra desconta o
   preço, adiciona um item ao inventário e toca o som nativo de confirmação.
   A loja permanece aberta. Segurar A não compra repetidamente.
4. Saia da loja com B. Comprar ainda não ativa a hunt.
5. Abra **Start → Item**. Selecione o pergaminho, pressione A para pegá-lo,
   selecione **USE** à esquerda e confirme com A. A ativação consome esse
   pergaminho e libera duas mortes para o chefe escolhido. Feche o inventário.
6. Entre pela porta superior. Sem uma hunt ativada, a porta não funciona.

| Pergaminho | Preço | Arena nativa |
| --- | ---: | --- |
| Colonel Gobovich | 20 | Goblin Fort, contexto 1 / sala 7 |
| Grove Giant | 40 | Contexto 2 / sala 9 |
| Wizari | 70 | Contexto 3 / sala 14 |
| Clione | 100 | Contexto 4 / sala 12 |

Há somente uma hunt ativa por vez. Usar outro pergaminho durante uma hunt ativa
é recusado, sem consumir o novo item. Não há compra se faltar dinheiro ou espaço.
Os pergaminhos ainda não usados são itens normais do inventário e ficam no save.

## Morte, vitória e saída

- Primeira morte: retorno ao hub com HP/SP restaurados; a hunt continua,
  com uma morte restante. A arena anterior é encerrada, incluindo as rotinas,
  recursos temporários e referências do chefe. Reentrar inicia uma luta nova,
  com o chefe novamente com vida cheia.
- Segunda morte: retorno ao hub e encerramento da hunt. Para entrar de novo,
  compre e use outro pergaminho, ou use um que já estava guardado.
- Vitória: o evento nativo de conclusão retorna ao hub e encerra a hunt.
- As apresentações com diálogo dos quatro chefes são puladas; sua lógica
  original continua disponível. Animações de aparecimento e eventos de vitória
  continuam, incluindo os diálogos originais de encerramento.
- As saídas laterais permanecem bloqueadas.
- A saída inferior mantém o salvamento nativo e mostra, em páginas curtas:
  `Would you like to return main title? (You are currently in single player mode).`
  Avance o texto com A e escolha Yes/No na confirmação final.

A hunt ativada é temporária: sair para o título, carregar um personagem ou
reiniciar encerra sua ativação; ela não é gravada como um contrato ativo no
save. Pergaminhos ainda não usados e dinheiro continuam salvos normalmente.
O “Continue” retoma no hub, não na enfermaria original do castelo.

## Menu e música

A nova arte de floresta foi criada com ImageGen a partir das duas referências,
mantendo a identidade da logo Monster Hunter e o subtítulo Souls Arena.
Depois foi reduzida a 240×160 e adaptada a 15 bancos locais de paleta do GBA,
preservando o banco da fonte nativa. O original da arte e a prévia convertida
estão em `assets/menu-v03`.

O menu usa o tema indicado em https://www.youtube.com/watch?v=Fj4o3q659Z4,
com loop de aproximadamente 94,5 segundos. A conversão inclui ajuste de volume,
filtros de graves/agudos e uma emenda de 1,5 segundo. O driver nativo toca PCM
mono de 8 bits a 10.512 Hz; a prévia WAV usa contêiner de 16 bits. Não é uma
reorquestração em chiptune nem reprodução externa. Hub e batalha mantêm as
músicas da v0.2, e os efeitos sonoros continuam nativos.

## Verificação e limites

Os testes usam o núcleo isolado do mGBA 0.10.5, com cópias temporárias da ROM
e sem controlar a sessão aberta do usuário. Os relatórios em `validation/v03`
identificam o hash exato da ROM examinada.

- Quatro chefes: entrada sem A/diálogo, primeira morte, reentrada com HP cheio,
  segunda morte, porta bloqueada e vitória com retorno ao hub.
- Encerramento das cinco tarefas reservadas aos chefes e limpeza das quatro
  referências antigas antes da nova entrada.
- Compra única, som de confirmação, falta de dinheiro, bolsa cheia e cancelamento.
- Cinco NPCs restantes comparados com a v0.2 a partir do mesmo estado inicial;
  o estoque nativo não foi redesenhado.
- Título, menus, confirmação inferior, salvamento/Continue e pergaminho salvo.
- Áudio renderizado e repetição real dos três loops no mixer do jogo.

Nos testes de retorno, HP foi zerado apenas no emulador de diagnóstico para
acionar os eventos nativos; posições também foram ajustadas nesse núcleo.
Esses testes não são uma campanha inteira vencida manualmente. Drops,
recompensas, novos chefes, balanceamento, multiplayer, novos sistemas de
fabricação/economia e importação de saves de versões anteriores continuam fora
do escopo. Vida verde e SP amarelo foram preservados, sem redesenhar o SP.

Original, v0.1, v0.2 e seus saves existentes não foram substituídos. A ROM final
tem 32 MiB. O manifesto `mod-v0.3.json` registra a versão e as verificações.

## Reconstrução

`tools/v03/build_v03.py` aplica a nova versão à v0.2 de hash verificado. Utiliza
a montagem ARM/Thumb de `tools/v03/runtime.s`, os assets de `assets/menu-v03`
e `audio/converted/MENU-gba.pcm`. Não altera as ROMs anteriores.

`prepare_menu.py` recodifica a arte original guardada no projeto; exige Pillow,
NumPy e SciPy. `prepare_menu_music.py` reconverte o WAV baixado; exige FFmpeg
e NumPy. `verify_hunts.py`, `verify_regressions.py` e `verify_audio.py` executam
as verificações desta versão com o mGBA instalado neste Mac.
