// Diagnostic only: exercise stock auth/API with optional missing license files.
#include "engine_api.h"
int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc != 8) return 2;
    HMODULE dll = LoadLibraryExA(argv[1], NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!dll) { printf("loader=%lu\n", GetLastError()); return 3; }
#define FN(type, var, name) type var = (type)(void *)GetProcAddress(dll, name)
    FN(initialize_fn, init, "ai_ttsLibraryInitialize");
    FN(authenticate_fn, auth, "ai_ttsLibraryAuthenticate");
    FN(new_fn, create, "ai_Talker_new");
    FN(delete_fn, destroy, "ai_Talker_delete");
    FN(terminate_fn, term, "ai_ttsLibraryTerminate");
    FN(load_lang_fn, lang, "ai_Talker_loadLangDic");
    FN(load_voice_fn, voice, "ai_Talker_loadVoiceDic");
    FN(select_fn, select_lang, "ai_Talker_selectLangDic");
    FN(select_fn, select_voice, "ai_Talker_selectVoiceDic");
    FN(talk_fn, talk, "ai_Talker_talk");
    FN(get_fs_fn, fs, "ai_Talker_getVoiceFs");
    FN(sink_new_fn, sink_new, "ai_TtsCallbackSink_new");
    FN(delete_fn, sink_delete, "ai_TtsCallbackSink_delete");
    FN(set_sink_fn, set_sink, "ai_Talker_setSink");
    int status = init(NULL);
    printf("initialize=%d\n", status);
    if (status) return 4;
    if (!strcmp(argv[2], "skip-auth")) {
        printf("authenticate=SKIPPED\n");
    } else {
        const char *lic = !strcmp(argv[2], "null-auth") ? NULL : argv[3];
        status = auth(lic, getenv("AITALK_LICENSE_CODE"), getenv("AITALK_PRODUCT_NAME"));
        printf("authenticate=%d\n", status);
    }
    void *obj = create();
    printf("talker=%p\n", obj);
    if (!obj) { term(); FreeLibrary(dll); return 5; }
    status = lang(obj, "standard", argv[4], 1);
    printf("loadLangDic=%d\n", status);
    if (!status) status = select_lang(obj, "standard");
    const char *vl = !strcmp(argv[5], "NULL") ? NULL : !strcmp(argv[5], "EMPTY") ? "" : argv[5];
    if (!status) status = voice(obj, "KotonohaAoi_ns_48", argv[6], 1, vl);
    printf("loadVoiceDic=%d\n", status);
    if (!status) status = select_voice(obj, "KotonohaAoi_ns_48");
    audio_output *out = calloc(1, sizeof(*out));
    void *sink = NULL;
    int rate = !status ? fs(obj) : 0;
    if (!status && out && rate > 0) {
        out->file = fopen(argv[7], "wb+");
        if (!out->file || !wav_header(out->file, rate, 0)) status = -7;
        if (!status) {
            sink = sink_new(on_event, out);
            status = sink ? set_sink(obj, sink) : -1;
        }
        if (!status) status = talk(obj, "です。", 0);
        printf("talk=%d pcmBytes=%u\n", status, out->bytes);
    }
    if (sink) { set_sink(obj, NULL); sink_delete(sink); }
    if (out && out->file) { wav_header(out->file, rate, out->bytes); fclose(out->file); }
    int ok = !status && out && out->bytes;
    free(out); destroy(obj); term(); FreeLibrary(dll);
    return ok ? 0 : 6;
}
