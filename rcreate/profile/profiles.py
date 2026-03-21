"""Preset profile configurations — equivalent to RcPlatformProfiles.java."""

from .profile import Profile

# Profile bitmask constants (from RcProfiles.java)
PROFILE_BASELINE = 0x0
PROFILE_EXPERIMENTAL = 0x1
PROFILE_DEPRECATED = 0x2
PROFILE_OEM = 0x4
PROFILE_LOW_POWER = 0x8
PROFILE_WIDGETS = 0x100
PROFILE_ANDROIDX = 0x200
PROFILE_ANDROID_NATIVE = 0x400
PROFILE_WEAR_WIDGETS = 0x800

# Document API level (from CoreDocument.java)
DOCUMENT_API_LEVEL = 8

# Preset profiles
WIDGETS_V6 = Profile(api_level=6, operations_profiles=0)
ANDROIDX = Profile(api_level=DOCUMENT_API_LEVEL, operations_profiles=PROFILE_ANDROIDX)
WEAR_WIDGETS = Profile(api_level=DOCUMENT_API_LEVEL, operations_profiles=PROFILE_WEAR_WIDGETS)
