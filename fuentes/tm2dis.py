import struct,os,tempfile
RAMF=os.path.join(tempfile.gettempdir(),'tm2_ram_real.bin')
ram=open(RAMF,'rb').read()
NW=len(ram)//4
W=struct.unpack('<%dI'%NW,ram)
R=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def sx(i): return i-0x10000 if i&0x8000 else i
def w(a): return W[(a&0x7FFFFF)>>2]
def dis(a,x):
    op=x>>26; rs=(x>>21)&31; rt=(x>>16)&31; rd=(x>>11)&31; sh=(x>>6)&31; fn=x&63; imm=x&0xFFFF; s=sx(imm)
    if x==0: return 'nop'
    if op==0:
        t={0:'sll',2:'srl',3:'sra',4:'sllv',6:'srlv',7:'srav',8:'jr',9:'jalr',16:'mfhi',18:'mflo',24:'mult',25:'multu',26:'div',27:'divu',32:'add',33:'addu',34:'sub',35:'subu',36:'and',37:'or',38:'xor',39:'nor',42:'slt',43:'sltu',12:'syscall',13:'break'}.get(fn)
        if t in ('sll','srl','sra'): return '%s %s,%s,%d'%(t,R[rd],R[rt],sh)
        if t in ('sllv','srlv','srav'): return '%s %s,%s,%s'%(t,R[rd],R[rt],R[rs])
        if t=='jr': return 'jr %s'%R[rs]
        if t=='jalr': return 'jalr %s'%R[rs]
        if t in ('mfhi','mflo'): return '%s %s'%(t,R[rd])
        if t in ('mult','multu','div','divu'): return '%s %s,%s'%(t,R[rs],R[rt])
        if t: return '%s %s,%s,%s'%(t,R[rd],R[rs],R[rt])
        return '.word %08X'%x
    if op==1: return '%s %s,%08X'%({0:'bltz',1:'bgez',16:'bltzal',17:'bgezal'}.get(rt,'regimm?'),R[rs],a+4+s*4)
    if op in (2,3): return '%s %08X'%('j' if op==2 else 'jal',(a&0xF0000000)|((x&0x3FFFFFF)<<2))
    if op in (4,5): return '%s %s,%s,%08X'%('beq' if op==4 else 'bne',R[rs],R[rt],a+4+s*4)
    if op in (6,7): return '%s %s,%08X'%('blez' if op==6 else 'bgtz',R[rs],a+4+s*4)
    if op in (8,9,10,11): return '%s %s,%s,%d'%({8:'addi',9:'addiu',10:'slti',11:'sltiu'}[op],R[rt],R[rs],s)
    if op in (12,13,14): return '%s %s,%s,0x%X'%({12:'andi',13:'ori',14:'xori'}[op],R[rt],R[rs],imm)
    if op==15: return 'lui %s,0x%X'%(R[rt],imm)
    m={32:'lb',33:'lh',34:'lwl',35:'lw',36:'lbu',37:'lhu',38:'lwr',40:'sb',41:'sh',42:'swl',43:'sw',46:'swr'}.get(op)
    if m: return '%s %s,%d(%s)'%(m,R[rt],s,R[rs])
    if op==16: return 'cop0 %08X'%x
    if op==18: return 'cop2 %08X'%x
    if op in (50,58): return '%s r%d,%d(%s)'%('lwc2' if op==50 else 'swc2',rt,s,R[rs])
    return '.word %08X'%x
def dump(a0,a1,mark=()):
    for a in range(a0,a1,4):
        x=w(a); print('%s%08X  %08X  %s'%('>>' if a in mark else '  ',a,x,dis(a,x)))
def fstart(a,lim=0x4000):
    b=a
    while a-b<lim:
        if (w(b)&0xFFFF8000)==0x27BD8000: return b
        b-=4
    return None
def fend(a,lim=0x4000):
    e=a
    while e-a<lim:
        if w(e)==0x03E00008: return e+8
        e+=4
    return a+lim
def refs(lo,hi,a0=0x80010000,a1=0x80800000):
    out=[]; reg={}
    for a in range(a0,a1,4):
        x=w(a); op=x>>26; rs=(x>>21)&31; rt=(x>>16)&31; imm=x&0xFFFF
        if op==0x0F: reg[rt]=(imm<<16,a); continue
        if rs in reg and 0<a-reg[rs][1]<=64:
            v=None
            if op==0x0D: v=reg[rs][0]|imm
            elif op==0x09 or op in (32,33,35,36,37,40,41,43): v=(reg[rs][0]+sx(imm))&0xFFFFFFFF
            if v is not None and lo<=v<hi: out.append((a,v,dis(a,x)))
    return out
