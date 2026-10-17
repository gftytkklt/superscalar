/* Probe-only transport shim; production AM driver unchanged. */
#include <stdint.h>
#define AUDIO_ADDR 0xa0000200u
#define AUDIO_SBUF_ADDR 0xa1200000u
uint32_t inl(uintptr_t);
void outl(uintptr_t,uint32_t);
void outb(uintptr_t,uint8_t);
