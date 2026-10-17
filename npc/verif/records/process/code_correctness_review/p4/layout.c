#include <am.h>
_Static_assert(sizeof(uintptr_t)==8,"RV64 word");
_Static_assert(sizeof(Context)==288,"frame");
_Static_assert(offsetof(Context,pdir)==0,"pdir/x0");
_Static_assert(offsetof(Context,gpr[2])==16,"sp");
_Static_assert(offsetof(Context,mcause)==256,"cause");
_Static_assert(offsetof(Context,mstatus)==264,"status");
_Static_assert(offsetof(Context,mepc)==272,"epc");
_Static_assert(offsetof(Context,np)==280,"np");
_Static_assert(sizeof(Context)%16==0,"alignment preservation");
const unsigned long layout[]={sizeof(Context),_Alignof(Context),offsetof(Context,gpr[2]),offsetof(Context,mcause),offsetof(Context,mstatus),offsetof(Context,mepc),offsetof(Context,np)};
