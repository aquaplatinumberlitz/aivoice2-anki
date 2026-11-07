#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static char voice_key[256]="unknown";
static FARPROC target(const char *name) {
    HMODULE mod=GetModuleHandleA("aitalk_real.dll");
    if(!mod)mod=LoadLibraryA("aitalk_real.dll");
    return GetProcAddress(mod,name);
}
static FILE *logfile(void) { return fopen("Z:[WORKSPACE]\\notes\\evidence\\voice-identity\\gui-calls.txt","ab"); }
int ai_Talker_selectVoiceDic(void *obj,const char *key) {
    snprintf(voice_key,sizeof(voice_key),"%s",key);
    FILE *f=logfile();if(f){fprintf(f,"selectVoiceDic obj=%p key=%s\n",obj,key);fclose(f);}
    return ((int(*)(void*,const char*))(void*)target("ai_Talker_selectVoiceDic"))(obj,key);
}
int ai_Talker_compile(void *obj,void *ir,const char *text,unsigned encoding){
    FILE*f=logfile();if(f){fprintf(f,"compile encoding=%u text=%s\n",encoding,text);fclose(f);}
    return ((int(*)(void*,void*,const char*,unsigned))(void*)target("ai_Talker_compile"))(obj,ir,text,encoding);
}
int ai_Talker_talkByIrText(void *obj,void *ir){
    char buf[20000]={0};
    int n=((int(*)(void*,char*,size_t,int))(void*)target("ai_TtsIrObject_toAIKana"))(ir,buf,sizeof(buf),0);
    FILE*f=logfile();if(f){fprintf(f,"talkByIrText voice=%s kana_size=%d kana=%s\n",voice_key,n,buf);fclose(f);}
    return ((int(*)(void*,void*))(void*)target("ai_Talker_talkByIrText"))(obj,ir);
}
void *ai_TtsImKana_newFromJson(const char *json){
    FILE*f=logfile();if(f){fprintf(f,"ImKana JSON=%s\n",json);fclose(f);}
    return ((void*(*)(const char*))(void*)target("ai_TtsImKana_newFromJson"))(json);
}
typedef struct {unsigned type;void *data;} Event;
typedef struct {void *pcm;uint64_t size;void *markers;uint64_t count;} Buffer;
typedef int(*Handler)(void*,Event*);
typedef struct{Handler handler;void *context;} Capture;
static int capture(void *context,Event *ev){
    Capture*c=context;
    if(ev->type==4&&ev->data){Buffer*b=ev->data;char path[700];snprintf(path,sizeof(path),"Z:[WORKSPACE]\\notes\\evidence\\voice-identity\\gui-%s.pcm",voice_key);FILE*f=fopen(path,"ab");if(f){fwrite(b->pcm,1,(size_t)b->size,f);fclose(f);}}
    return c->handler(c->context,ev);
}
void *ai_TtsCallbackSink_new(Handler handler,void *context){
    Capture*c=malloc(sizeof(*c));if(!c)return NULL;c->handler=handler;c->context=context;
    return ((void*(*)(Handler,void*))(void*)target("ai_TtsCallbackSink_new"))(capture,c);
}
int ai_Talker_setStylePreset(void *obj,const char *key,const char *preset) {
    FILE *f=logfile();if(f){fprintf(f,"setStylePreset key=%s preset=%s\n",key,preset);fclose(f);}
    return ((int(*)(void*,const char*,const char*))(void*)target("ai_Talker_setStylePreset"))(obj,key,preset);
}
int ai_TalkerConfig_setStyleColor(void *obj,const char *color) {
    FILE *f=logfile();if(f){fprintf(f,"setStyleColor config=%p color=%s\n",obj,color);fclose(f);}
    return ((int(*)(void*,const char*))(void*)target("ai_TalkerConfig_setStyleColor"))(obj,color);
}
#define DOUBLE_SETTER(name) \
int name(void *obj,double value){FILE*f=logfile();if(f){fprintf(f,#name " config=%p value=%.9g\n",obj,value);fclose(f);}return ((int(*)(void*,double))(void*)target(#name))(obj,value);}
DOUBLE_SETTER(ai_TalkerConfig_setPitch)
DOUBLE_SETTER(ai_TalkerConfig_setRate)
DOUBLE_SETTER(ai_TalkerConfig_setMasterVolume)
int ai_Talker_setDefaultConfig(void *obj,void *config) {
    FILE *f=logfile();if(f){fprintf(f,"setDefaultConfig talker=%p config=%p\n",obj,config);fclose(f);}
    return ((int(*)(void*,void*))(void*)target("ai_Talker_setDefaultConfig"))(obj,config);
}
int ai_Talker_talk(void *obj,const char *text,unsigned encoding) {
    FILE *f=logfile();if(f){fprintf(f,"talk encoding=%u text=%s\n",encoding,text);fclose(f);}
    return ((int(*)(void*,const char*,unsigned))(void*)target("ai_Talker_talk"))(obj,text,encoding);
}

int ai_Talker_selectLangDic(void *obj,const char *key) {
 FILE*f=logfile();if(f){fprintf(f,"selectLangDic obj=%p key=%s\n",obj,key);fclose(f);}
 return ((int(*)(void*,const char*))(void*)target("ai_Talker_selectLangDic"))(obj,key);
}
