import gzip
import struct
import sys

if (sys.version_info > (3, 0)):
    from io import BytesIO as ByteBuffer
else:
    from StringIO import StringIO as ByteBuffer


class VersionError(Exception):
    pass

#
# VGM Specification: https://vgmrips.net/wiki/VGM_Specification
#
class Parser:
    # VGM file identifier
    vgm_magic_number = b'Vgm '

    # Supported VGM versions
    supported_ver_list = [
        0x00000100,
        0x00000101,
        0x00000110,
        0x00000150,
        0x00000151,
        0x00000160,
        0x00000161,
        0x00000170,
        0x00000171,
    ]

    # VGM metadata offsets
    metadata_offsets = {
        # Version 1.00
        0x00000100: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            # 1.00/1.01 specific - later ym2413_clock
            'ym2151_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I', 'condition': lambda val: val <= 5000000},
            # 1.00/1.01 specific - later ym2413_clock
            'ym2612_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I', 'condition': lambda val: val > 5000000 },
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': 0x0009,
            'sn76489_shift_register_width': 16,
        },
        # Version 1.01
        0x00000101: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            # 1.00/1.01 specific - later ym2413_clock
            'ym2151_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I', 'condition': lambda val: val <= 5000000},
            # 1.00/1.01 specific - later ym2413_clock
            'ym2612_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I', 'condition': lambda val: val > 5000000 },
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},               # 1.01
            'sn76489_feedback': 0x0009,
            'sn76489_shift_register_width': 16,
        },
        # Version 1.10
        0x00000110: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},   # 1.10
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'}, #1.10
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},       # 1.10
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},       # 1.10
        },
        # Version 1.50
        0x00000150: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a,'size': 1,'type_format': 'B'},
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},    # 1.50
        },
        # Version 1.51
        0x00000151: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'},
            'sn76489_flags': {'offset': 0x2b, 'size': 1, 'type_format': 'B'},           # 1.51 
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},
            'sega_pcm_clock': {'offset': 0x38, 'size': 4, 'type_format': '<I'},         # 1.51
            'sega_pcm_interface': {'offset': 0x3c, 'size': 4, 'type_format': '<I'},     # 1.51
            'rf5c68_clock': {'offset': 0x40, 'size': 4, 'type_format': '<I'},           # 1.51
            'ym2203_clock': {'offset': 0x44, 'size': 4, 'type_format': '<I'},           # 1.51
            'ym2608_clock': {'offset': 0x48, 'size': 4, 'type_format': '<I'},           # 1.51
            'ym2610_clock': {'offset': 0x4c, 'size': 4, 'type_format': '<I'},           # 1.51
            'ym3812_clock': {'offset': 0x50, 'size': 4, 'type_format': '<I'},           # 1.51
            'ym3526_clock': {'offset': 0x54, 'size': 4, 'type_format': '<I'},           # 1.51
            'y8950_clock': {'offset': 0x58, 'size': 4, 'type_format': '<I'},            # 1.51
            'ymf262_clock': {'offset': 0x5c, 'size': 4, 'type_format': '<I'},           # 1.51
            'ymf278b_clock': {'offset': 0x60, 'size': 4, 'type_format': '<I'},          # 1.51
            'ymf271_clock': {'offset': 0x64, 'size': 4, 'type_format': '<I'},           # 1.51
            'ymz280b_clock': {'offset': 0x68, 'size': 4, 'type_format': '<I'},          # 1.51
            'rf5c164_clock': {'offset': 0x6c, 'size': 4, 'type_format': '<I'},          # 1.51
            'pwm_clock': {'offset': 0x70, 'size': 4, 'type_format': '<I'},              # 1.51
            'ay8910_clock': {'offset': 0x74, 'size': 4, 'type_format': '<I'},           # 1.51
            'ay8910_type': {'offset': 0x78, 'size': 1, 'type_format': 'B'},             # 1.51
            'ay8910_flags': {'offset': 0x79, 'size': 1, 'type_format': 'B'},            # 1.51
            'ym2203_flags': {'offset': 0x7a, 'size': 1, 'type_format': 'B'},            # 1.51
            'ym2608_flags': {'offset': 0x7b, 'size': 1, 'type_format': 'B'},            # 1.51
            'loop_modifier': {'offset': 0x7f, 'size': 1, 'type_format': 'B'},           # 1.51
        },
        # Version 1.60
        0x00000160: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'},
            'sn76489_flags': {'offset': 0x2b, 'size': 1, 'type_format': 'B'},
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},
            'sega_pcm_clock': {'offset': 0x38, 'size': 4, 'type_format': '<I'},
            'sega_pcm_interface': {'offset': 0x3c, 'size': 4, 'type_format': '<I'},
            'rf5c68_clock': {'offset': 0x40, 'size': 4, 'type_format': '<I'},
            'ym2203_clock': {'offset': 0x44, 'size': 4, 'type_format': '<I'},
            'ym2608_clock': {'offset': 0x48, 'size': 4, 'type_format': '<I'},
            'ym2610_clock': {'offset': 0x4c, 'size': 4, 'type_format': '<I'},
            'ym3812_clock': {'offset': 0x50, 'size': 4, 'type_format': '<I'},
            'ym3526_clock': {'offset': 0x54, 'size': 4, 'type_format': '<I'},
            'y8950_clock': {'offset': 0x58, 'size': 4, 'type_format': '<I'},
            'ymf262_clock': {'offset': 0x5c, 'size': 4, 'type_format': '<I'},
            'ymf278b_clock': {'offset': 0x60, 'size': 4, 'type_format': '<I'},
            'ymf271_clock': {'offset': 0x64, 'size': 4, 'type_format': '<I'},
            'ymz280b_clock': {'offset': 0x68, 'size': 4, 'type_format': '<I'},
            'rf5c164_clock': {'offset': 0x6c, 'size': 4, 'type_format': '<I'},
            'pwm_clock': {'offset': 0x70, 'size': 4, 'type_format': '<I'},
            'ay8910_clock': {'offset': 0x74, 'size': 4, 'type_format': '<I'},
            'ay8910_type': {'offset': 0x78, 'size': 1, 'type_format': 'B'},
            'ay8910_flags': {'offset': 0x79, 'size': 1, 'type_format': 'B'},
            'ym2203_flags': {'offset': 0x7a, 'size': 1, 'type_format': 'B'},
            'ym2608_flags': {'offset': 0x7b, 'size': 1, 'type_format': 'B'},
            'volume_modifier': {'offset': 0x7c, 'size': 1, 'type_format': 'B'},         # 1.60
            'loop_base': {'offset': 0x7e, 'size': 1, 'type_format': 'B'},               # 1.60
            'loop_modifier': {'offset': 0x7f, 'size': 1, 'type_format': 'B'},
        },
        # Version 1.61
        0x00000161: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'},
            'sn76489_flags': {'offset': 0x2b, 'size': 1, 'type_format': 'B'},
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},
            'sega_pcm_clock': {'offset': 0x38, 'size': 4, 'type_format': '<I'},
            'sega_pcm_interface': {'offset': 0x3c, 'size': 4, 'type_format': '<I'},
            'rf5c68_clock': {'offset': 0x40, 'size': 4, 'type_format': '<I'},
            'ym2203_clock': {'offset': 0x44, 'size': 4, 'type_format': '<I'},
            'ym2608_clock': {'offset': 0x48, 'size': 4, 'type_format': '<I'},
            'ym2610_clock': {'offset': 0x4c, 'size': 4, 'type_format': '<I'},
            'ym3812_clock': {'offset': 0x50, 'size': 4, 'type_format': '<I'},
            'ym3526_clock': {'offset': 0x54, 'size': 4, 'type_format': '<I'},
            'y8950_clock': {'offset': 0x58, 'size': 4, 'type_format': '<I'},
            'ymf262_clock': {'offset': 0x5c, 'size': 4, 'type_format': '<I'},
            'ymf278b_clock': {'offset': 0x60, 'size': 4, 'type_format': '<I'},
            'ymf271_clock': {'offset': 0x64, 'size': 4, 'type_format': '<I'},
            'ymz280b_clock': {'offset': 0x68, 'size': 4, 'type_format': '<I'},
            'rf5c164_clock': {'offset': 0x6c, 'size': 4, 'type_format': '<I'},
            'pwm_clock': {'offset': 0x70, 'size': 4, 'type_format': '<I'},
            'ay8910_clock': {'offset': 0x74, 'size': 4, 'type_format': '<I'},
            'ay8910_type': {'offset': 0x78, 'size': 1, 'type_format': 'B'},
            'ay8910_flags': {'offset': 0x79, 'size': 1, 'type_format': 'B'},
            'ym2203_flags': {'offset': 0x7a, 'size': 1, 'type_format': 'B'},
            'ym2608_flags': {'offset': 0x7b, 'size': 1, 'type_format': 'B'},
            'volume_modifier': {'offset': 0x7c, 'size': 1, 'type_format': 'B'},
            'loop_base': {'offset': 0x7e, 'size': 1, 'type_format': 'B'},
            'loop_modifier': {'offset': 0x7f, 'size': 1, 'type_format': 'B'},
            'gb_dmg_clock': {'offset': 0x80, 'size': 4, 'type_format': '<I'},           # 1.61
            'nes_apu_clock': {'offset': 0x84, 'size': 4, 'type_format': '<I'},          # 1.61
            'multi_pcm_clock': {'offset': 0x88, 'size': 4, 'type_format': '<I'},        # 1.61
            'upd7759_clock': {'offset': 0x8c, 'size': 4, 'type_format': '<I'},          # 1.61
            'okim6258_clock': {'offset': 0x90, 'size': 4, 'type_format': '<I'},         # 1.61
            'okim6258_flags': {'offset': 0x94, 'size': 1, 'type_format': 'B'},          # 1.61
            'k054539_flags': {'offset': 0x95, 'size': 1, 'type_format': 'B'},           # 1.61
            'c140_type': {'offset': 0x96, 'size': 1, 'type_format': 'B'},               # 1.61
            'okim6295 clock': {'offset': 0x98, 'size': 4, 'type_format': '<I'},         # 1.61
            'k051649_k052539_clock': {'offset': 0x9C, 'size': 4, 'type_format': '<I'},  # 1.61
            'k054539_clock': {'offset': 0xA0, 'size': 4, 'type_format': '<I'},          # 1.61
            'huc6280_clock': {'offset': 0xA4, 'size': 4, 'type_format': '<I'},          # 1.61
            'c140_clocl': {'offset': 0xA8, 'size': 4, 'type_format': '<I'},             # 1.61
            'k053260_clock': {'offset': 0xAC, 'size': 4, 'type_format': '<I'},          # 1.61
            'pokey_clock': {'offset': 0xB0, 'size': 4, 'type_format': '<I'},            # 1.61
            'qsound_clock': {'offset': 0xB4, 'size': 4, 'type_format': '<I'},           # 1.61
        },
        # Version 1.70
        0x00000170: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'},
            'sn76489_flags': {'offset': 0x2b, 'size': 1, 'type_format': 'B'},
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},
            'sega_pcm_clock': {'offset': 0x38, 'size': 4, 'type_format': '<I'},
            'sega_pcm_interface': {'offset': 0x3c, 'size': 4, 'type_format': '<I'},
            'rf5c68_clock': {'offset': 0x40, 'size': 4, 'type_format': '<I'},
            'ym2203_clock': {'offset': 0x44, 'size': 4, 'type_format': '<I'},
            'ym2608_clock': {'offset': 0x48, 'size': 4, 'type_format': '<I'},
            'ym2610_clock': {'offset': 0x4c, 'size': 4, 'type_format': '<I'},
            'ym3812_clock': {'offset': 0x50, 'size': 4, 'type_format': '<I'},
            'ym3526_clock': {'offset': 0x54, 'size': 4, 'type_format': '<I'},
            'y8950_clock': {'offset': 0x58, 'size': 4, 'type_format': '<I'},
            'ymf262_clock': {'offset': 0x5c, 'size': 4, 'type_format': '<I'},
            'ymf278b_clock': {'offset': 0x60, 'size': 4, 'type_format': '<I'},
            'ymf271_clock': {'offset': 0x64, 'size': 4, 'type_format': '<I'},
            'ymz280b_clock': {'offset': 0x68, 'size': 4, 'type_format': '<I'},
            'rf5c164_clock': {'offset': 0x6c, 'size': 4, 'type_format': '<I'},
            'pwm_clock': {'offset': 0x70, 'size': 4, 'type_format': '<I'},
            'ay8910_clock': {'offset': 0x74, 'size': 4, 'type_format': '<I'},
            'ay8910_type': {'offset': 0x78, 'size': 1, 'type_format': 'B'},
            'ay8910_flags': {'offset': 0x79, 'size': 1, 'type_format': 'B'},
            'ym2203_flags': {'offset': 0x7a, 'size': 1, 'type_format': 'B'},
            'ym2608_flags': {'offset': 0x7b, 'size': 1, 'type_format': 'B'},
            'volume_modifier': {'offset': 0x7c, 'size': 1, 'type_format': 'B'},
            'loop_base': {'offset': 0x7e, 'size': 1, 'type_format': 'B'},
            'loop_modifier': {'offset': 0x7f, 'size': 1, 'type_format': 'B'},
            'gb_dmg_clock': {'offset': 0x80, 'size': 4, 'type_format': '<I'},
            'nes_apu_clock': {'offset': 0x84, 'size': 4, 'type_format': '<I'},
            'multi_pcm_clock': {'offset': 0x88, 'size': 4, 'type_format': '<I'},
            'upd7759_clock': {'offset': 0x8c, 'size': 4, 'type_format': '<I'},
            'okim6258_clock': {'offset': 0x90, 'size': 4, 'type_format': '<I'},
            'okim6258_flags': {'offset': 0x94, 'size': 1, 'type_format': 'B'},
            'k054539_flags': {'offset': 0x95, 'size': 1, 'type_format': 'B'},
            'c140_type': {'offset': 0x96, 'size': 1, 'type_format': 'B'},
            'okim6295 clock': {'offset': 0x98, 'size': 4, 'type_format': '<I'},
            'k051649_k052539_clock': {'offset': 0x9C, 'size': 4, 'type_format': '<I'},
            'k054539_clock': {'offset': 0xA0, 'size': 4, 'type_format': '<I'},
            'huc6280_clock': {'offset': 0xA4, 'size': 4, 'type_format': '<I'},
            'c140_clocl': {'offset': 0xA8, 'size': 4, 'type_format': '<I'},
            'k053260_clock': {'offset': 0xAC, 'size': 4, 'type_format': '<I'},
            'pokey_clock': {'offset': 0xB0, 'size': 4, 'type_format': '<I'},
            'qsound_clock': {'offset': 0xB4, 'size': 4, 'type_format': '<I'},
            'extra_header_offset': {'offset': 0xBc, 'size': 4, 'type_format': '<I'},    # 1.70
        },
        # Version 1.71
        0x00000171: {
            'vgm_ident': {'offset': 0x00, 'size': 4, 'type_format': None},
            'eof_offset': {'offset': 0x04, 'size': 4, 'type_format': '<I'},
            'version': {'offset': 0x08, 'size': 4, 'type_format': '<I'},
            'sn76489_clock': {'offset': 0x0c, 'size': 4, 'type_format': '<I'},
            'ym2413_clock': {'offset': 0x10, 'size': 4, 'type_format': '<I'},
            'gd3_offset': {'offset': 0x14, 'size': 4, 'type_format': '<I'},
            'total_samples': {'offset': 0x18, 'size': 4, 'type_format': '<I'},
            'loop_offset': {'offset': 0x1c, 'size': 4, 'type_format': '<I'},
            'loop_samples': {'offset': 0x20, 'size': 4, 'type_format': '<I'},
            'rate': {'offset': 0x24, 'size': 4, 'type_format': '<I'},
            'sn76489_feedback': {'offset': 0x28, 'size': 2, 'type_format': '<H'},
            'sn76489_shift_register_width': {'offset': 0x2a, 'size': 1, 'type_format': 'B'},
            'sn76489_flags': {'offset': 0x2b, 'size': 1, 'type_format': 'B'},
            'ym2612_clock': {'offset': 0x2c, 'size': 4, 'type_format': '<I'},
            'ym2151_clock': {'offset': 0x30, 'size': 4, 'type_format': '<I'},
            'vgm_data_offset': {'offset': 0x34, 'size': 4, 'type_format': '<I'},
            'sega_pcm_clock': {'offset': 0x38, 'size': 4, 'type_format': '<I'},
            'sega_pcm_interface': {'offset': 0x3c, 'size': 4, 'type_format': '<I'},
            'rf5c68_clock': {'offset': 0x40, 'size': 4, 'type_format': '<I'},
            'ym2203_clock': {'offset': 0x44, 'size': 4, 'type_format': '<I'},
            'ym2608_clock': {'offset': 0x48, 'size': 4, 'type_format': '<I'},
            'ym2610_clock': {'offset': 0x4c, 'size': 4, 'type_format': '<I'},
            'ym3812_clock': {'offset': 0x50, 'size': 4, 'type_format': '<I'},
            'ym3526_clock': {'offset': 0x54, 'size': 4, 'type_format': '<I'},
            'y8950_clock': {'offset': 0x58, 'size': 4, 'type_format': '<I'},
            'ymf262_clock': {'offset': 0x5c, 'size': 4, 'type_format': '<I'},
            'ymf278b_clock': {'offset': 0x60, 'size': 4, 'type_format': '<I'},
            'ymf271_clock': {'offset': 0x64, 'size': 4, 'type_format': '<I'},
            'ymz280b_clock': {'offset': 0x68, 'size': 4, 'type_format': '<I'},
            'rf5c164_clock': {'offset': 0x6c, 'size': 4, 'type_format': '<I'},
            'pwm_clock': {'offset': 0x70, 'size': 4, 'type_format': '<I'},
            'ay8910_clock': {'offset': 0x74, 'size': 4, 'type_format': '<I'},
            'ay8910_type': {'offset': 0x78, 'size': 1, 'type_format': 'B'},
            'ay8910_flags': {'offset': 0x79, 'size': 1, 'type_format': 'B'},
            'ym2203_flags': {'offset': 0x7a, 'size': 1, 'type_format': 'B'},
            'ym2608_flags': {'offset': 0x7b, 'size': 1, 'type_format': 'B'},
            'volume_modifier': {'offset': 0x7c, 'size': 1, 'type_format': 'B'},
            'loop_base': {'offset': 0x7e, 'size': 1, 'type_format': 'B'},
            'loop_modifier': {'offset': 0x7f, 'size': 1, 'type_format': 'B'},
            'gb_dmg_clock': {'offset': 0x80, 'size': 4, 'type_format': '<I'},
            'nes_apu_clock': {'offset': 0x84, 'size': 4, 'type_format': '<I'},
            'multi_pcm_clock': {'offset': 0x88, 'size': 4, 'type_format': '<I'},
            'upd7759_clock': {'offset': 0x8c, 'size': 4, 'type_format': '<I'},
            'okim6258_clock': {'offset': 0x90, 'size': 4, 'type_format': '<I'},
            'okim6258_flags': {'offset': 0x94, 'size': 1, 'type_format': 'B'},
            'k054539_flags': {'offset': 0x95, 'size': 1, 'type_format': 'B'},
            'c140_type': {'offset': 0x96, 'size': 1, 'type_format': 'B'},
            'okim6295 clock': {'offset': 0x98, 'size': 4, 'type_format': '<I'},
            'k051649_k052539_clock': {'offset': 0x9C, 'size': 4, 'type_format': '<I'},
            'k054539_clock': {'offset': 0xA0, 'size': 4, 'type_format': '<I'},
            'huc6280_clock': {'offset': 0xA4, 'size': 4, 'type_format': '<I'},
            'c140_clocl': {'offset': 0xA8, 'size': 4, 'type_format': '<I'},
            'k053260_clock': {'offset': 0xAC, 'size': 4, 'type_format': '<I'},
            'pokey_clock': {'offset': 0xB0, 'size': 4, 'type_format': '<I'},
            'qsound_clock': {'offset': 0xB4, 'size': 4, 'type_format': '<I'},
            'SCSP_clock': {'offset': 0xB8, 'size': 4, 'type_format': '<I'},             # 1.71
            'extra_header_offset': {'offset': 0xBc, 'size': 4, 'type_format': '<I'},
            'wonder_swan_clock': {'offset': 0xc0, 'size': 4, 'type_format': '<I'},      # 1.71
            'vsu_clock': {'offset': 0xc4, 'size': 4, 'type_format': '<I'},              # 1.71
            'saa1099_clock': {'offset': 0xc8, 'size': 4, 'type_format': '<I'},          # 1.71
            'es5503_clock': {'offset': 0xcc, 'size': 4, 'type_format': '<I'},           # 1.71
            'es5505_es5506_clock': {'offset': 0xd0, 'size': 4, 'type_format': '<I'},    # 1.71
            'es5503_output_channels': {'offset': 0xd4, 'size': 1, 'type_format': 'B'},  # 1.71
            'es5505_es5506_output_channels': {'offset': 0xd5, 'size': 1, 'type_format': 'B'}, # 1.71
            'c352_clock_divider': {'offset': 0xd6, 'size': 1, 'type_format': 'B'},      # 1.71
            'x1_010_clock': {'offset': 0xd8, 'size': 4, 'type_format': '<I'},           # 1.71
            'c352_clock': {'offset': 0xdC, 'size': 4, 'type_format': '<I'},             # 1.71
            'ga20_clock': {'offset': 0xe0, 'size': 4, 'type_format': '<I'},             # 1.71
        },
    }

    def __init__(self, vgm_data):
        # Store the VGM data and validate it
        self.data = ByteBuffer(vgm_data)
        self.validate_vgm_data()

        # Set up the variables that will be populated
        self.vgm_data_offset = 0x40
        self.command_list = []
        self.data_block = None
        self.data_block_type = None
        self.gd3_data = {}
        self.metadata = {}

        # Parse the VGM metadata and validate the VGM version
        self.parse_metadata()
        self.validate_vgm_version()

        # Parse GD3 data and the VGM commands
        self.parse_gd3()
        self.parse_commands()

    def parse_commands(self):
        # Save the current position of the VGM data
        original_pos = self.data.tell()

        # Seek to the start of the VGM data
        self.data.seek(
            self.vgm_data_offset
            #self.metadata['vgm_data_offset'] +
            #self.metadata_offsets[self.metadata['version']]['vgm_data_offset']['offset']
        )

        while True:
            # Read a byte, this will be a VGM command, we will then make
            # decisions based on the given command
            command = self.data.read(1)

            # Break if we are at the end of the file
            if command == '':
                break

            # @TODO: automatize reading of command operands based on reserved ranges in specification (that should take care of dual chip support as well)
            # @TODO: add optional flag to unpack operands
            # @TODO: implement extra header (v1.70) support

            # 0x31 dd - AY8910 stereo mask, dd is a bit mask of i y r3 l3 r2 l2 r1 l1 (bit 7 ... 0)
            #           i   chip instance (0 or 1)
            #           y   set stereo mask for YM2203 SSG (1) or AY8910 (0)
            #           l1/l2/l3    enable channel 1/2/3 on left speaker
            #           r1/r2/r3    enable channel 1/2/3 on right speaker
            # 0x4f dd - Game Gear PSG stereo, write dd to port 0x06
            # 0x50 dd - PSG (SN76489/SN76496) write value dd
            if command in [b'\x31', b'\x4f', b'\x50']:
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(1),
                })

            # 0x51 aa dd - YM2413, write value dd to register aa
            # 0x52 aa dd - YM2612 port 0, write value dd to register aa
            # 0x53 aa dd - YM2612 port 1, write value dd to register aa
            # 0x54 aa dd - YM2151, write value dd to register aa
            # 0x55 aa dd - YM2203, write value dd to register aa
            # 0x56 aa dd - YM2608 port 0, write value dd to register aa
            # 0x57 aa dd - YM2608 port 1, write value dd to register aa
            # 0x58 aa dd - YM2610 port 0, write value dd to register aa
            # 0x59 aa dd - YM2610 port 1, write value dd to register aa
            # 0x5A aa dd - YM3812, write value dd to register aa
            # 0x5B aa dd - YM3526, write value dd to register aa
            # 0x5C aa dd - Y8950, write value dd to register aa
            # 0x5D aa dd - YMZ280B, write value dd to register aa
            # 0x5E aa dd - YMF262 port 0, write value dd to register aa
            # 0x5F aa dd - YMF262 port 1, write value dd to register aa
            # 0xA0 aa dd - AY8910, write value dd to register aa
            # 0xB0 aa dd - RF5C68, write value dd to register aa
            # 0xB1 aa dd - RF5C164, write value dd to register aa
            # 0xB2 ad dd - PWM, write value ddd to register a (d is MSB, dd is LSB)
            # 0xB3 aa dd - GameBoy DMG, write value dd to register aa
            # 0xB4 aa dd - NES APU, write value dd to register aa
            # 0xB5 aa dd - MultiPCM, write value dd to register aa
            # 0xB6 aa dd - uPD7759, write value dd to register aa
            # 0xB7 aa dd - OKIM6258, write value dd to register aa
            # 0xB8 aa dd - OKIM6295, write value dd to register aa
            # 0xB9 aa dd - HuC6280, write value dd to register aa
            # 0xBA aa dd - K053260, write value dd to register aa
            # 0xBB aa dd - Pokey, write value dd to register aa
            # 0xBC aa dd - WonderSwan, write value dd to register aa
            # 0xBD aa dd - SAA1099, write value dd to register aa
            # 0xBE aa dd - ES5506, write value dd to register aa
            # 0xBF aa dd - GA20, write value dd to register aa
            elif command in [b'\x51', b'\x52', b'\x53', b'\x54',
                             b'\x55', b'\x56', b'\x57', b'\x58',
                             b'\x59', b'\x5a', b'\x5b', b'\x5c',
                             b'\x5d', b'\x5e', b'\x5f', b'\xa0',
                             b'\xb0', b'\xb1', b'\xb2', b'\xb3',
                             b'\xb4', b'\xb5', b'\xb6', b'\xb7',
                             b'\xb8', b'\xb9', b'\xba', b'\xbb',
                             b'\xbc', b'\xbd', b'\xbe', b'\xbf',
                            ]:
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(2),
                })

            # 0x61 nn nn - Wait n samples, n can range from 0 to 65535
            elif command == b'\x61':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(2), # struct.unpack('<H', self.data.read(2))[0],
                })

            # 0x62 - Wait 735 samples (60th of a second)
            # 0x63 - Wait 882 samples (50th of a second)
            # 0x66 - End of sound data
            elif command in [b'\x62', b'\x63', b'\x66']:
                self.command_list.append({'command': command, 'data': None})

                # Stop processing commands if we are at the end of the music
                # data
                if command == b'\x66':
                    break

            # 0x67 0x66 tt ss ss ss ss - Data block
            elif command == b'\x67':
                # Skip the compatibility byte (0x66)
                self.data.seek(1, 1)

                self.data_block_type = self.data.read(1)

                # Read the size of the data block
                data_block_size = struct.unpack('<I', self.data.read(4))[0]

                # Store the data block for later use
                self.data_block = ByteBuffer(self.data.read(data_block_size))

            # 0x68 0x66 cc oo oo oo dd dd dd ss ss ss - PCM RAM write
            elif command == b'\x68':
                # Skip the compatibility byte (0x66)
                self.data.seek(1, 1)
                # Read the rest of data cc oo oo oo dd dd dd ss ss ss
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(10),
                })

            # 0x7n - Wait n+1 samples, n can range from 0 to 15
            # 0x8n - YM2612 port 0 address 2A write from the data bank, then
            #        wait n samples; n can range from 0 to 15
            elif b'\x70' <= command <= b'\x8f':
                self.command_list.append({'command': command, 'data': None})

            # 0x90 ss tt pp cc - DAC Setup Stream Control
            elif command == b'\x90':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(4),
                })
            # 0x91 ss dd ll bb - DAC Set Stream Data
            elif command == b'\x91':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(4),
                })
            # 0x92 ss ff ff ff ff - DAC Set Stream Frequency
            elif command == b'\x92':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(5),
                })
            # 0x93 ss aa aa aa aa mm ll ll ll ll - DAC Start Stream
            elif command == b'\x93':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(10),
                })
            # 0x94 ss - DAC Stop Stream
            elif command == b'\x94':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(1),
                })
            # 0x95 ss bb bb ff - DAC Start Stream (fast call)
            elif command == b'\x95':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(4),
                })

            # 0xC0 bbaa dd - Sega PCM, write value dd to memory offset aabb
            # 0xC1 bbaa dd - RF5C68, write value dd to memory offset aabb
            # 0xC2 bbaa dd - RF5C164, write value dd to memory offset aabb
            # 0xC3 cc bbaa - MultiPCM, write set bank offset aabb to channel cc
            # 0xC4 mmll rr - QSound, write value mmll to register rr (mm - data MSB, ll - data LSB)
            # 0xC5 mmll dd - SCSP, write value dd to memory offset mmll (mm - offset MSB, ll - offset LSB)
            # 0xC6 mmll dd - WonderSwan, write value dd to memory offset mmll (mm - offset MSB, ll - offset LSB)
            # 0xC7 mmll dd - VSU, write value dd to memory offset mmll (mm - offset MSB, ll - offset LSB)
            # 0xC8 mmll dd - X1-010, write value dd to memory offset mmll (mm - offset MSB, ll - offset LSB)
            # 0xD0 pp aa dd - YMF278B, port pp, write value dd to register aa
            # 0xD1 pp aa dd - YMF271, port pp, write value dd to register aa
            # 0xD2 pp aa dd - SCC1, port pp, write value dd to register aa
            # 0xD3 pp aa dd - K054539, write value dd to register ppaa
            # 0xD4 pp aa dd - C140, write value dd to register ppaa
            # 0xD5 pp aa dd - ES5503, write value dd to register ppaa
            # 0xD6 pp aa dd - ES5506, write value aadd to register pp
            elif command in [b'\xc0', b'\xc1', b'\xc2', b'\xc3',
                             b'\xc4', b'\xc5', b'\xc6', b'\xc7',
                             b'\xc8',
                             b'\xd0', b'\xd1', b'\xd2', b'\xd3',
                             b'\xd4', b'\xd5', b'\xd6',
                            ]:
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(3),
                })

            # 0xE0 dddddddd - Seek to offset dddddddd (Intel byte order) in PCM
            #                 data bank
            elif command == b'\xe0':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(4),
                })

            # 0xE1 mmll aadd - C352, write value aadd to register mmll
            elif command == b'\xe1':
                self.command_list.append({
                    'command': command,
                    'data': self.data.read(4),
                })

        # Seek back to the original position in the VGM data
        self.data.seek(original_pos)

    def parse_gd3(self):
        # Save the current position of the VGM data
        original_pos = self.data.tell()

        # Seek to the start of the GD3 data
        self.data.seek(
            self.metadata['gd3_offset'] +
            self.metadata_offsets[self.metadata['version']]['gd3_offset']['offset']
        )

        # Skip 8 bytes ('Gd3 ' string and 4 byte version identifier)
        self.data.seek(8, 1)

        # Get the length of the GD3 data, then read it
        gd3_length = struct.unpack('<I', self.data.read(4))[0]
        gd3_data = ByteBuffer(self.data.read(gd3_length))

        # Parse the GD3 data
        gd3_fields = []
        current_field = b''
        while True:
            # Read two bytes. All characters (English and Japanese) in the GD3
            # data use two byte encoding
            char = gd3_data.read(2)

            # Break if we are at the end of the GD3 data
            if char == b'':
                break

            # Check if we are at the end of a field, if not then continue to
            # append to "current_field"
            if char == b'\x00\x00':
                gd3_fields.append(current_field)
                current_field = b''
            else:
                current_field += char

        # Once all the fields have been parsed, create a dict with the data
        self.gd3_data = {
            'title_eng': gd3_fields[0],
            'title_jap': gd3_fields[1],
            'game_eng': gd3_fields[2],
            'game_jap': gd3_fields[3],
            'console_eng': gd3_fields[4],
            'console_jap': gd3_fields[5],
            'artist_eng': gd3_fields[6],
            'artist_jap': gd3_fields[7],
            'date': gd3_fields[8],
            'vgm_creator': gd3_fields[9],
            'notes': gd3_fields[10],
        }

        # Seek back to the original position in the VGM data
        self.data.seek(original_pos)

    def parse_metadata(self):
        # Save the current position of the VGM data
        original_pos = self.data.tell()

        # Create the list to store the VGM metadata
        self.metadata = {}

        # Iterate over the offsets and parse the metadata
        highest_supported_version = self.supported_ver_list[-1]
        for version, offsets in self.metadata_offsets.items():
            # Skip parsing metadata from VGM versions later than the version of the file
            if version <= self.metadata.get('version', highest_supported_version):

                # Calculate offset of VGM data
                if 'vgm_data_offset' in self.metadata:
                    self.vgm_data_offset =  self.metadata['vgm_data_offset'] + \
                                            self.metadata_offsets[version]['vgm_data_offset']['offset']
                header_end = self.vgm_data_offset # Header ends where VGM data starts

                for value, offset_data in offsets.items():

                    if not isinstance(offset_data, dict):
                        self.metadata[value] = offset_data
                        continue

                    # Skip parsing metadata attributes that are located outside the header,
                    # set them to 0 instead.
                    #
                    # See specification: "All header sizes are valid for all versions from 1.50 on,
                    # as long as header has at least 64 bytes. If the VGM data starts at an offset
                    # that is lower than 0x100, all overlapping header bytes have to be handled as
                    # they were zero."
                    if offset_data['offset'] >= header_end:
                        self.metadata[value] = 0
                        continue

                    # Seek to the data location and read the data
                    self.data.seek(offset_data['offset'])
                    data = self.data.read(offset_data['size'])

                    # Unpack the data if required
                    if offset_data['type_format'] is not None:
                        data = struct.unpack(
                            offset_data['type_format'],
                            data,
                        )[0]

                    # Check if special condition applies
                    # mostly used for a backwards compatibility handling in pre 1.10 formats
                    if 'condition' in offset_data and not offset_data['condition'](data):
                        continue

                    self.metadata[value] = data

        # Seek back to the original position in the VGM data
        self.data.seek(original_pos)

    def validate_vgm_data(self):
        # Save the current position of the VGM data
        original_pos = self.data.tell()

        # Seek to the start of the file
        self.data.seek(0)

        # Perform basic validation on the given file by checking for the VGM
        # magic number ('Vgm ')
        if self.data.read(4) != self.vgm_magic_number:
            # Could not find the magic number. The file could be gzipped (e.g.
            # a vgz file). Try un-gzipping the file and trying again.
            self.data.seek(0)
            self.data = gzip.GzipFile(fileobj=self.data, mode='rb')

            try:
                if self.data.read(4) != self.vgm_magic_number:
                    raise ValueError('Data does not appear to be a valid VGM file')
            except IOError:
                # IOError will be raised if the file is not a valid gzip file
                raise ValueError('Data does not appear to be a valid VGM file')

        # Seek back to the original position in the VGM data
        self.data.seek(original_pos)

    def validate_vgm_version(self):
        def bcd_version_to_str(bcd):
            version = ""
            while bcd > 0:
                version = str(bcd & 15) + version
                bcd >>= 4
            return version

        if self.metadata['version'] not in self.supported_ver_list:
            version = self.metadata['version']
            raise VersionError(f'VGM version {bcd_version_to_str(version>>8)}.{bcd_version_to_str(version&255)} is not supported')
