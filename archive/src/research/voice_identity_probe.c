// Persistent single-threaded Wine worker. Protocol: five u32 lengths followed
// by UTF-8 strings (text, key, voice package, voice license, output WAV).
// Replies are i32 status + u32 PCM bytes; readiness reply has bytes=0.
#include "engine_api.h"
#include <io.h>
#include <fcntl.h>

typedef int (__cdecl *unload_fn)(void *);

static void reply(int status, uint32_t bytes) {
    int32_t code = status;
    fwrite(&code, 4, 1, stdout);
    fwrite(&bytes, 4, 1, stdout);
    fflush(stdout);
}

int main(int argc, char **argv) {
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc != 4) return 2;
    const char *product = getenv("AITALK_PRODUCT_NAME");
    const char *code = getenv("AITALK_LICENSE_CODE");
    if (!product || !*product || !code || !*code) return 2;
    HMODULE engine = LoadLibraryExA(argv[1], NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!engine) { fprintf(stderr, "LoadLibraryEx: %lu\n", GetLastError()); return 3; }
#define RESOLVE(type, var, name) \
    type var = (type)(void *)GetProcAddress(engine, name); \
    if (!var) { fprintf(stderr, "Missing export: %s\n", name); FreeLibrary(engine); return 3; }
    RESOLVE(initialize_fn, initialize, "ai_ttsLibraryInitialize");
    RESOLVE(authenticate_fn, authenticate, "ai_ttsLibraryAuthenticate");
    RESOLVE(new_fn, talker_new, "ai_Talker_new");
    RESOLVE(delete_fn, talker_delete, "ai_Talker_delete");
    RESOLVE(terminate_fn, terminate, "ai_ttsLibraryTerminate");
    RESOLVE(load_lang_fn, load_lang, "ai_Talker_loadLangDic");
    RESOLVE(load_voice_fn, load_voice, "ai_Talker_loadVoiceDic");
    RESOLVE(select_fn, select_lang, "ai_Talker_selectLangDic");
    RESOLVE(select_fn, select_voice, "ai_Talker_selectVoiceDic");
    RESOLVE(unload_fn, unload_voice, "ai_Talker_unloadAllVoiceDic");
    RESOLVE(talk_fn, talk, "ai_Talker_talk");
    RESOLVE(get_fs_fn, get_fs, "ai_Talker_getVoiceFs");
    RESOLVE(sink_new_fn, sink_new, "ai_TtsCallbackSink_new");
    RESOLVE(delete_fn, sink_delete, "ai_TtsCallbackSink_delete");
    RESOLVE(set_sink_fn, set_sink, "ai_Talker_setSink");
#undef RESOLVE
    int status = initialize(NULL);
    if (status == 0) status = authenticate(argv[2], code, product);
    void *talker = status == 0 ? talker_new() : NULL;
    if (!talker && status == 0) status = -1001;
    if (status == 0) status = load_lang(talker, "standard", argv[3], 1);
    if (status == 0) status = select_lang(talker, "standard");
    reply(status, 0);
    if (status != 0) {
        if (talker) talker_delete(talker);
        terminate(); FreeLibrary(engine); return 4;
    }
    typedef const char *(__cdecl *string_fn)(void *);
    typedef int (__cdecl *preset_fn)(void *,const char *,char *,size_t);
    typedef int (__cdecl *color_fn)(void *,const char *);
    typedef void *(__cdecl *config_fn)(void *);
    string_fn get_name=(string_fn)(void*)GetProcAddress(engine,"ai_Talker_getVoiceName");
    string_fn get_key=(string_fn)(void*)GetProcAddress(engine,"ai_Talker_getSelectedVoiceDic");
    preset_fn get_preset=(preset_fn)(void*)GetProcAddress(engine,"ai_Talker_getStylePreset");
    config_fn get_config=(config_fn)(void*)GetProcAddress(engine,"ai_Talker_getDefaultConfig");
    color_fn set_color=(color_fn)(void*)GetProcAddress(engine,"ai_TalkerConfig_setStyleColor");
    char selected_package[8193] = {0};
    uint32_t lengths[5];
    while (fread(lengths, sizeof(lengths), 1, stdin) == 1) {
        char *fields[5] = {0};
        int valid = 1;
        for (unsigned i = 0; i < 5; i++) {
            if (!lengths[i] || lengths[i] > 32768) { valid = 0; break; }
            fields[i] = malloc((size_t)lengths[i] + 1);
            if (!fields[i] || fread(fields[i], 1, lengths[i], stdin) != lengths[i]) { valid = 0; break; }
            fields[i][lengths[i]] = 0;
            if (strlen(fields[i]) != lengths[i]) { valid = 0; break; }
        }
        if (!valid) { for (unsigned i = 0; i < 5; i++) free(fields[i]); break; }
        status = 0;
        if (strlen(fields[2]) >= sizeof(selected_package)) status = -3;
        if (status == 0 && strcmp(selected_package, fields[2]) != 0) {
            if (selected_package[0]) status = unload_voice(talker);
            selected_package[0] = 0;
            if (status == 0) status = load_voice(talker, fields[1], fields[2], 1, fields[3]);
            if (status == 0) status = select_voice(talker, fields[1]);
            if (status == 0) strcpy(selected_package, fields[2]);
        }
        char preset[20000]={0};
        int plen=get_preset(talker,fields[1],preset,sizeof(preset));
        fprintf(stderr,"IDENTITY key=%s name=%s preset_size=%d preset=%s\n",get_key(talker),get_name(talker),plen,preset);
        if(getenv("TEST_STYLE")) fprintf(stderr,"set_color=%d style=%s\n",set_color(get_config(talker),getenv("TEST_STYLE")),getenv("TEST_STYLE"));
        audio_output *out = calloc(1, sizeof(*out));
        void *sink = NULL;
        int fs = status == 0 ? get_fs(talker) : 0;
        if (status == 0 && (!out || fs <= 0 || fs > 192000)) status = -1;
        if (status == 0) {
            out->file = fopen(fields[4], "wb+");
            if (!out->file || !wav_header(out->file, (unsigned)fs, 0)) status = -7;
        }
        if (status == 0) {
            sink = sink_new(on_event, out);
            status = sink ? set_sink(talker, sink) : -1;
        }
        // Encoding 0 is UTF-8; 1 is CP932. Passing UTF-8 with 1 reads mojibake.
        if (status == 0) status = talk(talker, fields[0], 0);
        if (sink) { set_sink(talker, NULL); sink_delete(sink); }
        uint32_t bytes = out ? out->bytes : 0;
        if (status == 0 && (!bytes || out->failed)) status = -12;
        if (out && out->file) {
            if (!wav_header(out->file, (unsigned)fs, bytes)) status = -7;
            if (fclose(out->file) != 0) status = -7;
        }
        free(out);
        if (status != 0) remove(fields[4]);
        for (unsigned i = 0; i < 5; i++) free(fields[i]);
        reply(status, bytes);
    }
    talker_delete(talker);
    terminate(); FreeLibrary(engine);
    return 0;
}
