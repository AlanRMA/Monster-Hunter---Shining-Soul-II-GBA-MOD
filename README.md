![IdeiaDeBackground](/Theme.jpeg)
# Shining Soul II — Registro de modding

Atualizado em: 26/09/2026.

Objetivo: estudar Shining Soul II para criar um mod inspirado em Monster Hunter, começando pela reutilização de uma sala de boss como arena.

## Ambiente e critérios de confirmação

- Jogo: Shining Soul II (USA).
- Emulador observado: mGBA 0.10.5, macOS.
- Hash e revisão exata da ROM: ainda não registrados.
- Os endereços abaixo foram observados nesta sessão. Sua estabilidade após reiniciar, carregar outro personagem ou trocar de classe ainda precisa ser testada.
- “Confirmado” significa observado nos testes ou diretamente demonstrado pelo código lido. Hipóteses estão identificadas.
- Endereços de RAM e VRAM não são offsets de arquivo da ROM. Alterações temporárias não constituem um patch permanente.

## Status — base de trabalho: 500

**STR** - 2 bytes - 02003C2C

**DEX** - 2 bytes - 02003C2E

**INT** - 2 bytes - 02003C30

**VIT** - 2 bytes - 02003C32

Os quatro atributos foram exibidos em 500 após as alterações. HP e SP máximos apareceram como 999.

Distinção importante: 500 é o limite normal relatado para STR, DEX e INT. Para VIT, o limite normal relatado é 333; a edição direta permitiu exibir 500. Isso não confirma benefício adicional acima de 333 nem o limite interno do campo.

Fonte sobre limites normais: [guia de Shining Soul II](https://gamefaqs.gamespot.com/gba/589485-shining-soul-ii/faqs/30780).

Exemplo de escrita, seguido de `c` em uma entrada separada:

```text
w/2 $02003C2C 500
```

### Cópias temporárias dos atributos

- `020327C0` e `02032800` acompanharam STR = 19, mas as alterações foram sobrescritas.
- A rotina próxima de `0801B830` copiou o valor original para uma área temporária.
- `02003C2C` foi identificado como origem da STR nessa cópia; alterar essa origem resolveu o teste.

## Eric Skills — Master = nível 7

Base de endereços solicitada pelo usuário:

**Sword** - 2 bytes* - 02003C50

**Axe** - 2 bytes* - 02003C54

**Spear** - 2 bytes* - 02003C58

**Shield** - 2 bytes* - 02003C5C

**Armor Up** - 2 bytes* - 02003C60

**Efficacy** - 2 bytes* - 02003C64

**Counter** - 2 bytes* - 02003C68

**Tactics** - 2 bytes* - 02003C6C

\* “2 bytes” preserva a base solicitada, mas não é um tamanho de campo confirmado. Shield respondeu inicialmente a uma escrita de 2 bytes; Axe foi confirmado em níveis 1 e 7 usando escrita de 1 byte. O espaçamento entre os endereços é 4 bytes, o que também não prova que o campo de nível ocupe 4 bytes. Para os próximos testes, usar `w/1` no byte identificado até entender os bytes vizinhos.

- Confirmados individualmente: Axe e Shield; Shield exibiu Lv 7 / MASTER.
- Sword, Spear, Armor Up, Efficacy, Counter e Tactics seguem o padrão observado, mas ainda não tiveram confirmação individual explícita no registro.
- A hipótese anterior de espaçamento de 2 bytes foi descartada após comportamento visual incorreto. Não usar aquela tabela antiga.
- Outra classe pode usar as mesmas posições para habilidades diferentes, ou mudar a base da estrutura. Ainda não testado.

Comandos de teste para Master; executar um por vez e conferir o menu antes de salvar:

```text
w/1 $02003C50 7
w/1 $02003C54 7
w/1 $02003C58 7
w/1 $02003C5C 7
w/1 $02003C60 7
w/1 $02003C64 7
w/1 $02003C68 7
w/1 $02003C6C 7
```

## Experiência e HP — dados secundários

- XP: `02003C38` e `03003E50` acompanharam a mudança de 264 para 312.
- Foi proposto `w/2 $02003C38 1000`; capturas posteriores mostram nível 4 e EXP 1020, mas não houve registro controlado que confirme sozinho a origem principal e a persistência.
- O tamanho total do campo de XP ainda é desconhecido. Uma busca de 2 bytes pode encontrar só a parte baixa de um campo maior.
- HP: `0200B260` e `03003ED0` foram candidatos quando o HP era 8. A origem principal não foi confirmada; não tratá-los como mapa definitivo de HP.

## Arena do boss — camadas gráficas

Nome do boss/fase: ainda não registrado. Preservar um save state da sala, pois o jogador não consegue simplesmente sair e entrar novamente.

| Camada | Map base em VRAM | Conteúdo observado | Prioridade |
|---|---|---|---:|
| BG0 | `0600E000` | Interface de HP, SP e Soul | 0 |
| BG1 | `0600E800` | Partes de paredes e vegetação | 1 |
| BG2 | `0600F000` | Outras partes de paredes e vegetação | 2 |
| BG3 | `0600F800` | Chão e base do cenário | 3 |

- Todas apresentaram Tile base `06000000` e tamanho gráfico carregado de 256 × 256 pixels.
- BG0 tinha Offset 0, 0. BG1–BG3 tinham inicialmente Offset 65, 108.
- BG3 depois mostrou 240, 33 e 89, 156, com alterações nas peças exibidas.
- O jogo atualiza o conteúdo do quadro gráfico conforme a câmera se move. Os 256 × 256 não representam necessariamente a sala inteira.
- As camadas sugerem composição de profundidade; a relação exata com sprites e colisão ainda não foi mapeada.

### Caminho de dados confirmado para um trecho do BG3

```text
0200B440 — base de origem da camada na RAM
    └─ 0200B480 — trecho observado, valor 41BB
           ↓ cópia de entradas de 2 bytes
0202C460 — área intermediária do BG3 na RAM
           ↓ cópia para VRAM
0600F800 — mapa gráfico do BG3 na memória de vídeo
```

- Os primeiros 32 bytes de `0202C460` e `0600F800` coincidiram exatamente no teste.
- Um watchpoint mostrou `0202C460` passando de `72CC` para `41BB`.
- A leitura veio de `0200B480`; depois da leitura, `r12` avançou para `0200B482`.
- `0200B480` não mudou ao percorrer a sala, mas foi lido. Isso é compatível com dados de origem estáveis; não prova que essa região seja toda a sala ou que nunca seja regravada.
- `41BB`, `72CC` etc. são valores observados nas entradas gráficas; não foram identificados como IDs de sala.

### Estruturas das camadas

A função em `08009130` calcula a estrutura como:

```text
03003290 + índice × 24 bytes
```

| Camada/índice | Estrutura | Campo +12: ponteiro de origem |
|---|---|---|
| BG0 / 0 | `03003290` | `0300329C` |
| BG1 / 1 | `030032A8` | `030032B4` |
| BG2 / 2 | `030032C0` | `030032CC` |
| BG3 / 3 | `030032D8` | `030032E4` |

Campos identificados ou candidatos:

| Offset | Tamanho lido | Significado | Evidência |
|---|---|---|---|
| +8 | 2 bytes | Deslocamento/coordenada usada no cálculo | Uso observado; semântica exata pendente |
| +10 | 2 bytes | Segundo deslocamento/coordenada | Uso observado; semântica exata pendente |
| +12 | 4 bytes | Ponteiro para origem dos dados gráficos | Confirmado pelo código e leitura |
| +16 | 2 bytes | Passo entre linhas, em entradas/tiles | Confirmado no cálculo de origem |
| +18 | 2 bytes | Provável altura em tiles | Hipótese; falta observar uso |
| +20 | 2 bytes | Índice na tabela de destinos | Confirmado |
| +22 | 2 bytes | Controle de uso das coordenadas | Testado contra zero no código; função exata pendente |

Valores lidos do BG3:

```text
r/4 $030032E4 → 0200B440
r/2 $030032E8 → 003C = 60
r/2 $030032EA → 0028 = 40
r/2 $030032EC → 0003
```

A rotina trabalha com unidades de 8 pixels. A largura gráfica é de 60 tiles = 480 pixels. A hipótese de altura é 40 tiles = 320 pixels. Ainda não confirmar “arena 480 × 320” sem validar o uso da altura e a extensão real dos dados; a área caminhável é outra informação.

Tabela de destinos em `03003580`:

```text
Índice 0: 00000000
Índice 1: 0202B440
Índice 2: 0202BC50
Índice 3: 0202C460
```

A entrada zero nesta tabela não significa ausência de BG0: a interface foi observada no visualizador e pode seguir outro caminho de atualização.

### Rotinas importantes

| Endereço | Observação |
|---|---|
| `08009130` | Seleciona estrutura de 24 bytes a partir de `03003290` |
| `080093C0` | Chama `08009068` no caminho capturado |
| `08009068` | Seleciona origem e destino; calcula trecho de linha com coordenadas em tiles |
| `08009084` | Carrega ponteiro de origem de `[r6 + 12]` |
| `080090CC` | Lê passo/largura de `[r6 + 16]` |
| `08009116` | Chama a função de cópia `080B7FE8` |
| `080B7FE8` | Executa `swi #11`; depois retorna com `bx lr` |
| `00000294` | Rotina de cópia: lê halfword e avança origem em 2 bytes |
| `00000298` | Escreve halfword e avança destino em 2 bytes |

O cálculo usa coordenadas divididas por 8, máscara de 255 pixels e divisão da linha em partes que completam 32 posições. Isso sustenta a interpretação de um quadro gráfico reutilizado durante a rolagem.

## Procedimentos no debugger

- Executar cada comando separadamente; colar `w/…` e `c` juntos produziu erros de interpretação.
- `w/1`: escreve 1 byte; `w/2`: escreve 2 bytes. Escolher tamanho pela evidência, não apenas pelo resultado da busca.
- `r/2`, `r/4`: leitura de um valor.
- `x/1`, `x/2`, `x/4`: leitura de várias unidades; o último argumento é a quantidade de unidades, não de bytes.
- `watch/w`: pausa em escrita; `watch/c`: pausa em mudança; `watch/r`: pausa em leitura.
- `delete N`: remove o watchpoint/breakpoint de número N. Os números variam ao criar novos.
- `disassemble/t`: usar explicitamente para os trechos Thumb do jogo; as rotinas de cópia capturadas em endereços baixos estavam em ARM.
- Uma pausa de watchpoint não significa travamento do jogo.
- Não transformar as hipóteses em cheats permanentes antes de confirmar campo, efeito e persistência.

Último estado conhecido: watchpoint #5 em mudança de `0200B480` e #6 em leitura de `0200B480`; #6 foi o último a disparar. Confirmar a lista com `listw` antes de remover ou adicionar outros.

## Leitura das quatro estruturas — resultado

```text
x/4 $03003290 24
```

Leitura recebida:

```text
03003290: 00000000 00000000 00000000 00000000
030032A0: 00000000 00000000 000F0007 00000000
030032B0: 00000000 0200D9C0 0028003C 00010001
030032C0: 000F0007 00000000 00000000 0200C700
030032D0: 0028003C 00010002 000F0007 00000000
030032E0: 00000000 0200B440 0028003C 00010003
```

Decodificação em little-endian, respeitando estruturas de 24 bytes (não as linhas de 16 bytes do dump):

| Camada | Origem confirmada | +16: largura | +18: altura candidata | +20: índice | +22: controle |
|---|---|---:|---:|---:|---:|
| BG0 | `00000000` | 0 | 0 | 0 | 0 |
| BG1 | `0200D9C0` | 60 | 40 | 1 | 1 |
| BG2 | `0200C700` | 60 | 40 | 2 | 1 |
| BG3 | `0200B440` | 60 | 40 | 3 | 1 |

BG1–BG3 também têm +0 = 7, +2 = 15 e +4 a +10 zerados. Os significados de +0 e +2 continuam desconhecidos; não interpretar como coordenadas sem evidência.

As diferenças `0200C700 - 0200B440` e `0200D9C0 - 0200C700` são ambas `0x12C0` = 4800 bytes, exatamente `60 × 40 × 2`. Isso reforça fortemente a hipótese de três mapas de 60 × 40 entradas de 2 bytes (480 × 320 pixels). O limite final do BG1 e o uso de +18 como altura ainda precisam ser confirmados; a área caminhável não foi identificada.

Faixas previstas, com limite final exclusivo:

- BG3: `[0200B440, 0200C700)`.
- BG2: `[0200C700, 0200D9C0)`.
- BG1: `[0200D9C0, 0200EC80)` — final calculado, não verificado.

BG0 está zerado nesta tabela, embora a interface exista em VRAM; não concluir que a interface esteja desativada.

### Continuação em 0800918C — campos de controle

Leitura realizada. O trecho ainda não mostrou o uso de +18 como altura.

- `0800918C–08009192`: se o ponteiro de origem `[r6 + 12]` for zero, desvia para `080094AC`.
- `r4` mantém a base `03003290` nesse trecho. Em `08009194–080091AA`, lê um campo de 2 bytes em `0300331C` (base + `0x8C`) e compara com 5, 8 e 10.
- Para alguns desses casos, lê outro campo de 2 bytes em `03003320` (base + `0x90`). No caso 5, compara indiretamente com 13; no caso 8, trata especialmente a camada 3 e usa valores de 2 a 14 para selecionar um destino numa tabela.
- Esses campos controlam comportamentos específicos de atualização gráfica. São candidatos para investigação de contexto de fase/sala/efeito, mas sua semântica ainda é desconhecida. Não são IDs de sala confirmados.
- `080091DC` contém o literal `080091E0`; `080091E0–08009213` é a tabela de 13 endereços indicada pelo código. O disassembler apresentou os dados como falsas instruções. Retomar a leitura de código em `08009214`.
- Novas capturas mostram BG1 e BG3 com Offset 56, 124, mantendo map bases e tile base; sustentam a rolagem conjunta já observada.

Leituras recebidas: `0300331C = 1` e `03003320 = 7`. A combinação identifica o contexto observado, mas ainda não comprova IDs de fase/sala. Como o primeiro campo é 1, o fluxo segue o caso padrão em `0800925E`, não os tratamentos especiais de 5, 8 ou 10.

### Continuação em 08009214 — deslocamento em tiles

- No caminho padrão, `0800926E–08009280` converte a primeira coordenada em unidades de 8 pixels e subtrai o halfword em `[r6 + 0]`.
- `08009286–08009292` inicia o cálculo equivalente para a segunda coordenada.
- No caso especial de controle 10, `08009236–08009254` subtrai `[r6 + 2]` da segunda coordenada em tiles e pode reescrever esse campo.
- +0 e +2, antes sem interpretação, passam a ser candidatos a coordenadas de referência da atualização em tiles; ainda falta confirmar a atualização normal no final da função. Não são dimensões do mapa.
- O trecho não acessa +18: a interpretação de 40 como altura continua apoiada pelo layout e pelos intervalos entre blocos, não confirmada por esse código.

Próxima leitura focada: `disassemble/t $0800946A 40`, para examinar a parte final da função e verificar como atualiza as referências e o deslocamento gráfico.

## Ainda não localizado

- ID da sala e rotina que a carrega.
- Dados originais da arena na ROM e eventual compressão.
- Altura confirmada, colisão, área caminhável, saídas e eventos do boss.
- Estruturas de itens, inventário, equipamentos e recompensas.
- Persistência dos endereços entre personagens, classes, carregamentos e reinicializações.

## Comparação entre áreas — campos candidatos de identificação

| Local informado | `0300331C` (2 bytes) | `03003320` (2 bytes) |
|---|---:|---:|
| Arena do boss estudada | 1 | 7 |
| Entrada da fase, após teste de transição | 1 | 0 |
| Área seguinte à entrada | Não relido | 1 |
| Sala seguinte, após a sala 1 | Não relido | 2 |

A entrada foi testada após orientar a visita à fase dos goblins; o usuário informou apenas “entrada da fase”, sem repetir o nome. Confirmar o nome antes de catalogar formalmente. O usuário esclareceu que avançou salas, não fases.

Teste de escrita: o usuário tentou mudar `03003320` para 7 e não houve a troca desejada para a arena. Não foi fornecida leitura imediatamente após a escrita; não sabemos se o valor persistiu ou foi sobrescrito. Ao passar normalmente para a próxima sala, o campo mostrou 2. A sequência natural 0 → 1 → 2, junto de 7 na arena, sustenta que o campo acompanha o índice da sala atual. Escrever nele isoladamente não demonstrou acionar o carregamento de outra sala. Próximo alvo: observar uma escrita natural nesse campo durante uma transição.

Entre arena e entrada, o primeiro campo permaneceu em 1 e o segundo passou de 7 para 0. Ao avançar uma área a partir da entrada, o usuário leu `03003320 = 1`; `0300331C` ainda não foi relido nessa área. A sequência observada 0 → 1 reforça segundo campo = sala/segmento. Falta verificar se o primeiro continua em 1 e comparar com castelo e outra fase. Não presumir que todos os números sejam sequenciais nem que esses campos possam ser escritos para teletransportar.

### Transição natural da sala 2 para 3

Watchpoint #7 em mudança de `03003320` disparou com valor antigo 2 e novo 3. Isso confirma que o campo é atualizado no percurso normal entre salas; sequência observada 0 → 1 → 2 → 3, com 7 na arena.

```text
r0: 03003320  r1: 00000000  r2: 08546564  r3: 00000018
r4: 00000003  r5: 03003290  r6: 03003550  r7: 00000001
r8: 00000001  r9: 0854654C  r10: 00000000 r11: 00000000
r12: 0000271A r13: 0202FB58 r14: 080094F5 r15: 08009524
cpsr: 0000003F [------T]
Cycle: 61701775236
```

O código está em modo Thumb, próximo de `08009524`; confirmar a instrução exata da escrita com disassembly. `r4 = 3` coincide com o novo índice; `r5` aponta para a base já conhecida das estruturas. `0854654C` e `08546564` são endereços na região de ROM e diferem em `0x18`, mas não há evidência suficiente para nomeá-los como tabela de salas ou descritores. Próxima leitura: `disassemble/t $080094C0 64`. Manter a parada até capturar o trecho.

### Função de preparação da transição — 080094CC

Confirmado pelo disassembly fornecido:

- Entrada Thumb em `080094CC`; salva argumento `r0` em `r7` e argumento `r1` em `r4`.
- `0800951C` grava o primeiro argumento, via `r7`, em `0300331C`.
- `08009520` grava o segundo argumento, via `r4`, em `03003320`. Essa é a escrita que disparou o watchpoint na transição 2 → 3.
- No teste, argumentos preservados: primeiro = 1; segundo = 3. A interpretação do segundo como índice da sala é fortemente sustentada; primeiro como fase/contexto ainda depende de comparação entre fases.
- Antes das escritas, testa o bit 0 em `0300332C` (+0x9C da base) e o retorno de uma chamada a `08000470` com `03003550` como argumento. Alguns caminhos retornam zero sem executar a preparação. Significado dos controles ainda desconhecido.
- Prepara campos na estrutura `03003550`: +12 recebe `0800A535`, +16 recebe `0300354C`, +8 recebe 80 decimal, +32 e +36 recebem zero no caminho observado. O endereço ímpar `0800A535` é compatível com ponteiro para função Thumb em `0800A534`; o uso como callback ainda precisa ser confirmado.
- Portanto, a função faz mais que escrever os índices: alterar somente `03003320` não reproduz a preparação observada. Ainda não foi demonstrado que chamar esta função isoladamente basta para trocar de sala com segurança.
- Para o primeiro argumento = 1, `08009522–08009526` desvia para `0800962C`, evitando o caso especial de valor 5.
- `080094C0–080094CB` e os literais em `08009500–08009507` são dados exibidos como instruções, não sequência executável normal.
- Os valores `0854654C` e `08546564` nos registradores da parada anterior ainda não foram usados no trecho mostrado; podem ser valores residuais. Não catalogá-los como descritores sem observar seu uso.

Próxima leitura no caminho efetivamente usado: `disassemble/t $0800962C 96`. Objetivo: acompanhar a seleção/preparação de dados para os argumentos 1 e 3, até o final próximo de `08009708`.

### Tabela de seleção de salas na ROM — 0800962C

O código calcula o endereço da entrada como:

```text
entrada = 0848553C + contexto * 0x74 + 0x10 + sala * 4
```

Aqui `contexto` é o primeiro argumento preservado em r7 (candidato a fase) e `sala` o segundo, preservado em r4. O passo de 0x74 por contexto não comprova sozinho quantas salas existem: pode haver cabeçalho e outros campos.

Para contexto 1:

- Sala 0: entrada em `084855C0`.
- Sala 3: entrada em `084855CC`.
- Arena, sala 7: entrada em `084855DC`.

Esses são endereços de entradas, não os endereços finais dos mapas. `0800963A` lê a entrada e `0800963C` chama `08006E34` para interpretá-la. O retorno é guardado em `03003340` (base +0xB0). Depois chama `08008CDC` com esse resultado e o contexto.

A entrada original tem o bit `0x40000000` testado. Dependendo dele, o código usa o retorno +0x10 diretamente ou chama `08000BC8` com retorno +0x10 e `030032F4` como argumentos. Formato da entrada, significado do bit e função de `08000BC8` ainda não confirmados; não assumir ponteiro direto nem compressão.

O resultado desse segundo caminho é guardado em `030032F0` (base +0x60). A estrutura apontada tem dois campos iniciais de 2 bytes, usados no cálculo:

```text
ponteiro seguinte = estrutura + 0x10 + campo0 * campo2 * 6
```

Isso é compatível com cabeçalho de 16 bytes e três camadas de 2 bytes por tile, dadas as evidências anteriores. O código guarda o ponteiro seguinte em +0x68 ou +0x6C conforme o resultado de `0800C6B0`; não identifica sozinho o conteúdo seguinte como colisão. No caminho de retorno zero dessa função, copia os dois campos para `03003308` e `0300330A`.

A rotina também copia esses campos para outros controles e zera estado de atualização. Portanto, escrever só o índice da sala não executa esse carregamento.

Importante: a última parada foi na escrita do índice em `08009520`, ANTES dessas operações. Enquanto permanecer nessa parada, os ponteiros e dimensões globais podem ainda corresponder à sala anterior. Não rotulá-los automaticamente como dados da sala 3.

Próximas leituras estáticas: `x/4 $084855C0 8` e `disassemble/t $08006E34 24`, para examinar as entradas 0–7 e a função que interpreta seus valores.

### Entradas de salas e resolução de recurso

Leitura das oito entradas do contexto 1:

| Sala | Endereço da entrada | Valor/código de recurso |
|---|---|---|
| 0 | `084855C0` | `00020006` |
| 1 | `084855C4` | `00020007` |
| 2 | `084855C8` | `00020008` |
| 3 | `084855CC` | `00020009` |
| 4 | `084855D0` | `0002000A` |
| 5 | `084855D4` | `0002000B` |
| 6 | `084855D8` | `0002000C` |
| 7 — arena | `084855DC` | `0002000D` |

Os valores não são ponteiros diretos para a ROM. `08006E34` preserva o argumento em r0, coloca `0856F954` em r1 e chama `08006A5C`; retorna seu resultado. Assim, `08006A5C` recebe o código e uma base para resolvê-lo. O significado da parte alta `0002` e da parte baixa ainda não foi demonstrado; hipótese de grupo/índice não confirmada.

A função `08006E34` termina em `08006E3E`; `08006E40` é o literal e `08006E44` inicia outra função. Não usar a rotina posterior como continuação do resolvedor.

Próxima leitura: `disassemble/t $08006A5C 64`. Objetivo: obter a fórmula de resolução e então ler somente as entradas de tabela necessárias para o recurso da arena `0002000D`.

## Atualizações futuras

Para cada descoberta, registrar data, endereço, tamanho, valor anterior/depois, comando, efeito observado e condição de teste. Manter hipóteses separadas das confirmações e anotar dependência da sala/personagem.
