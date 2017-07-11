# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest

from .utils import load_psd, decode_psd, full_name
from psd_tools import PSDImage, Group


FILE_NAMES = (
    'layer_mask_data.psd',
    'masks.psd',
    'masks2.psd',
    'masks.psb',
    'masks2.psb'
)

MASK_DATA_BY_LAYERS = (
# Each block correspond to file in FILE_NAMES at the same index:
#   (
#       (<layer id>, <some of mask_data>),
#       ...
#   )
#
#   <some of mask_data>     = (background_color, <some of flags>, parameters,
#                              <some of real_flags>, real_background_color)
#                             OR
#                             None
#
#   <some of flags>         = (mask_disabled, user_mask_from_render, parameters_applied)
#   parameters              = parameters            OR None
#   <some of real_flags>    = <some of flags>       OR None
#   real_background_color   = real_background_color OR None
#
    (
        (0, None                                                                               ),
        (1, (  0, (False, True , True ), (None, None,  204, None), None                 , None)),
        (2, (  0, (False, False, True ), ( 230,    6, None, None), None                 , None)),
        (3, (255, (False, False, False), None                    , None                 , None)),
        (4, (  0, (False, True , True ), ( 191,    3, None,    2), (False, False, False),  255))
    ),

    (
        (20, (0, (False, True, False), None, (True, False, False), 255)),
    ),

    (
        (1, (0, (False, True, False), None, (False, False, False), 255)),
    ),

    (
        (20, (0, (False, True, False), None, (True, False, False), 255)),
    ),

    (
        (1, (0, (False, True, False), None, (False, False, False), 255)),
    )
)


@pytest.mark.parametrize('filename', FILE_NAMES)
def test_file_with_masks_is_parsed(filename):
    psd = decode_psd(filename)
    for layer_channels in psd.layer_and_mask_data.layers.channel_image_data:
        assert len(layer_channels) >= 3


@pytest.mark.parametrize(('filename', 'mask_data_by_layers'), zip(FILE_NAMES, MASK_DATA_BY_LAYERS))
def test_layer_mask_data(filename, mask_data_by_layers):
    psd = load_psd(filename)
    layers = psd.layer_and_mask_data.layers.layer_records

    for layer_id, ethalon_mask_data in mask_data_by_layers:
        mask_data = layers[layer_id].mask_data

        has_mask_data = (ethalon_mask_data is not None)
        assert (mask_data is not None) == has_mask_data

        if has_mask_data:
            assert mask_data.background_color == ethalon_mask_data[0]

            ethalon_flags = ethalon_mask_data[1]
            assert mask_data.flags.mask_disabled         == ethalon_flags[0]
            assert mask_data.flags.user_mask_from_render == ethalon_flags[1]
            assert mask_data.flags.parameters_applied    == ethalon_flags[2]

            ethalon_parameters = ethalon_mask_data[2]
            if ethalon_parameters is not None:
                assert mask_data.parameters.user_mask_density == ethalon_parameters[0]
                assert mask_data.parameters.user_mask_feather == ethalon_parameters[1]
                assert mask_data.parameters.vector_mask_density == ethalon_parameters[2]
                assert mask_data.parameters.vector_mask_feather == ethalon_parameters[3]

            ethalon_real_flags = ethalon_mask_data[3]
            has_real_flags = (ethalon_real_flags is not None)
            assert (mask_data.real_flags is not None) == has_real_flags

            if has_real_flags:
                assert mask_data.real_flags.mask_disabled         == ethalon_real_flags[0]
                assert mask_data.real_flags.user_mask_from_render == ethalon_real_flags[1]
                assert mask_data.real_flags.parameters_applied    == ethalon_real_flags[2]

            assert mask_data.real_background_color == ethalon_mask_data[4]


@pytest.mark.parametrize('filename', FILE_NAMES)
def test_mask_data_as_pil(filename):

    def traverse_tree(layers):
        if isinstance(layers, PSDImage):
            layers = layers.layers
        for l in layers:
            mask_data = l.mask_data
            if mask_data:
                if mask_data.is_valid:
                    assert mask_data.as_PIL() is not None
                else:
                    bbox = mask_data.bbox
                    assert bbox.width == 0 or bbox.height == 0
            if isinstance(l, Group):
                traverse_tree(l.layers)

    psd = PSDImage.load(full_name(filename))
    traverse_tree(psd)
