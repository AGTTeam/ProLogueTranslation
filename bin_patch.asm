.nds

.open "ProLogueData/repack/arm9_dec.bin",0x02000000
  .org 0x0207cb08
  .area 0x180
  ;r3 = first byte
  ;r2 = second byte
  ;Check if the text is ASCII or sjis, if r3 is > 0x7f then it's sjis
  ASCII:
  cmp r3,0x7f
  movle r2,r3
  ble @@ret
  @@sjis:
  orr r2,r2,r3,lsl 0x8
  add r6,r6,0x1
  @@ret:
  b ASCII_RET
  .pool

  ;Convert string in r0 from sjis to ASCII
  SJIS_TO_ASCII:
  push {r1-r5}
  ldr r1,=SJIS_TO_ASCII_BUFFER
  ldr r2,[r1]
  cmp r2,0
  moveq r2,1
  movne r2,0
  str r2,[r1]
  addeq r1,r1,4
  addne r1,r1,4*4
  push {r1}
  ;Load the sjis character and set up the lookup
  @@loop:
  ldrh r2,[r0]
  cmp r2,0
  beq @@ret
  mov r4,0
  ldr r3,=SJIS_TO_ASCII_LOOKUP
  ;Search for the sjis character
  @@loopchar:
  ldrh r5,[r3]
  cmp r5,0
  beq @@notfound
  cmp r2,r5
  addne r4,r4,1
  addne r3,r3,2
  bne @@loopchar
  ;Write the ASCII character to the buffer and continue
  @@foundchar:
  ldr r3,=SJIS_TO_ASCII_RESULT
  ldrb r5,[r3,r4]
  strb r5,[r1]
  add r1,r1,1
  add r0,r0,2
  b @@loop
  ;Didn't find this character in the lookup, so we just copy it
  @@notfound:
  strb r2,[r1]
  lsr r2,r2,8
  strb r2,[r1,1]
  add r1,r1,2
  add r0,r0,2
  b @@loop
  ;Write a 0 byte to the buffer and return
  @@ret:
  mov r2,0
  strb r2,[r1]
  pop {r0}
  pop {r1-r5}
  bx lr
  .pool

  SJIS_TO_ASCII_BUFFER:
  .dw 0
  .dw 0
  .dw 0
  .dw 0
  .dw 0
  .dw 0
  .dw 0

  DEFAULT_INPUT:
  push {lr}
  push {r0}
  ;Call the normal initialization function we replaced
  bl 0x020ab6a0
  ;Call the function that gets called when clicking the change buttons with the correct parameter
  pop {r0}
  mov r1,1
  bl 0x020ab2ec
  pop {pc}

  PLAYING_INTRO:
  .dw 0

  NO_AUDIO_PAUSE:
  push {r0}
  ldr r0,=PLAYING_INTRO
  ldr r0,[r0]
  cmp r0,1
  moveq r4,0
  movne r4,1
  pop {r0}
  b NO_AUDIO_PAUSE_RET

  CHECK_SCRIPT_OPCODE:
  cmp r6,0xf0
  bne @@ret
  push {r0-r1}
  ldr r0,=PLAYING_INTRO
  ldr r1,[r0]
  cmp r1,0
  moveq r1,1
  movne r1,0
  str r1,[r0]
  pop {r0-r1}
  b CHECK_SCRIPT_OPCODE_CONTINUE
  @@ret:
  cmp r6,0x30
  b CHECK_SCRIPT_OPCODE_RET
  .pool
  .endarea

  .org 0x02075804
  .area 0x11b
  SJIS_TO_ASCII_LOOKUP:
  .sjisn "０１２３４５６７８９"
  .sjisn "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
  .sjisn "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
  .sjisn "　、。，．？！（）【】＝＜＞＄％＆"
  .dh 0
  SJIS_TO_ASCII_RESULT:
  .ascii "0123456789"
  .ascii "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  .ascii "abcdefghijklmnopqrstuvwxyz"
  .ascii " ,.,.?!()[]=<>$%&"
  .endarea

  .org 0x0207592c
  .area 0x73
  ;Manual translation for a couple DS Download Play strings
  .align
  DOWNLOAD_PLAY1:
  .ascii "L",0," ",0,"C",0,"o",0,"m",0,"m",0,"u",0,"n",0,"i",0,"c",0,"a",0,"t",0,"o",0,"r",0,0,0
  DOWNLOAD_PLAY2:
  .ascii "C",0,"h",0,"a",0,"t",0," ",0,"w",0,"i",0,"t",0,"h",0," ",0,"L",0," ",0,"o",0,"n",0," ",0,"y",0,"o",0,"u",0,"r",0," ",0,"D",0,"S",0,".",0,0xa,0,"(",0,"T",0,"r",0,"i",0,"a",0,"l",0," ",0,"V",0,"e",0,"r",0,"s",0,"i",0,"o",0,"n",0,")",0,0,0
  .endarea

  ;Hook the name return function calls
  .org 0x02010450
  b SJIS_TO_ASCII
  .org 0x02010418
  b SJIS_TO_ASCII

  ;Swap <name> (first -> family)
  .org 0x0202f3f4
  ;.dw 0x0202e6c4
  .dw 0x0202e648
  ;Swap <name> (family -> first)
  .org 0x0202f3e4
  ;.dw 0x0202e648
  .dw 0x0202e6c4

  ;Don't call this function at startup to give us some space for string overflows
  .org 0x02000ec4
  nop

  ;Make some space by redirecting some strings
  .org 0x0207ca64
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8
  .skip 8
  .dw 0x0207cad8

  ;Make some more space
  .org 0x02023c8c
  .dw 0x020757f8
  .org 0x02023d44
  .dw 0x020757f8
  .org 0x02023dd0
  .dw 0x020757f8
  .org 0x02023e18
  .dw 0x020757f8
  .org 0x02024910
  .dw 0x020757f8
  .org 0x02023e5c
  .dw 0x020757f8
  .org 0x02023f00
  .dw 0x020757f8
  .org 0x02023f04
  .dw 0x020757f8
  .org 0x02024338
  .dw 0x020757f8
  .org 0x02024474
  .dw 0x020757f8
  .org 0x0202498c
  .dw 0x020757f8
  .org 0x020247e4
  .dw 0x020757f8
  .org 0x02024914
  .dw 0x020757f8
  .org 0x02024cbc
  .dw 0x020757f8
  .org 0x02024f34
  .dw 0x020757f8
  .org 0x02024f38
  .dw 0x020757f8
.close

.open "ProLogueData/repack/overlay/overlay_0000_dec.bin",0x020aa840
  .org 0x020acbc8
  ;mov r4,1
  b NO_AUDIO_PAUSE
  NO_AUDIO_PAUSE_RET:

  .org 0x020aec94
  CHECK_SCRIPT_OPCODE_CONTINUE:

  .org 0x020aecc0
  b CHECK_SCRIPT_OPCODE
  CHECK_SCRIPT_OPCODE_RET:

  ;Swap @n0
  .org 0x020b1fe8
  ;bl 0x02010444
  bl 0x0201040c
  .org 0x020b1ff0
  ;bl 0x0201040c
  bl 0x02010444
  .org 0x020b2000
  ;bl 0x02010444
  bl 0x0201040c
  .org 0x020b1ff8
  ;bl 0x0201040c
  bl 0x02010444
.close

.open "ProLogueData/repack/overlay/overlay_0026_dec.bin",0x020c1860
  ;Hook the function that reads characters to handle ASCII
  .org 0x020c45ec
  ;orr r2,r2,r3,lsl 0x8
  b ASCII
  ASCII_RET:

  ;The function call above this actually returns the character width
  .org 0x020c4600
  ;add r7,r7,0xc
  add r7,r7,r0
  ;Here we only increase the text pointer by 1 since the ASCII code only adds 1 for sjis
  ;add r6,r6,0x2
  add r6,r6,0x1

  ;Align wallpaper text left
  .org 0x020c71b4
  mov r1,0x20
  .org 0x020c71e8
  mov r1,0x20

  ;Swap abcd name (first -> family)
  .org 0x020c3414
  ;bl 0x020c1ae4
  bl 0x020c1ad4
  .org 0x020c3448
  ;bl 0x020c1ae4
  bl 0x020c1ad4
  ;Swap abcd name (family -> first)
  .org 0x020c33f8
  ;bl 0x020c1ad4
  bl 0x020c1ae4
.close

.open "ProLogueData/repack/overlay/overlay_0011_dec.bin",0x020c1860
  ;Don't convert status screen to sjis
  .org 0x020c2b5c
  nop
  nop
  mov r3,sp
  .org 0x020c2b90
  nop
  nop
  mov r3,sp
  .org 0x020c2c54
  nop
  nop
  mov r3,sp
.close

.open "ProLogueData/repack/overlay/overlay_0014_dec.bin",0x020c1860
  .org 0x020c2e34
  .dw DOWNLOAD_PLAY1
  .dw DOWNLOAD_PLAY2
.close

.open "ProLogueData/repack/overlay/overlay_0029_dec.bin",0x020aa840
  ;Change default input to English characters
  .org 0x020acf80
  .dw DEFAULT_INPUT
.close
