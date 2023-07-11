.nds

.open "ProLogueData/repack_CHILD/arm9_dec.bin",0x02000000
  .org 0x02168470
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
  .endarea

  ;Don't call this function at startup to give us some space for string overflows
  .org 0x02000ef4
  nop

  ;Hook the function that reads characters to handle ASCII
  .org 0x02011bf8
  ;orr r2,r2,r3,lsl 0x8
  b ASCII
  ASCII_RET:
  .org 0x02011c0c
  ;The function call above this actually returns the character width
  ;add r7,r7,0xc
  add r7,r7,r0
  ;Here we only increase the text pointer by 1 since the ASCII code only adds 1 for sjis
  ;add r6,r6,0x2
  add r6,r6,0x1

  ;Make some space by redirecting some strings
  .org 0x021683cc
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
  .skip 8
  .dw 0x02168440
.close
