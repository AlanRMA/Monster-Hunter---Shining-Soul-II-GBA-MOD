.syntax unified
.cpu arm7tdmi
.thumb
.section .text
.equ STATE, 0x0203ff00
.macro call address
    ldr r3, =\address + 1
    bl bx_r3
.endm
.global purchase, use_scroll, fresh, return_hub, resources, dialogue, gate, resume_hub
.thumb_func
gate:
    ldr r0, =STATE
    ldr r0, [r0, #4]
    subs r0, #1
    cmp r0, #3
    bls gate_allowed
    push {r4}
    call 0x080020f4
    movs r1, #172
    lsls r1, r1, #1
    muls r0, r1
    ldr r4, =0x03003e9c
    adds r4, r4, r0
    // 72 was still inside the door trigger and continually swallowed menus.
    ldr r1, =96 << 8
    str r1, [r4]
    str r1, [r4, #8]
    movs r0, #97
    call 0x08058588
    pop {r4}
    movs r0, #0
    ldr r3, =0x08088a73
    bx r3
gate_allowed:
    call 0x08015940
    movs r0, #3
    call 0x0801a7b8
    call 0x0800b544
    ldr r3, =0x080888e5
    bx r3
.ltorg
.thumb_func
purchase:
    ldr r0, =STATE
    ldr r1, [r0, #12]
    cmp r1, #1
    bne purchase_native
    ldr r1, =0x03001444
    ldrh r1, [r1]
    movs r2, #1
    tst r1, r2
    beq purchase_native
    ldr r1, =0x03006590
    ldr r1, [r1]
    ldr r2, [r1, #28]
    cmp r2, #22
    bne purchase_native
    ldr r2, [r1, #4]
    cmp r2, #3
    bhi purchase_native
    push {r4-r7}
    movs r4, r1
    lsls r2, r2, #4
    ldr r5, =260
    adds r5, r5, r4
    adds r5, r5, r2
    call 0x0805cf5c
    cmp r0, #0
    blt purchase_fail
    movs r6, r0
    movs r0, r5
    call 0x0805add4
    movs r7, r0
    call 0x0805b04c
    cmp r0, r7
    blo purchase_fail
    movs r0, r7
    call 0x0807bdbc
    movs r0, #0
    movs r1, r6
    movs r2, r5
    call 0x0807bc48
    movs r0, #95
    call 0x08058588
    b purchase_done
purchase_fail:
    movs r0, #97
    call 0x08058588
purchase_done:
    pop {r4-r7}
    ldr r3, =0x0807f8e9
    bx r3
purchase_native:
    ldr r3, =0x0807e45d
    bx r3
.ltorg

.thumb_func
use_scroll:
    cmp r0, #0
    beq use_native
    ldrh r2, [r0]
    cmp r2, #1
    bne use_native
    ldrh r2, [r0, #2]
    ldr r3, =0xff00
    subs r2, r2, r3
    cmp r2, #3
    bhi use_native
    ldr r3, =0x0300331c
    ldrh r3, [r3]
    cmp r3, #0
    bne use_deny
    ldr r3, =0x03003320
    ldrh r3, [r3]
    cmp r3, #1
    bne use_deny
    ldr r3, =STATE
    ldr r1, [r3, #4]
    cmp r1, #0
    bne use_deny
    adds r2, #1
    str r2, [r3, #4]
    movs r1, #2
    str r1, [r3, #16]
    movs r1, #0
    str r1, [r3, #20]
    movs r0, #1
    bx lr
use_deny:
    push {lr}
    movs r0, #97
    call 0x08058588
    movs r0, #0
    pop {r1}
    bx r1
use_native:
    push {r4-r7,lr}
    mov r7, r10
    mov r6, r9
    mov r5, r8
    ldr r3, =0x0805bcd1
    bx r3
.ltorg

.thumb_func
fresh:
    ldr r0, =STATE
    movs r1, #0
    str r1, [r0]
    str r1, [r0, #4]
    str r1, [r0, #8]
    str r1, [r0, #12]
    str r1, [r0, #16]
    str r1, [r0, #20]
    ldr r0, =0x03003600
    ldr r0, [r0]
    ldr r1, =348
    adds r0, r0, r1
    movs r2, #25
fresh_gold_loop:
    ldrh r1, [r0]
    cmp r1, #10
    bne fresh_gold_next
    ldr r1, =1000
    str r1, [r0, #4]
    b fresh_done
fresh_gold_next:
    adds r0, #16
    subs r2, #1
    bne fresh_gold_loop
fresh_done:
    ldr r3, =0x09000001
    bx r3
.ltorg

.thumb_func
resume_hub:
    // Loading a character must not restore the original castle infirmary or
    // inherit another character's temporary activated hunt. Inventory is native.
    ldr r0, =STATE
    movs r1, #0
    str r1, [r0]
    str r1, [r0, #4]
    str r1, [r0, #12]
    str r1, [r0, #16]
    str r1, [r0, #20]
    str r1, [r0, #24]
    movs r1, #2
    str r1, [r0, #8]
    movs r0, #0
    movs r1, #1
    movs r2, #1
    call 0x080230b8
    ldr r3, =0x080226c1
    bx r3
.ltorg

.thumb_func
return_hub:
    push {r4}
    ldr r4, =STATE
    ldr r3, [r4, #8]
    cmp r3, #1
    bne return_native
    cmp r0, #0
    bne return_native
    cmp r1, #4
    bne return_victory
    movs r3, #1
    str r3, [r4, #20]
    ldr r3, [r4, #16]
    cmp r3, #0
    beq return_expire
    subs r3, #1
    str r3, [r4, #16]
    cmp r3, #0
    bne return_ready
    b return_expire
return_victory:
    movs r3, #2
    str r3, [r4, #20]
return_expire:
    movs r3, #0
    str r3, [r4, #4]
    str r3, [r4, #16]
return_ready:
    // The boss tasks have native destructors for their child scripts, sprites
    // and temporary pools. Cancel them before the castle clears exit flags.
    push {r0-r2,lr}
    bl unload_arena
    pop {r0-r2}
    pop {r3}
    mov lr, r3
    movs r1, #1
    movs r3, #0
    str r3, [r4, #12]
    movs r3, #2
    str r3, [r4, #8]
return_native:
    pop {r4}
    push {r4,r5,lr}
    lsls r0, r0, #16
    lsrs r5, r0, #16
    lsls r1, r1, #16
    ldr r3, =0x08026b1d
    bx r3
.ltorg

.thumb_func
unload_arena:
    push {r4-r6,lr}
    ldr r4, =0x03004370
    movs r5, #5
unload_task:
    movs r0, r4
    call 0x08000470
    cmp r0, #0
    beq unload_next
    movs r0, r4
    call 0x080003a8
unload_next:
    adds r4, #40
    subs r5, #1
    bne unload_task
    ldr r0, =0x0300584c
    movs r1, #0
    str r1, [r0]
    // These references must not point to an entity from the departed room.
    ldr r0, =0x030003e8
    str r1, [r0]
    ldr r0, =0x030003f4
    str r1, [r0]
    ldr r0, =0x03000404
    str r1, [r0]
    ldr r0, =0x03000428
    str r1, [r0]
    pop {r4-r6,pc}
.ltorg

.thumb_func
resources:
    ldr r2, =0x0010ff00
    subs r2, r0, r2
    cmp r2, #3
    bhi resources_native
    lsls r2, r2, #9
    ldr r0, =0x09002400
    adds r0, r0, r2
    bx lr
resources_native:
    push {r4-r6,lr}
    movs r4, r0
    movs r3, r1
    lsls r0, r4, #4
    ldr r2, =0x08006a65
    bx r2
.ltorg

// Original dialogue creation stays intact. During arena presentation only,
// return an already-completed handle instead of opening a dialogue window.
.thumb_func
dialogue:
    push {r0-r3}
    ldr r0, =STATE
    ldr r0, [r0, #8]
    cmp r0, #1
    bne dialogue_native
    ldr r0, =0x03005e48
    ldr r0, [r0]
    cmp r0, #217
    bne dialogue_native
    pop {r0-r3}
    ldr r0, =STATE+64
    movs r1, #0
    str r1, [r0, #116]
    bx lr
dialogue_native:
    pop {r0-r3}
    push {r4-r7,lr}
    sub sp, #4
    ldr r7, [sp, #24]
    movs r1, #0
    ldr r3, =0x0805df09
    bx r3
.ltorg

.thumb_func
bx_r3:
    bx r3
