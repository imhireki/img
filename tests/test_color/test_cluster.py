from color import cluster


def test_color_cluster(mocker):
    expected_sorted_colors = [(255, 255, 255), (0, 0, 0)]
    vertically_aligned_rgb = [
        (255, 255, 255, 0, 0),  # Red
        (255, 255, 255, 0, 0),  # Green
        (255, 255, 255, 0, 0),  # Blue
    ]
    image = mocker.Mock(getdata=lambda band: vertically_aligned_rgb[band])

    color_cluster = cluster.ColorCluster(image)
    colors = color_cluster.get_colors()

    assert colors == expected_sorted_colors
