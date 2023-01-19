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
  .endarea

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
.close

.open "ProLogueData/repack/overlay/overlay_0011_dec.bin",0x020c1860
  ;Don't convert status screen to shift-jis
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
