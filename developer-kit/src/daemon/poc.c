// PoC: load aitalk_engine.dll, init, auth, talker, paths, dic, talk -> WAV
// HISTORICAL, contains known incorrect signatures/auth/callback assumptions.
// Use run_auth_probe.py --synthesize and auth_probe.c for the verified flow.
// Build: x86_64-w64-mingw32-gcc -O2 poc.c -o poc.exe -L../../AIVoice2Editor -laitalk_engine -static-libgcc
// Run: WINEPREFIX=...> wine poc.exe
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

// Try to match real signatures. NOTE: setPathSet/setSink/pathAdd looked 1-arg
// in wrapper decompile, but core takes 2-arg. Assume C API is 2-arg (common).
// Dynamic trace will confirm.

typedef int (__cdecl *fn_libInit)(void*); // unknown, try void*
extern int __cdecl ai_ttsLibraryInitialize(void*);
extern int __cdecl ai_ttsLibraryAuthenticate(const char*, const char*, const char*);
extern int __cdecl ai_ttsLibraryTerminate(void);
extern void* __cdecl ai_Talker_new(void);
extern int __cdecl ai_Talker_delete(void*);
extern void* __cdecl ai_PathSet_new(void);
extern int __cdecl ai_PathSet_delete(void*);
extern int __cdecl ai_PathSet_add(void*, const char*, const char*);
extern int __cdecl ai_Talker_setPathSet(void*, void*);
extern int __cdecl ai_Talker_setSink(void*, void*);
extern int __cdecl ai_Talker_loadLangDic(void*);
extern int __cdecl ai_Talker_loadVoiceDic(void*, const char*, const char*, unsigned int, void*);
extern int __cdecl ai_Talker_talk(void*, const char*, unsigned int);
extern void* __cdecl ai_TtsCallbackSink_new(void*, void*);
extern int __cdecl ai_TtsCallbackSink_delete(void*);

// Callback sink: guess signature (buf,len) or (buf,len,format...) — log bytes
static FILE* g_wav = NULL;
static long g_total = 0;
static void CALLBACK on_data(const void* buf, unsigned int len, void* ctx) {
    if (!g_wav) return;
    fwrite(buf, 1, len, g_wav);
    g_total += len;
    printf("[cb] +%u bytes total=%ld\n", len, g_total);
}
static int CALLBACK on_data2(const void* buf, unsigned int len, unsigned int a3, void* ctx) {
    if (!g_wav) return 0;
    fwrite(buf, 1, len, g_wav);
    g_total += len;
    printf("[cb2] +%u bytes total=%ld a3=%u\n", len, g_total, a3);
    return 0;
}

int main(int argc, char** argv) {
    printf("poc start\n");

    const char* base = "C:\\Program Files\\AI\\AIVoice2\\AIVoice2Editor";
    // allow override via argv[1] = base dir
    if (argc > 1) base = argv[1];
    char licPath[1024], langDir[1024], voiceDir[1024], voicePath[1024];
    snprintf(licPath, sizeof(licPath), "%s\\Lib\\AITalk\\aitalk.lic", base);
    snprintf(langDir, sizeof(langDir), "%s\\Lang", base);
    snprintf(voiceDir, sizeof(voiceDir), "%s\\Voice", base);
    snprintf(voicePath, sizeof(voicePath), "%s\\Voice\\KotonohaAkane_ns_48\\KotonohaAkane_ns_48.aivdic", base);

    printf("lic=%s\nlang=%s\nvoice=%s\n", licPath, langDir, voicePath);

    int r;
    r = ai_ttsLibraryInitialize(NULL);
    printf("libInit=%d\n", r);

    // Common A.I.Voice SDK order: (licPath, "?", "?") — try empty strings first? we need real.
    // Try candidate: (licPath, "", "") ? Auth core expects 3 non-empty? First arg lic path
    r = ai_ttsLibraryAuthenticate(licPath, "", "");
    printf("auth1(lic,,)=%d\n", r);
    if (r != 0) {
        // fallback: (licPath, licPath, licPath) ? or (licPath, "AIVoice", "AIVoice")?
        // log and stop — need App.so caller
        printf("auth failed, need caller trace\n");
    }

    void* talker = ai_Talker_new();
    printf("talker=%p\n", talker);
    if (!talker) return 1;

    void* ps = ai_PathSet_new();
    printf("pathset=%p\n", ps);
    r = ai_PathSet_add(ps, "Lang", langDir);
    printf("pathAdd Lang=%d\n", r);
    r = ai_PathSet_add(ps, "Voice", voiceDir);
    printf("pathAdd Voice=%d\n", r);
    r = ai_Talker_setPathSet(talker, ps);
    printf("setPathSet=%d\n", r);
    r = ai_Talker_loadLangDic(talker);
    printf("loadLang=%d\n", r);
    r = ai_Talker_loadVoiceDic(talker, "KotonohaAkane_ns_48", voicePath, 1, NULL);
    printf("loadVoice(tar)=%d\n", r);
    if (r != 0) {
        r = ai_Talker_loadVoiceDic(talker, "KotonohaAkane_ns_48", voiceDir, 0, NULL);
        printf("loadVoice(dir)=%d\n", r);
    }

    g_wav = fopen("Z:\\home\\admin\\aivoice2-re\\cache\\poc.wav", "wb");
    printf("wav fopen=%p\n", (void*)g_wav);

    void* sink = ai_TtsCallbackSink_new((void*)on_data, NULL);
    printf("sink=%p\n", sink);
    r = ai_Talker_setSink(talker, sink);
    printf("setSink=%d\n", r);

    const char* text = "こんにちは、世界。";
    // encoding guess: try 0 first
    for (unsigned enc=0; enc<3; enc++) {
        printf("talk enc=%u ...\n", enc);
        r = ai_Talker_talk(talker, text, enc);
        printf("talk=%d total=%ld\n", r, g_total);
        if (g_total>0) break;
    }

    if (g_wav) fclose(g_wav);
    printf("done total=%ld\n", g_total);
    return 0;
}
