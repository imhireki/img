import os

import pytest

from image import editor


@pytest.fixture(autouse=True)
def patch_tempfile(mocker):
    return mocker.patch('image.editor.get_named_temporary_file')


class TestStaticImageEditor:
    def test_actual_mode(self, mocker):
        image_mode = 'RGB'
        image_editor = editor.StaticImageEditor(mocker.Mock(mode=image_mode))

        assert image_editor.actual_mode == image_mode

    def test_result(self, mocker, patch_tempfile):
        image_editor = editor.StaticImageEditor(mocker.Mock())

        assert image_editor.result is patch_tempfile.return_value

    def test_result_deleter(self, mocker, patch_tempfile):
        image_editor = editor.StaticImageEditor(mocker.Mock())
        del image_editor.result
        assert patch_tempfile.call_count == 2

    def test_convert_mode(self, mocker):
        image_editor = editor.StaticImageEditor(mocker.Mock())
        image_editor.convert_mode('RGBA')

        assert (image_editor._original_image.convert.call_args.kwargs
                == {"mode": "RGBA"})

    def test_resize(self, mocker, editor_options):
        image_mock = mocker.Mock()

        image_editor = editor.StaticImageEditor(image_mock)
        image_editor.resize(**editor_options['resize_options'])

        assert (image_mock.resize.call_args.kwargs
                == editor_options['resize_options'])

    def test_save(self, mocker, editor_options):
        edited_image_mock = mocker.Mock()
        image_convert_mock = mocker.Mock(return_value=edited_image_mock)

        image_editor = editor.StaticImageEditor(
            mocker.Mock(convert=image_convert_mock))
        image_editor.save(**editor_options['save_options'])

        assert image_convert_mock.called
        assert (edited_image_mock.save.call_args.kwargs
                == editor_options['save_options'])


class TestAnimatedImageEditor:
    @pytest.mark.parametrize('mode, _info, extrema, _actual_mode', [
        ['P', {}, 0, 'RGB'],
        ['P', {'transparency': 1}, 0, 'RGBA'],
        ['RGBA', {}, [0, 0, 0, (255, 255)], 'RGB'],
        ['RGBA', {}, [0, 0, 0, (0, 255)], 'RGBA']
    ])
    def test_actual_mode(self, mocker, mode, _info, extrema, _actual_mode):
        image_editor = editor.AnimatedImageEditor(
            mocker.Mock(mode=mode, getextrema=lambda: extrema, info=_info)
            )

        assert image_editor.actual_mode == _actual_mode

    def test_result(self, mocker, patch_tempfile):
        mocker.patch('image.editor.AnimatedImageEditor._find_actual_mode')

        image_editor = editor.AnimatedImageEditor(mocker.Mock())

        assert image_editor.result is patch_tempfile.return_value

    def test_result_deleter(self, mocker, patch_tempfile):
        image_editor = editor.StaticImageEditor(mocker.Mock())
        del image_editor.result
        assert patch_tempfile.call_count == 2

    def test_convert_mode(self, mocker):
        new_mode = 'RGBA'
        image_mock_1 = mocker.Mock(mode='P')
        image_mock_2 = mocker.Mock(mode='RGB')
        mocker.patch('image.editor.AnimatedImageEditor._find_actual_mode',
                     lambda self: image_mock_2.mode)
        mocker.patch('image.editor.AnimatedImageEditor._get_frames',
                     lambda self: (_ for _ in [image_mock_1, image_mock_2]))

        image_editor = editor.AnimatedImageEditor(image_mock_1)
        image_editor.convert_mode(new_mode)
        [_ for _ in image_editor._edited_frames]

        assert image_mock_1.convert.call_args.kwargs == {"mode": new_mode}
        assert image_mock_2.copy.called

    def test_resize(self, mocker, editor_options):
        image_mock_1_converted = mocker.Mock()
        image_mock_1 = mocker.Mock(mode='P', convert=image_mock_1_converted)
        image_mock_2 = mocker.Mock(mode='RGB')
        mocker.patch('image.editor.AnimatedImageEditor._find_actual_mode',
                     lambda self: image_mock_2.mode)
        mocker.patch('image.editor.AnimatedImageEditor._get_frames',
                     lambda self: (_ for _ in [image_mock_1, image_mock_2]))

        image_editor = editor.AnimatedImageEditor(image_mock_1)
        image_editor.resize(**editor_options['resize_options'])
        [_ for _ in image_editor._edited_frames]

        assert image_mock_1.convert.call_args.args[0] == image_mock_2.mode
        assert (image_mock_1_converted.return_value.resize.call_args.kwargs
                == editor_options['resize_options'])
        assert (image_mock_2.resize.call_args.kwargs
                == editor_options['resize_options'])

    def test_save(self, mocker, editor_options):
        editor_options['save_options'].update({"save_all": True})
        image_mock_1, image_mock_2 = mocker.Mock(), mocker.Mock()
        mocker.patch('image.editor.AnimatedImageEditor._find_actual_mode',
                     lambda self: 'RGB')
        mocker.patch('image.editor.AnimatedImageEditor.convert_mode')

        image_editor = editor.AnimatedImageEditor(image_mock_1)
        image_editor._edited_frames = (_ for _ in [image_mock_1, image_mock_2])
        image_editor.save(**editor_options['save_options'])

        editor_options['save_options'].update({"append_images": [image_mock_2]})
        assert (image_mock_1.save.call_args.kwargs
                == editor_options['save_options'])


class TestBulkResizeSaveEditor:
    def test_actual_mode(self, mocker):
        _image_editor_mock = mocker.Mock(actual_mode='RGB')

        image_editor = editor.BulkResizeSaveEditor(
            (_ for _ in [_image_editor_mock]), {}, {})
        image_editor._current_image_editor = _image_editor_mock

        assert image_editor.actual_mode == _image_editor_mock.actual_mode

    def test_result(self, mocker):
        _image_editor = mocker.Mock()

        image_editor = editor.BulkResizeSaveEditor(
            (_ for _ in [_image_editor]), {}, {})
        image_editor._current_image_editor = _image_editor

        assert image_editor.result is _image_editor.result

    def test_convert_mode(self, mocker):
        image_editor = editor.BulkResizeSaveEditor(
            (_ for _ in [mocker.Mock()]), {}, {})

        assert not image_editor.convert_mode('RGB')

    def test_resize(self, mocker, editor_options):
        _image_editor = mocker.Mock()

        image_editor = editor.BulkResizeSaveEditor(
            (_ for _ in [_image_editor]), {}, {})
        image_editor._current_image_editor = _image_editor
        image_editor.resize(**editor_options['resize_options'])

        assert (_image_editor.resize.call_args.kwargs
                == editor_options['resize_options'])

    def test_save(self, mocker, editor_options):
        _image_editor = mocker.Mock()

        image_editor = editor.BulkResizeSaveEditor(
            (_ for _ in [_image_editor]), {}, {})
        image_editor._current_image_editor = _image_editor
        image_editor.save(**editor_options['save_options'])

        assert (_image_editor.save.call_args.kwargs
                == editor_options['save_options'])
