"""Bridge Anki's legacy in-memory Editor and backend-driven NewEditor."""
from types import SimpleNamespace

from aqt.operations.note import update_note


def note_id(editor):
    if hasattr(editor, 'nid'):
        return editor.nid
    note = getattr(editor, 'note', None)
    return note.id if note else None


def note_info(editor, on_done):
    if callable(getattr(editor, 'get_note_info', None)):
        editor.get_note_info(on_done)
        return

    def saved():
        note = getattr(editor, 'note', None)
        if note:
            on_done(SimpleNamespace(id=note.id, mid=note.mid, fields=note.fields[:]))

    editor.call_after_note_saved(saved)


def set_fields(editor, fields, names, on_done, on_error):
    if callable(getattr(editor, 'get_note_info', None)):
        import json
        editor.web.evalWithCallback(
            f'setFields({json.dumps(names)}, {json.dumps(fields)}); saveNow();',
            lambda _result: on_done())
        return
    note = editor.note
    if note is None:
        on_error(ValueError('Note đã đóng; mở lại hộp thoại.'))
        return
    note.fields = fields

    def saved(_changes=None):
        if editor.note is note and editor.web:
            editor.loadNote(focusTo=editor.last_field_index)
        on_done()

    if editor.addMode:
        # New notes live in memory until the user presses Add.
        saved()
    else:
        update_note(parent=editor.widget, note=note).success(saved).failure(
            on_error).run_in_background(initiator=editor)
