import pytest

from image import category


def test_static_image_category(mocker):
    supported_images = {"STATIC": {"JPEG_RGB": mocker.Mock()}}
    image_mock = mocker.Mock(format='JPEG', mode='RGB')

    image_category = category.StaticImageCategory(image_mock, supported_images)
    image_profile = image_category.get_image_profile()

    assert image_profile is supported_images['STATIC']['JPEG_RGB']

def test_animated_image_category(mocker):
    supported_images = {"ANIMATED": {"GIF_P": mocker.Mock()}}
    image_mock = mocker.Mock(format='GIF', mode='P')

    image_category = category.AnimatedImageCategory(image_mock, supported_images)
    image_profile = image_category.get_image_profile()

    assert image_profile is supported_images['ANIMATED']['GIF_P']


class TestImageCategoryProxy:
    @pytest.mark.parametrize('is_animated, format, support_patch', [
        [True, 'GIF', 'image.category.AnimatedImageCategory'],
        [False, 'JPEG', 'image.category.StaticImageCategory'],
        [False, 'GIF', 'image.category.AnimatedImageCategory']
    ])
    def test_get_image_category(self, mocker, is_animated,
                               format, support_patch):
        image_category_mock = mocker.patch(support_patch)

        proxy = category.ImageCategoryProxy(
            mocker.Mock(is_animated=is_animated, format=format), {})
        image_category = proxy.get_image_category()

        assert image_category is image_category_mock.return_value
        assert proxy._image_category is image_category_mock.return_value

    def test_get_image_profile(self, mocker):
        proxy = category.ImageCategoryProxy(mocker.Mock(), {})
        mocker.patch.object(proxy, 'get_image_category')
        proxy._image_category = mocker.Mock()

        image_profile = proxy.get_image_profile()

        assert image_profile is proxy._image_category.get_image_profile.return_value
        assert (proxy._image_profile
                is proxy._image_category.get_image_profile.return_value)

    @pytest.mark.parametrize('_image_profile', [1, 0])
    def test_is_supported(self, mocker, _image_profile):
        proxy = category.ImageCategoryProxy(mocker.Mock(), {})
        mocker.patch.object(proxy, 'get_image_profile')
        proxy._image_profile = _image_profile

        is_supported = proxy.is_supported()

        assert is_supported is (_image_profile is not None)
